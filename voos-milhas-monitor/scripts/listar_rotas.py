#!/usr/bin/env python3
"""Imprime as rotas da rotina semanal e o link público de cada uma."""

from __future__ import annotations

import json
from pathlib import Path

from links import link_busca

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "config-rotina.json"


def carregar() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def rotas(config: dict) -> list[dict]:
    cidades = config.get("cidades", {})
    janela = config["janela"]
    brasil = {codigo.strip().upper() for codigo in config.get("origens_brasil", [])}
    saida = []
    for grupo in config["grupos"]:
        for origem in grupo["origens"]:
            if brasil and origem.upper() not in brasil:
                continue
            for destino in grupo["destinos"]:
                saida.append(
                    {
                        "grupo": grupo["nome"],
                        "origem": origem,
                        "destino": destino,
                        "cidade_origem": cidades.get(origem, origem),
                        "cidade_destino": cidades.get(destino, destino),
                        "link": link_busca(origem, destino, janela),
                    }
                )
    return saida


def main() -> int:
    config = carregar()
    itens = rotas(config)
    print(f"{len(itens)} rotas. Janela {config['janela']['ida_inicio']} a {config['janela']['ida_fim']}.")
    for item in itens:
        print(
            f"{item['grupo']}\t{item['origem']} {item['cidade_origem']} → "
            f"{item['destino']} {item['cidade_destino']}\t{item['link']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
