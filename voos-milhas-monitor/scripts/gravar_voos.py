#!/usr/bin/env python3
"""Ingere cotações: grava observações, calcula baseline e emite alertas.

Fluxo:
1. Toda cotação válida vira observação append-only (data/observacoes.csv).
2. Baseline = mediana da rota nos últimos N dias (com bootstrap da média da página).
3. Alerta entra em voos_ativos.csv quando o preço está X% abaixo da referência.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import baseline as baseline_mod
from links import link_ida_volta

RAIZ = Path(__file__).resolve().parents[1]
CONFIG_PATH = RAIZ / "config-rotina.json"

COLUNAS = [
    "id",
    "timestamp",
    "origem",
    "destino",
    "cidade_origem",
    "cidade_destino",
    "companhia",
    "data_ida",
    "data_volta",
    "preco_por_pessoa",
    "preco_total",
    "preco_referencia",
    "fonte_referencia",
    "desconto_percentual",
    "economia_estimada",
    "tipo_voo_ida",
    "tipo_voo_volta",
    "total_conexoes",
    "conexoes_ida",
    "conexoes_volta",
    "duracao_total_ida",
    "duracao_total_volta",
    "mudanca_aeroporto",
    "aeroportos_conexao",
    "classificacao_logistica",
    "score",
    "bagagem_incluida",
    "link",
]

COLUNAS_ALERTAS = [
    "id",
    "emitido_em",
    "origem",
    "destino",
    "data_ida",
    "data_volta",
    "preco",
    "baseline",
    "fonte_referencia",
    "desconto_percentual",
    "link",
]


def carregar_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def ler_csv(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def escrever_csv(caminho: Path, linhas: list[dict], colunas: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, lineterminator="\n")
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({coluna: linha.get(coluna, "") for coluna in colunas})


def classificar(conexoes: int) -> tuple[str, int]:
    if conexoes <= 0:
        return "Direto", 90
    if conexoes == 1:
        return "1 conexão", 80
    return "2+ conexões", 70


def estadia_dias(ida, volta) -> int | None:
    try:
        ida_dt = datetime.strptime(str(ida)[:10], "%Y-%m-%d")
        volta_dt = datetime.strptime(str(volta)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    return (volta_dt - ida_dt).days


def limites_estadia(config: dict) -> tuple[int, int]:
    janela = config.get("janela") or {}
    return int(janela.get("estadia_dias_min", 7)), int(janela.get("estadia_dias_max", 15))


def desconto_minimo(config: dict) -> float:
    alerta = config.get("alerta") or {}
    if "desconto_minimo_percentual" in alerta:
        return float(alerta["desconto_minimo_percentual"])
    return float(config.get("desconto_minimo_percentual", 25))


def percentual_abaixo(preco, media) -> float | None:
    try:
        preco_f = float(preco)
        media_f = float(media)
    except (TypeError, ValueError):
        return None
    if preco_f <= 0 or media_f <= 0:
        return None
    return (media_f - preco_f) / media_f * 100


def media_vista(item: dict):
    for chave in ("preco_medio", "media", "preco_referencia"):
        valor = item.get(chave)
        if valor not in (None, ""):
            return valor
    return None


def numero(valor, padrao: int | None = None) -> int | None:
    if valor is None or valor == "":
        return padrao
    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


def texto_mudanca(valor) -> str:
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    if valor is None or str(valor).strip() == "":
        return "não informado"
    texto = str(valor).strip().lower()
    if texto in {"sim", "true", "1", "yes"}:
        return "Sim"
    if texto in {"nao", "não", "false", "0", "no"}:
        return "Não"
    return "não informado"


def id_alerta(origem: str, destino: str, ida: str, volta: str) -> str:
    return f"ALERTA_{origem}_{destino}_{str(ida)[:10]}_{str(volta)[:10]}"


def linha_de_cotacao(
    item: dict,
    cidades: dict,
    agora: str,
    origens_brasil: set[str],
    estadia_min: int,
    estadia_max: int,
    desconto_min: float,
    referencia: dict,
) -> dict | None:
    origem = str(item.get("origem") or "").strip().upper()
    destino = str(item.get("destino") or "").strip().upper()
    preco = item.get("preco")
    if origem not in origens_brasil:
        return None
    if not origem or not destino or preco in (None, ""):
        return None
    try:
        valor = float(preco)
    except (TypeError, ValueError):
        return None
    if valor <= 0:
        return None
    dias = estadia_dias(item.get("data_ida"), item.get("data_volta"))
    if dias is None or dias < estadia_min or dias > estadia_max:
        return None
    ref = referencia.get("valor")
    desconto = percentual_abaixo(valor, ref)
    if desconto is None or desconto < desconto_min:
        return None
    media_f = float(ref)
    conexoes_ida = numero(item.get("conexoes_ida"))
    if conexoes_ida is None:
        conexoes_ida = numero(item.get("conexoes"), 0)
    conexoes_volta = numero(item.get("conexoes_volta"))
    if conexoes_volta is None:
        conexoes_volta = conexoes_ida
    tipo_ida, score = classificar(conexoes_ida or 0)
    tipo_volta, _ = classificar(conexoes_volta or 0)
    mudanca = texto_mudanca(item.get("mudanca_aeroporto"))
    if mudanca == "Sim":
        logistica = "Atenção"
        score = max(score - 15, 40)
    elif (conexoes_ida or 0) <= 0 and (conexoes_volta or 0) <= 0:
        logistica = "Excelente"
    elif (conexoes_ida or 0) <= 1 and (conexoes_volta or 0) <= 1:
        logistica = "Boa"
    else:
        logistica = "Moderada"
    preco_txt = f"{valor:.2f}"
    ida = item.get("data_ida") or ""
    volta = item.get("data_volta") or ""
    return {
        "id": id_alerta(origem, destino, ida, volta),
        "timestamp": agora,
        "origem": origem,
        "destino": destino,
        "cidade_origem": cidades.get(origem, origem),
        "cidade_destino": cidades.get(destino, destino),
        "companhia": item.get("companhia") or "",
        "data_ida": ida,
        "data_volta": volta,
        "preco_por_pessoa": preco_txt,
        "preco_total": preco_txt,
        "preco_referencia": f"{media_f:.2f}",
        "fonte_referencia": referencia.get("fonte") or "",
        "desconto_percentual": f"{desconto:.1f}",
        "economia_estimada": f"{media_f - valor:.2f}",
        "tipo_voo_ida": tipo_ida,
        "tipo_voo_volta": tipo_volta,
        "total_conexoes": str((conexoes_ida or 0) + (conexoes_volta or 0)),
        "conexoes_ida": str(conexoes_ida or 0),
        "conexoes_volta": str(conexoes_volta or 0),
        "duracao_total_ida": item.get("duracao_ida") or "",
        "duracao_total_volta": item.get("duracao_volta") or "",
        "mudanca_aeroporto": mudanca,
        "aeroportos_conexao": item.get("aeroportos_conexao") or "",
        "classificacao_logistica": logistica,
        "score": str(score),
        "bagagem_incluida": "",
        "link": link_ida_volta(origem, destino, ida, volta),
    }


def dentro_do_desconto(linha: dict, minimo: float) -> bool:
    desconto = percentual_abaixo(linha.get("preco_por_pessoa"), linha.get("preco_referencia"))
    return desconto is not None and desconto >= minimo


def chave_celula(linha: dict) -> tuple[str, str, str, str]:
    return (
        str(linha.get("origem", "")).upper(),
        str(linha.get("destino", "")).upper(),
        str(linha.get("data_ida", ""))[:10],
        str(linha.get("data_volta", ""))[:10],
    )


def mesclar(existentes: list[dict], novas: list[dict]) -> list[dict]:
    substituidas = {chave_celula(linha) for linha in novas}
    mantidas = [linha for linha in existentes if chave_celula(linha) not in substituidas]
    return novas + mantidas


def caminho_alertas(config: dict, raiz: Path) -> Path:
    relativo = (config.get("alerta") or {}).get("arquivo", "data/alertas.csv")
    return raiz / relativo


def estatisticas(linhas: list[dict], agora: str, novas: int, observacoes: int) -> dict:
    precos = []
    descontos = []
    for linha in linhas:
        try:
            precos.append(float(linha["preco_por_pessoa"]))
        except (KeyError, TypeError, ValueError):
            pass
        try:
            descontos.append(float(linha["desconto_percentual"]))
        except (KeyError, TypeError, ValueError):
            pass
    return {
        "ultima_atualizacao": agora,
        "total_oportunidades": len(linhas),
        "novas_semana": novas,
        "observacoes_novas": observacoes,
        "maior_desconto": round(max(descontos), 1) if descontos else 0,
        "melhor_custo_milheiro": 0,
        "melhor_preco": round(min(precos), 2) if precos else 0,
    }


def _agora_dt(agora: str) -> datetime:
    try:
        dt = datetime.fromisoformat(agora.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def gravar(raiz: Path, config: dict, cotacoes: dict, agora: str | None = None) -> dict:
    momento = agora or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    momento_dt = _agora_dt(momento)
    cidades = config.get("cidades", {})
    origens_brasil = {codigo.strip().upper() for codigo in config.get("origens_brasil", [])}
    estadia_min, estadia_max = limites_estadia(config)
    minimo_desconto = desconto_minimo(config)

    obs_path = baseline_mod.caminho_observacoes(config, raiz)
    observacoes_existentes = baseline_mod.ler_observacoes(obs_path)
    novas_obs: list[dict] = []
    for item in cotacoes.get("itens") or []:
        obs = baseline_mod.observacao_de_item(item, momento)
        if not obs:
            continue
        if obs["origem"] not in origens_brasil:
            continue
        dias = estadia_dias(obs["data_ida"], obs["data_volta"])
        if dias is None or dias < estadia_min or dias > estadia_max:
            continue
        novas_obs.append(obs)
    # Baseline usa só o histórico anterior — a cotação atual não puxa a mediana.
    baseline_mod.append_observacoes(obs_path, novas_obs)

    novas = []
    for item in cotacoes.get("itens") or []:
        origem = str(item.get("origem") or "").strip().upper()
        destino = str(item.get("destino") or "").strip().upper()
        referencia = baseline_mod.referencia_alerta(
            observacoes_existentes,
            origem,
            destino,
            config,
            preco_pagina=media_vista(item),
            agora=momento_dt,
        )
        linha = linha_de_cotacao(
            item,
            cidades,
            momento,
            origens_brasil,
            estadia_min,
            estadia_max,
            minimo_desconto,
            referencia,
        )
        if linha:
            novas.append(linha)

    planilha = raiz / config["planilha"]
    mescladas = [
        linha
        for linha in mesclar(ler_csv(planilha), novas)
        if (dias := estadia_dias(linha.get("data_ida"), linha.get("data_volta"))) is not None
        and estadia_min <= dias <= estadia_max
        and dentro_do_desconto(linha, minimo_desconto)
    ]
    # Normaliza colunas antigas sem fonte_referencia
    for linha in mescladas:
        linha.setdefault("fonte_referencia", linha.get("fonte_referencia") or "")
    escrever_csv(planilha, mescladas, COLUNAS)

    alertas_path = caminho_alertas(config, raiz)
    alertas = [
        {
            "id": linha["id"],
            "emitido_em": linha["timestamp"],
            "origem": linha["origem"],
            "destino": linha["destino"],
            "data_ida": linha["data_ida"],
            "data_volta": linha["data_volta"],
            "preco": linha["preco_por_pessoa"],
            "baseline": linha["preco_referencia"],
            "fonte_referencia": linha.get("fonte_referencia") or "",
            "desconto_percentual": linha["desconto_percentual"],
            "link": linha["link"],
        }
        for linha in mescladas
    ]
    escrever_csv(alertas_path, alertas, COLUNAS_ALERTAS)

    stats = estatisticas(mescladas, momento, len(novas), len(novas_obs))
    destino_stats = raiz / config["estatisticas"]
    destino_stats.parent.mkdir(parents=True, exist_ok=True)
    destino_stats.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "cotadas": len(novas),
        "observacoes": len(novas_obs),
        "total": len(mescladas),
        "estatisticas": stats,
    }


def main() -> int:
    config = carregar_config()
    caminho = RAIZ / config["cotacoes"]
    if not caminho.exists():
        print(f"Sem arquivo de cotações ({caminho.name}). CSV mantido.")
        return 0
    cotacoes = json.loads(caminho.read_text(encoding="utf-8"))
    resultado = gravar(RAIZ, config, cotacoes)
    print(
        f"Observações novas: {resultado['observacoes']}. "
        f"Alertas nesta rodada: {resultado['cotadas']}. "
        f"Linhas no CSV: {resultado['total']}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
