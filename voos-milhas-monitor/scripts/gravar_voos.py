#!/usr/bin/env python3
"""Grava no CSV só ida e volta vista, pelo menos 30% abaixo da média vista.

Rotas ausentes em out/cotacoes.json permanecem se ainda cumprirem a regra.
Sem a média vista na página, a cotação não entra.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def carregar_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def ler_csv(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def escrever_csv(caminho: Path, linhas: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, lineterminator="\n")
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({coluna: linha.get(coluna, "") for coluna in COLUNAS})


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
    return float(config.get("desconto_minimo_percentual", 30))


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


def linha_de_cotacao(
    item: dict,
    cidades: dict,
    agora: str,
    origens_brasil: set[str],
    estadia_min: int,
    estadia_max: int,
    desconto_min: float,
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
    media = media_vista(item)
    desconto = percentual_abaixo(valor, media)
    if desconto is None or desconto < desconto_min:
        return None
    media_f = float(media)
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
    return {
        "id": f"ROTA_{origem}_{destino}",
        "timestamp": agora,
        "origem": origem,
        "destino": destino,
        "cidade_origem": cidades.get(origem, origem),
        "cidade_destino": cidades.get(destino, destino),
        "companhia": item.get("companhia") or "",
        "data_ida": item.get("data_ida") or "",
        "data_volta": item.get("data_volta") or "",
        "preco_por_pessoa": preco_txt,
        "preco_total": preco_txt,
        "preco_referencia": f"{media_f:.2f}",
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
        "link": link_ida_volta(origem, destino, item.get("data_ida") or "", item.get("data_volta") or ""),
    }


def dentro_do_desconto(linha: dict, minimo: float) -> bool:
    desconto = percentual_abaixo(linha.get("preco_por_pessoa"), linha.get("preco_referencia"))
    return desconto is not None and desconto >= minimo


def mesclar(existentes: list[dict], novas: list[dict]) -> list[dict]:
    substituidas = {(linha["origem"], linha["destino"]) for linha in novas}
    mantidas = [
        linha
        for linha in existentes
        if (linha.get("origem", "").upper(), linha.get("destino", "").upper())
        not in substituidas
    ]
    return novas + mantidas


def estatisticas(linhas: list[dict], agora: str, novas: int) -> dict:
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
        "maior_desconto": round(max(descontos), 1) if descontos else 0,
        "melhor_custo_milheiro": 0,
        "melhor_preco": round(min(precos), 2) if precos else 0,
    }


def gravar(raiz: Path, config: dict, cotacoes: dict, agora: str | None = None) -> dict:
    momento = agora or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    cidades = config.get("cidades", {})
    origens_brasil = {codigo.strip().upper() for codigo in config.get("origens_brasil", [])}
    estadia_min, estadia_max = limites_estadia(config)
    minimo_desconto = desconto_minimo(config)
    novas = []
    for item in cotacoes.get("itens") or []:
        linha = linha_de_cotacao(
            item,
            cidades,
            momento,
            origens_brasil,
            estadia_min,
            estadia_max,
            minimo_desconto,
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
    escrever_csv(planilha, mescladas)
    stats = estatisticas(mescladas, momento, len(novas))
    destino_stats = raiz / config["estatisticas"]
    destino_stats.parent.mkdir(parents=True, exist_ok=True)
    destino_stats.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"cotadas": len(novas), "total": len(mescladas), "estatisticas": stats}


def main() -> int:
    config = carregar_config()
    caminho = RAIZ / config["cotacoes"]
    if not caminho.exists():
        print(f"Sem arquivo de cotações ({caminho.name}). CSV mantido.")
        return 0
    cotacoes = json.loads(caminho.read_text(encoding="utf-8"))
    resultado = gravar(RAIZ, config, cotacoes)
    print(
        f"Cotadas nesta rodada: {resultado['cotadas']}. "
        f"Linhas no CSV: {resultado['total']}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
