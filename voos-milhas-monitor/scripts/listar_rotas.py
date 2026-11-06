#!/usr/bin/env python3
"""Imprime a amostra da matriz de datas desta rodada (e o link de cada célula)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matriz

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "config-rotina.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Lista células da matriz para cotar.")
    parser.add_argument(
        "--sem-avancar",
        action="store_true",
        help="Só lista a amostra; não move o cursor de rotação.",
    )
    parser.add_argument(
        "--resumo",
        action="store_true",
        help="Só imprime o tamanho da matriz, sem listar células.",
    )
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if args.resumo:
        celulas = matriz.gerar_celulas(config)
        print(
            f"{len(celulas)} células. "
            f"Rotas={len(matriz.rotas_config(config))} "
            f"passo={((config.get('matriz') or {}).get('passo_ida_dias', 7))}d "
            f"estadias={matriz.estadias_config(config)} "
            f"max/rodada={((config.get('matriz') or {}).get('max_celulas_por_rodada', 40))}."
        )
        return 0

    resultado = matriz.listar_rodada(config, avancar=not args.sem_avancar)
    amostra = resultado["amostra"]
    minimo = float(
        ((config.get("alerta") or {}).get("desconto_minimo_percentual"))
        or config.get("desconto_minimo_percentual", 25)
    )
    print(
        f"{resultado['total_celulas']} células na matriz. "
        f"Amostra desta rodada: {len(amostra)}. "
        f"Alerta se ≥ {minimo:.0f}% abaixo do baseline."
    )
    for item in amostra:
        print(
            f"{item['grupo']}\t{item['origem']} {item['cidade_origem']} → "
            f"{item['destino']} {item['cidade_destino']}\t"
            f"{item['data_ida']} → {item['data_volta']}\t"
            f"{item['estadia_dias']}d\t{item['link']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
