#!/usr/bin/env python3
"""Grava no CSV só as cotações que a rotina realmente viu.

Rotas ausentes em out/cotacoes.json permanecem como estão.
Não calcula desconto inventado: preço de referência fica igual ao preço visto.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

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
    "duracao_total_ida",
    "duracao_total_volta",
    "mudanca_aeroporto",
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


def classificar(conexoes: int) -> tuple[str, str, int]:
    if conexoes <= 0:
        return "Direto", "Excelente", 90
    if conexoes == 1:
        return "1 conexão", "Boa", 80
    return "2+ conexões", "Moderada", 70


def linha_de_cotacao(item: dict, cidades: dict, agora: str) -> dict | None:
    origem = str(item.get("origem") or "").strip().upper()
    destino = str(item.get("destino") or "").strip().upper()
    preco = item.get("preco")
    if not origem or not destino or preco in (None, ""):
        return None
    try:
        valor = float(preco)
    except (TypeError, ValueError):
        return None
    if valor <= 0:
        return None
    try:
        conexoes = int(item.get("conexoes") if item.get("conexoes") is not None else 0)
    except (TypeError, ValueError):
        conexoes = 0
    tipo, logistica, score = classificar(conexoes)
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
        "preco_referencia": preco_txt,
        "desconto_percentual": "0",
        "economia_estimada": "0",
        "tipo_voo_ida": tipo,
        "tipo_voo_volta": tipo,
        "total_conexoes": str(conexoes),
        "duracao_total_ida": item.get("duracao_ida") or "",
        "duracao_total_volta": item.get("duracao_volta") or "",
        "mudanca_aeroporto": "",
        "classificacao_logistica": logistica,
        "score": str(score),
        "bagagem_incluida": "",
        "link": item.get("link") or "",
    }


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
    novas = []
    for item in cotacoes.get("itens") or []:
        linha = linha_de_cotacao(item, cidades, momento)
        if linha:
            novas.append(linha)
    planilha = raiz / config["planilha"]
    mescladas = mesclar(ler_csv(planilha), novas)
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
