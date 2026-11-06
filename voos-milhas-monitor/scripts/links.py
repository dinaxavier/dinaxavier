"""Links públicos de passagem de ida e volta."""

from __future__ import annotations

import urllib.parse


def link_ida_volta(origem: str, destino: str, data_ida: str, data_volta: str) -> str:
    consulta = (
        f"Passagem de ida e volta de {origem.strip().upper()} para {destino.strip().upper()} "
        f"saindo em {str(data_ida)[:10]} e voltando em {str(data_volta)[:10]}"
    )
    return "https://www.google.com/travel/flights?hl=pt-BR&curr=BRL&q=" + urllib.parse.quote(consulta)


def link_busca(origem: str, destino: str, janela: dict) -> str:
    consulta = (
        f"Passagens de ida e volta de {origem.strip().upper()} para {destino.strip().upper()} "
        f"saindo entre {janela['ida_inicio']} e {janela['ida_fim']} "
        f"com volta de {janela['estadia_dias_min']} a {janela['estadia_dias_max']} dias"
    )
    return "https://www.google.com/travel/flights?hl=pt-BR&curr=BRL&q=" + urllib.parse.quote(consulta)
