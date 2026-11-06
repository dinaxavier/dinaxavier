#!/usr/bin/env python3
"""Classifica promoções de milhas: Excelente / Regular / Ruim.

Custo efetivo do milheiro após bônus de transferência =
  custo_base / (1 + bonus_transferencia/100)
"""

from __future__ import annotations

import re
from typing import Any


def _float(valor) -> float | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor) if float(valor) > 0 else None
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    texto = texto.replace(".", "").replace(",", ".") if texto.count(",") == 1 and texto.count(".") > 1 else texto
    texto = texto.replace(",", ".")
    try:
        numero = float(re.sub(r"[^0-9.]", "", texto))
    except ValueError:
        return None
    return numero if numero > 0 else None


def extrair_milheiro(texto: str) -> float | None:
    padroes = [
        r"milheiro[^\d]{0,20}(?:a partir(?: de)?|de|por)?\s*R\$?\s*(\d+[.,]\d{2})",
        r"(?:a partir(?: de)?|desde)\s*R\$?\s*(\d+[.,]\d{2})[^\d]{0,20}milheiro",
        r"R\$?\s*(\d+[.,]\d{2})\s*/\s*milheiro",
        r"milheiro\s+a\s+partir\s+R\$?\s*(\d+[.,]\d{2})",
    ]
    for padrao in padroes:
        m = re.search(padrao, texto, re.I)
        if m:
            return _float(m.group(1).replace(",", "."))
    return None


def extrair_bonus_transferencia(texto: str) -> float | None:
    m = re.search(
        r"(\d{1,3})\s*%\s*(?:de\s+)?b[oô]nus[^\n.]{0,40}transfer",
        texto,
        re.I,
    )
    if m:
        return float(m.group(1))
    m = re.search(
        r"transfer[^\n.]{0,40}(\d{1,3})\s*%\s*(?:de\s+)?b[oô]nus",
        texto,
        re.I,
    )
    if m:
        return float(m.group(1))
    m = re.search(r"at[eé]\s+(\d{1,3})\s*%\s*(?:de\s+)?b[oô]nus", texto, re.I)
    if m and re.search(r"transfer", texto, re.I):
        return float(m.group(1))
    return None


def custo_efetivo(custo_base: float | None, bonus_pct: float | None) -> float | None:
    if custo_base is None:
        return None
    if bonus_pct is None or bonus_pct <= 0:
        return round(custo_base, 2)
    return round(custo_base / (1 + bonus_pct / 100), 2)


def classificar(custo_efetivo_valor: float | None, config: dict, texto: str = "") -> str:
    regras = config.get("avaliacao") or {}
    excelente_ate = float(regras.get("excelente_ate", 18))
    regular_ate = float(regras.get("regular_ate", 28))
    baixo = texto.lower()
    # Turbo / aceleradores costumam ser caros na compra isolada.
    if re.search(r"\bturbo\b|multiplique seus pontos|aceler", baixo) and (
        custo_efetivo_valor is None or custo_efetivo_valor > excelente_ate
    ):
        return "Ruim"
    if custo_efetivo_valor is None:
        # Só bônus de transferência, sem preço: depende do caso.
        if re.search(r"transfer", baixo):
            return "Regular"
        return "Regular"
    if custo_efetivo_valor <= excelente_ate:
        return "Excelente"
    if custo_efetivo_valor <= regular_ate:
        return "Regular"
    return "Ruim"


def nota_avaliacao(
    classificacao: str,
    custo_base: float | None,
    custo_pos: float | None,
    bonus_transfer: float | None,
    texto: str,
) -> str:
    baixo = texto.lower()
    if "turbo" in baixo and custo_base is not None:
        if custo_pos is not None and bonus_transfer:
            return (
                f"Ruim para compra isolada (milheiro ~R$ {custo_base:.2f}). "
                f"Pode valer se houver transferência com ~{bonus_transfer:.0f}% "
                f"(efetivo ~R$ {custo_pos:.2f})."
            )
        return (
            f"Ruim para compra isolada (milheiro ~R$ {custo_base:.2f}), "
            "mas pode aproveitar se houver transferência bonificada vantajosa."
        )
    if classificacao == "Excelente" and custo_pos is not None:
        return f"Custo efetivo competitivo (~R$ {custo_pos:.2f}/milheiro)."
    if classificacao == "Regular":
        if custo_base is None:
            return "Depende do bônus, do programa de destino e da emissão específica."
        return (
            f"Custo intermediário (~R$ {(custo_pos or custo_base):.2f}/milheiro); "
            "vale comparar com a emissão que você pretende fazer."
        )
    if custo_pos is not None:
        return f"Custo elevado (~R$ {custo_pos:.2f}/milheiro) sem vantagem clara na compra isolada."
    return "Sem vantagem comprovada na compra isolada."


def score_de(classificacao: str) -> str:
    return {"Excelente": "92", "Regular": "70", "Ruim": "40"}.get(classificacao, "60")


def avaliar_promocao(
    *,
    programa: dict | None,
    titulo: str,
    descricao: str,
    config: dict,
    bonus_percentual: str | float | None = None,
) -> dict[str, Any]:
    texto = f"{titulo} {descricao}"
    regras = config.get("avaliacao") or {}
    refs = regras.get("bonus_transferencia_referencia") or {}

    custo_base = extrair_milheiro(texto)
    bonus_transfer = extrair_bonus_transferencia(texto)
    if bonus_transfer is None:
        bonus_transfer = _float(bonus_percentual) if bonus_percentual not in (None, "") else None
        if bonus_transfer is not None and not re.search(r"transfer", texto, re.I):
            # bônus genérico de compra/clube não é bônus de transferência
            bonus_transfer = None

    # Coalizões: se há milheiro de compra e não veio bônus de transferência na matéria,
    # usa referência configurada só para o campo "após transferência".
    bonus_ref = None
    prog_id = (programa or {}).get("id") or ""
    tipo = (programa or {}).get("tipo") or ""
    if custo_base is not None and bonus_transfer is None and tipo == "coalizao":
        bonus_ref = _float(refs.get(prog_id))
    bonus_para_efetivo = bonus_transfer if bonus_transfer is not None else bonus_ref

    efetivo_pos = custo_efetivo(custo_base, bonus_para_efetivo)
    # Classificação da compra isolada usa o milheiro sem transfer (ou Regular se só transfer).
    custo_isolado = custo_base
    classificacao = classificar(custo_isolado, config, texto)
    nota = nota_avaliacao(classificacao, custo_base, efetivo_pos, bonus_para_efetivo, texto)

    return {
        "custo_por_milheiro": f"{custo_base:.2f}" if custo_base is not None else "",
        "bonus_transferencia_percentual": (
            f"{bonus_para_efetivo:.0f}" if bonus_para_efetivo is not None else ""
        ),
        "custo_efetivo_milheiro": f"{efetivo_pos:.2f}" if efetivo_pos is not None else "",
        "classificacao": classificacao,
        "nota_avaliacao": nota,
        "score": score_de(classificacao),
        "bonus_referencia": bonus_ref is not None and bonus_transfer is None,
    }
