#!/usr/bin/env python3
"""Imprime as rotas da rotina semanal e o link público de cada uma."""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "config-rotina.json"


def carregar() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def link_google(origem: str, destino: str, janela: dict) -> str:
    consulta = (
        f"Voos de {origem} para {destino} "
        f"entre {janela['ida_inicio']} e {janela['ida_fim']} "
        f"ida e volta {janela['estadia_dias_min']} a {janela['estadia_dias_max']} dias"
    )
    return (
        "https://www.google.com/travel/flights?hl=pt-BR&curr=BRL&q="
        + urllib.parse.quote(consulta)
    )


def rotas(config: dict) -> list[dict]:
    cidades = config.get("cidades", {})
    janela = config["janela"]
    saida = []
    for grupo in config["grupos"]:
        for origem in grupo["origens"]:
            for destino in grupo["destinos"]:
                saida.append(
                    {
                        "grupo": grupo["nome"],
                        "origem": origem,
                        "destino": destino,
                        "cidade_origem": cidades.get(origem, origem),
                        "cidade_destino": cidades.get(destino, destino),
                        "link": link_google(origem, destino, janela),
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
