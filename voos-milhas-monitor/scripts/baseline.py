#!/usr/bin/env python3
"""Histórico append-only de observações e baseline (mediana) por rota."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

RAIZ = Path(__file__).resolve().parents[1]
CONFIG_PATH = RAIZ / "config-rotina.json"

COLUNAS_OBS = [
    "observado_em",
    "origem",
    "destino",
    "data_ida",
    "data_volta",
    "preco",
    "companhia",
    "fonte",
    "id_celula",
]


def carregar_config(caminho: Path | None = None) -> dict:
    return json.loads((caminho or CONFIG_PATH).read_text(encoding="utf-8"))


def caminho_observacoes(config: dict, raiz: Path | None = None) -> Path:
    base = raiz or RAIZ
    relativo = (config.get("baseline") or {}).get("observacoes", "data/observacoes.csv")
    return base / relativo


def ler_observacoes(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def escrever_observacoes(caminho: Path, linhas: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_OBS, lineterminator="\n")
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({coluna: linha.get(coluna, "") for coluna in COLUNAS_OBS})


def append_observacoes(caminho: Path, novas: list[dict]) -> int:
    if not novas:
        return 0
    existentes = ler_observacoes(caminho)
    existentes.extend(novas)
    escrever_observacoes(caminho, existentes)
    return len(novas)


def _parse_ts(texto: str) -> datetime | None:
    if not texto:
        return None
    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        return None


def _float(valor) -> float | None:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if numero > 0 else None


def observacoes_na_janela(
    observacoes: list[dict],
    origem: str,
    destino: str,
    agora: datetime,
    janela_dias: int,
) -> list[float]:
    corte = agora - timedelta(days=max(int(janela_dias), 1))
    precos: list[float] = []
    origem_u = origem.upper()
    destino_u = destino.upper()
    for linha in observacoes:
        if str(linha.get("origem", "")).upper() != origem_u:
            continue
        if str(linha.get("destino", "")).upper() != destino_u:
            continue
        ts = _parse_ts(str(linha.get("observado_em") or ""))
        if ts is None or ts < corte:
            continue
        preco = _float(linha.get("preco"))
        if preco is not None:
            precos.append(preco)
    return precos


def calcular_baseline(
    observacoes: list[dict],
    origem: str,
    destino: str,
    config: dict,
    agora: datetime | None = None,
) -> dict:
    cfg = config.get("baseline") or {}
    janela = int(cfg.get("janela_dias", 90))
    minimo = int(cfg.get("min_observacoes", 3))
    metrica = str(cfg.get("metrica", "mediana")).lower()
    momento = agora or datetime.now(timezone.utc)
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    precos = observacoes_na_janela(observacoes, origem, destino, momento, janela)
    if len(precos) < minimo:
        return {
            "valor": None,
            "n": len(precos),
            "minimo": minimo,
            "suficiente": False,
            "metrica": metrica,
            "janela_dias": janela,
        }
    if metrica == "media":
        valor = sum(precos) / len(precos)
    else:
        valor = float(median(precos))
    return {
        "valor": round(valor, 2),
        "n": len(precos),
        "minimo": minimo,
        "suficiente": True,
        "metrica": metrica,
        "janela_dias": janela,
    }


def referencia_alerta(
    observacoes: list[dict],
    origem: str,
    destino: str,
    config: dict,
    preco_pagina=None,
    agora: datetime | None = None,
) -> dict:
    """Baseline próprio; se ainda frio, usa média da página como bootstrap."""
    base = calcular_baseline(observacoes, origem, destino, config, agora=agora)
    if base["suficiente"] and base["valor"] is not None:
        return {
            "valor": base["valor"],
            "fonte": "baseline",
            "n": base["n"],
            "detalhe": base,
        }
    pagina = _float(preco_pagina)
    if pagina is not None:
        return {
            "valor": round(pagina, 2),
            "fonte": "pagina",
            "n": base["n"],
            "detalhe": base,
        }
    return {
        "valor": None,
        "fonte": "indisponivel",
        "n": base["n"],
        "detalhe": base,
    }


def observacao_de_item(item: dict, observado_em: str) -> dict | None:
    origem = str(item.get("origem") or "").strip().upper()
    destino = str(item.get("destino") or "").strip().upper()
    preco = _float(item.get("preco"))
    ida = str(item.get("data_ida") or "")[:10]
    volta = str(item.get("data_volta") or "")[:10]
    if not origem or not destino or preco is None or not ida or not volta:
        return None
    return {
        "observado_em": observado_em,
        "origem": origem,
        "destino": destino,
        "data_ida": ida,
        "data_volta": volta,
        "preco": f"{preco:.2f}",
        "companhia": item.get("companhia") or "",
        "fonte": item.get("fonte") or "Google Flights",
        "id_celula": f"{origem}_{destino}_{ida}_{volta}",
    }
