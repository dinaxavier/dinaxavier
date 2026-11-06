#!/usr/bin/env python3
"""Coleta promoções de compra de milhas/pontos nos programas mapeados.

Fontes: feeds RSS de portais de fidelidade (Passageiro de Primeira, Melhores Destinos).
Grava oportunidades ativas em data/milhas_ativas.csv para o balão do dashboard.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import avaliar_milhas

MAX_IDADE_DIAS = 14

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "config-milhas.json"
COLUNAS = [
    "id",
    "timestamp",
    "programa",
    "tipo_promocao",
    "descricao",
    "custo_por_milheiro",
    "bonus_percentual",
    "bonus_transferencia_percentual",
    "custo_efetivo_milheiro",
    "classificacao",
    "nota_avaliacao",
    "desconto_percentual",
    "score",
    "validade_promocao",
    "link",
    "ativo",
]

FEEDS_PADRAO = [
    "https://passageirodeprimeira.com/feed/",
    "https://passageirodeprimeira.com/category/promocoes/feed/",
    "https://passageirodeprimeira.com/tag/bonus/feed/",
    "https://www.melhoresdestinos.com.br/feed",
]

FIDELIDADE = re.compile(r"milhas|pontos|avios|milheiro|b[oô]nus|clube\s+\w+|transfer", re.I)
COMPRA = re.compile(
    r"compra|comprar|b[oô]nus|transfer|milheiro|clube\s+(smiles|livelo|azul)|"
    r"turbo\s+livelo|pontos do cart[aã]o|desconto na compra|% de b[oô]nus|"
    r"assinando o clube|compre\s+\d|ganhe\s+\d",
    re.I,
)
EMISSAO = re.compile(
    r"^voe (para|de)\b|a partir de \d+\s*mil\s*(milhas|pontos)|emiss[aã]o de voos",
    re.I,
)
RUIDO = re.compile(
    r"assina compra|aquisi[cç]|fus[aã]o|participa[cç][aã]o acion|cupom de at[eé].*passagens|"
    r"decolar|hoteis\.com|hotel",
    re.I,
)

ALIAS = {
    "smiles": ["smiles", "gol smiles"],
    "azul": ["azul fidelidade", "tudoazul", "tudo azul", "pontos azul", "azul "],
    "latam_pass": ["latam pass", "latam "],
    "livelo": ["livelo"],
    "esfera": ["esfera"],
    "iberia_avios": ["iberia", "avios"],
    "ba_avios": ["british airways", "executive club"],
    "tap_milesgo": ["tap miles", "miles&go", "miles & go", "tap "],
    "flying_blue": ["flying blue", "air france", "klm"],
    "aadvantage": ["aadvantage", "american airlines"],
    "united_mileageplus": ["mileageplus", "united "],
    "copa_connectmiles": ["connectmiles", "copa "],
    "aerolineas_plus": ["aerolíneas", "aerolineas"],
}


def carregar_config() -> dict:
    if not CONFIG.exists():
        return {"programas": [], "feeds": FEEDS_PADRAO}
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def baixar(url: str, timeout: int = 20) -> bytes | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RadarVoosMilhas/1.0 (+https://github.com/dinaxavier/dinaxavier)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError, ValueError) as erro:
        print(f"⚠ falha ao ler {url}: {erro}", file=sys.stderr)
        return None


def parse_rss(conteudo: bytes) -> list[dict]:
    try:
        root = ET.fromstring(conteudo)
    except ET.ParseError:
        return []
    itens = []
    for item in root.findall("./channel/item"):
        titulo = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = re.sub(r"\s+", " ", desc).strip()
        pub = item.findtext("pubDate") or ""
        itens.append({"titulo": titulo, "link": link, "descricao": desc, "pubDate": pub})
    return itens


def programas_por_id(config: dict) -> dict[str, dict]:
    return {p["id"]: p for p in (config.get("programas") or []) if p.get("id")}


def detectar_programa(texto: str, programas: dict[str, dict]) -> dict | None:
    baixo = texto.lower()
    # Avios + Iberia tem prioridade sobre BA genérico
    candidatos: list[tuple[int, dict]] = []
    for prog_id, aliases in ALIAS.items():
        prog = programas.get(prog_id)
        if not prog:
            continue
        if any(alias in baixo for alias in aliases):
            prioridade = int(prog.get("prioridade") or 9)
            candidatos.append((prioridade, prog))
    if not candidatos:
        # fallback pelo nome configurado
        for prog in programas.values():
            nome = str(prog.get("nome") or "").lower()
            if nome and nome in baixo:
                candidatos.append((int(prog.get("prioridade") or 9), prog))
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: x[0])
    return candidatos[0][1]


def eh_compra_milhas(titulo: str, descricao: str) -> bool:
    texto = f"{titulo} {descricao}"
    if RUIDO.search(titulo):
        return False
    if not FIDELIDADE.search(texto):
        return False
    if not COMPRA.search(texto):
        return False
    if EMISSAO.search(titulo) and not re.search(r"b[oô]nus|compra|comprar|milheiro|transfer", titulo, re.I):
        return False
    return True


def extrair_bonus(texto: str) -> str:
    m = re.search(r"(\d{1,3})\s*%\s*(?:de\s+)?b[oô]nus", texto, re.I)
    return m.group(1) if m else ""


def tipo_de(titulo: str) -> str:
    t = titulo.lower()
    if "transfer" in t:
        return "Transferência"
    if "clube" in t:
        return "Clube"
    if "compra" in t or "compre" in t:
        return "Compra"
    if "bônus" in t or "bonus" in t:
        return "Bônus"
    return "Promoção"


def data_publicacao(pub: str) -> datetime | None:
    if not pub:
        return None
    try:
        dt = parsedate_to_datetime(pub)
    except (TypeError, ValueError, IndexError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def validade_de(pub_dt: datetime | None) -> str:
    # Sem data explícita na matéria, mantém o aviso por 7 dias após a publicação.
    dt = pub_dt or datetime.now(timezone.utc)
    return (dt.date() + timedelta(days=7)).isoformat()


def coletar(config: dict) -> list[dict]:
    programas = programas_por_id(config)
    feeds = config.get("feeds") or FEEDS_PADRAO
    agora_dt = datetime.now(timezone.utc)
    agora = agora_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    corte = agora_dt - timedelta(days=MAX_IDADE_DIAS)
    vistos: set[str] = set()
    saida: list[dict] = []
    for feed in feeds:
        bruto = baixar(feed)
        if not bruto:
            continue
        for item in parse_rss(bruto):
            titulo = item["titulo"]
            desc = item["descricao"]
            link = item["link"]
            if not titulo or not link or link in vistos:
                continue
            pub_dt = data_publicacao(item.get("pubDate") or "")
            if pub_dt is not None and pub_dt < corte:
                continue
            if not eh_compra_milhas(titulo, desc):
                continue
            prog = detectar_programa(f"{titulo} {desc}", programas)
            if not prog:
                continue
            vistos.add(link)
            bonus = extrair_bonus(f"{titulo} {desc}")
            avaliacao = avaliar_milhas.avaliar_promocao(
                programa=prog,
                titulo=titulo,
                descricao=desc,
                config=config,
                bonus_percentual=bonus,
            )
            saida.append(
                {
                    "id": f"MILHAS_{prog['id']}_{abs(hash(link)) % 10_000_000:07d}",
                    "timestamp": agora,
                    "programa": prog.get("nome") or prog["id"],
                    "tipo_promocao": tipo_de(titulo),
                    "descricao": titulo if len(titulo) <= 160 else titulo[:157] + "…",
                    "custo_por_milheiro": avaliacao["custo_por_milheiro"],
                    "bonus_percentual": bonus,
                    "bonus_transferencia_percentual": avaliacao["bonus_transferencia_percentual"],
                    "custo_efetivo_milheiro": avaliacao["custo_efetivo_milheiro"],
                    "classificacao": avaliacao["classificacao"],
                    "nota_avaliacao": avaliacao["nota_avaliacao"],
                    "desconto_percentual": bonus,
                    "score": avaliacao["score"],
                    "validade_promocao": validade_de(pub_dt),
                    "link": link,
                    "ativo": "sim",
                }
            )
    ordem_classe = {"Excelente": 0, "Regular": 1, "Ruim": 2}
    ordem = {p["id"]: int(p.get("prioridade") or 9) for p in programas.values()}

    def chave(linha: dict) -> tuple:
        pid = next((i for i, p in programas.items() if p.get("nome") == linha["programa"]), "zzz")
        return (
            ordem_classe.get(linha.get("classificacao") or "", 9),
            ordem.get(pid, 9),
            linha["programa"],
            linha["descricao"],
        )

    saida.sort(key=chave)
    return saida[:20]


def gravar(caminho: Path, linhas: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, lineterminator="\n")
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({c: linha.get(c, "") for c in COLUNAS})


def main() -> int:
    config = carregar_config()
    relativo = config.get("arquivo_promocoes") or "data/milhas_ativas.csv"
    destino = RAIZ / relativo
    linhas = coletar(config)
    gravar(destino, linhas)
    print(f"{len(linhas)} promoções ativas gravadas em {destino.relative_to(RAIZ)}.")
    for linha in linhas[:8]:
        print(f"- {linha['programa']}: {linha['descricao'][:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
