"""Links do Google Flights com ida e volta já preenchidas."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta


def _varint(valor: int) -> bytes:
    saida = bytearray()
    while True:
        byte = valor & 0x7F
        valor >>= 7
        if valor:
            saida.append(byte | 0x80)
        else:
            saida.append(byte)
            return bytes(saida)


def _chave(campo: int, tipo: int) -> bytes:
    return _varint((campo << 3) | tipo)


def _texto(campo: int, valor: str) -> bytes:
    dados = valor.encode()
    return _chave(campo, 2) + _varint(len(dados)) + dados


def _inteiro(campo: int, valor: int) -> bytes:
    return _chave(campo, 0) + _varint(valor)


def _mensagem(campo: int, conteudo: bytes) -> bytes:
    return _chave(campo, 2) + _varint(len(conteudo)) + conteudo


def _aeroporto(codigo: str) -> bytes:
    return _inteiro(1, 1) + _texto(2, codigo)


def _trecho(data: str, origem: str, destino: str) -> bytes:
    return _texto(2, data) + _mensagem(13, _aeroporto(origem)) + _mensagem(14, _aeroporto(destino))


def tfs_ida_volta(origem: str, destino: str, data_ida: str, data_volta: str) -> str:
    """Monta o parâmetro tfs que o Google Flights usa para preencher a busca."""
    origem = origem.strip().upper()
    destino = destino.strip().upper()
    ida = str(data_ida)[:10]
    volta = str(data_volta)[:10]
    corpo = (
        _inteiro(1, 28)
        + _inteiro(2, 2)
        + _mensagem(3, _trecho(ida, origem, destino))
        + _mensagem(3, _trecho(volta, destino, origem))
        + _inteiro(8, 1)
        + _inteiro(9, 1)
        + _inteiro(14, 1)
        + _mensagem(16, _inteiro(1, (1 << 64) - 1))
        + _inteiro(19, 1)
    )
    return base64.urlsafe_b64encode(corpo).decode().rstrip("=")


def link_ida_volta(origem: str, destino: str, data_ida: str, data_volta: str) -> str:
    tfs = tfs_ida_volta(origem, destino, data_ida, data_volta)
    return f"https://www.google.com/travel/flights/search?tfs={tfs}&hl=pt-BR&curr=BRL"


def link_busca(origem: str, destino: str, janela: dict) -> str:
    ida = datetime.strptime(janela["ida_inicio"], "%Y-%m-%d")
    volta = ida + timedelta(days=int(janela["estadia_dias_min"]))
    return link_ida_volta(origem, destino, ida.date().isoformat(), volta.date().isoformat())
