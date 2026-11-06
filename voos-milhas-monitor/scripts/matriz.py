#!/usr/bin/env python3
"""Gera a matriz rota × data_ida × estadia e amostra células por rodada."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from links import link_ida_volta

RAIZ = Path(__file__).resolve().parents[1]
CONFIG_PATH = RAIZ / "config-rotina.json"
ESTADO_PADRAO = "out/matriz_estado.json"


def carregar_config(caminho: Path | None = None) -> dict:
    return json.loads((caminho or CONFIG_PATH).read_text(encoding="utf-8"))


def _parse_data(texto: str) -> datetime:
    return datetime.strptime(str(texto)[:10], "%Y-%m-%d")


def datas_ida(janela: dict, passo: int) -> list[str]:
    inicio = _parse_data(janela["ida_inicio"])
    fim = _parse_data(janela["ida_fim"])
    if fim < inicio:
        return []
    passo = max(int(passo), 1)
    saida: list[str] = []
    atual = inicio
    while atual <= fim:
        saida.append(atual.date().isoformat())
        atual += timedelta(days=passo)
    if saida and saida[-1] != fim.date().isoformat():
        saida.append(fim.date().isoformat())
    return saida


def estadias_config(config: dict) -> list[int]:
    matriz = config.get("matriz") or {}
    if matriz.get("estadias"):
        return sorted({int(d) for d in matriz["estadias"] if int(d) > 0})
    janela = config.get("janela") or {}
    minimo = int(janela.get("estadia_dias_min", 7))
    maximo = int(janela.get("estadia_dias_max", 15))
    if maximo < minimo:
        minimo, maximo = maximo, minimo
    meio = (minimo + maximo) // 2
    return sorted({minimo, meio, maximo})


def rotas_config(config: dict) -> list[dict]:
    cidades = config.get("cidades", {})
    brasil = {codigo.strip().upper() for codigo in config.get("origens_brasil", [])}
    saida = []
    for grupo in config.get("grupos") or []:
        for origem in grupo.get("origens") or []:
            origem_u = str(origem).strip().upper()
            if brasil and origem_u not in brasil:
                continue
            for destino in grupo.get("destinos") or []:
                destino_u = str(destino).strip().upper()
                saida.append(
                    {
                        "grupo": grupo.get("nome") or "",
                        "origem": origem_u,
                        "destino": destino_u,
                        "cidade_origem": cidades.get(origem_u, origem_u),
                        "cidade_destino": cidades.get(destino_u, destino_u),
                    }
                )
    return saida


def gerar_celulas(config: dict) -> list[dict]:
    matriz = config.get("matriz") or {}
    passo = int(matriz.get("passo_ida_dias", 7))
    idas = datas_ida(config.get("janela") or {}, passo)
    estadias = estadias_config(config)
    celulas = []
    for rota in rotas_config(config):
        for ida in idas:
            for estadia in estadias:
                volta_dt = _parse_data(ida) + timedelta(days=estadia)
                volta = volta_dt.date().isoformat()
                celulas.append(
                    {
                        **rota,
                        "data_ida": ida,
                        "data_volta": volta,
                        "estadia_dias": estadia,
                        "id_celula": f"{rota['origem']}_{rota['destino']}_{ida}_{volta}",
                        "link": link_ida_volta(
                            rota["origem"], rota["destino"], ida, volta
                        ),
                    }
                )
    return celulas


def caminho_estado(config: dict, raiz: Path | None = None) -> Path:
    base = raiz or RAIZ
    relativo = (config.get("matriz") or {}).get("estado", ESTADO_PADRAO)
    return base / relativo


def ler_estado(caminho: Path) -> dict:
    if not caminho.exists():
        return {"offset": 0, "ultima_rodada": None, "total_celulas": 0}
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"offset": 0, "ultima_rodada": None, "total_celulas": 0}


def gravar_estado(caminho: Path, estado: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def amostrar_celulas(
    celulas: list[dict],
    config: dict,
    estado: dict | None = None,
    avancar: bool = True,
) -> tuple[list[dict], dict]:
    matriz = config.get("matriz") or {}
    limite = max(int(matriz.get("max_celulas_por_rodada", 40)), 1)
    atual = dict(estado or {"offset": 0})
    total = len(celulas)
    if total == 0:
        atual.update({"offset": 0, "total_celulas": 0, "amostradas": 0})
        return [], atual

    if not matriz.get("rotacao", True):
        amostra = celulas[:limite]
        atual.update(
            {
                "offset": 0,
                "total_celulas": total,
                "amostradas": len(amostra),
                "cobertura_pct": round(100 * len(amostra) / total, 1),
            }
        )
        return amostra, atual

    offset = int(atual.get("offset") or 0) % total
    amostra = []
    for i in range(min(limite, total)):
        amostra.append(celulas[(offset + i) % total])
    novo_offset = (offset + len(amostra)) % total if avancar else offset
    atual.update(
        {
            "offset": novo_offset,
            "offset_anterior": offset,
            "total_celulas": total,
            "amostradas": len(amostra),
            "cobertura_pct": round(100 * len(amostra) / total, 1),
        }
    )
    return amostra, atual


def listar_rodada(
    config: dict,
    raiz: Path | None = None,
    avancar: bool = True,
) -> dict:
    base = raiz or RAIZ
    celulas = gerar_celulas(config)
    caminho = caminho_estado(config, base)
    estado = ler_estado(caminho)
    amostra, novo_estado = amostrar_celulas(celulas, config, estado, avancar=avancar)
    novo_estado["ultima_rodada"] = datetime.now().astimezone().replace(microsecond=0).isoformat()
    if avancar:
        gravar_estado(caminho, novo_estado)
    return {
        "total_celulas": len(celulas),
        "amostra": amostra,
        "estado": novo_estado,
        "estado_path": str(caminho.relative_to(base)) if caminho.is_relative_to(base) else str(caminho),
    }


def main() -> int:
    config = carregar_config()
    resultado = listar_rodada(config, avancar=True)
    amostra = resultado["amostra"]
    print(
        f"{resultado['total_celulas']} células na matriz. "
        f"Rodada: {len(amostra)} células "
        f"(passo={((config.get('matriz') or {}).get('passo_ida_dias', 7))}d, "
        f"estadias={estadias_config(config)})."
    )
    for item in amostra:
        print(
            f"{item['grupo']}\t{item['origem']}→{item['destino']}\t"
            f"{item['data_ida']}→{item['data_volta']}\t"
            f"{item['estadia_dias']}d\t{item['link']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
