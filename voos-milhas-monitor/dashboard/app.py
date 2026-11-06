import html
import importlib
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import links

# O Streamlit reexecuta este arquivo e mantém o módulo antigo na memória.
# Sem o reload, o botão continua gerando o link que abre a busca vazia.
importlib.reload(links)
link_ida_volta = links.link_ida_volta

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Radar de Voos & Milhas",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
ORIGENS_BRASIL = {"GRU", "CGH", "VCP", "CNF"}

LUGARES = {
    "MAD": ("Madri", "Espanha", "🇪🇸", "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?auto=format&fit=crop&w=480&q=70"),
    "BCN": ("Barcelona", "Espanha", "🇪🇸", "https://images.unsplash.com/photo-1583422409516-2895a77efded?auto=format&fit=crop&w=480&q=70"),
    "FCO": ("Roma", "Itália", "🇮🇹", "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=480&q=70"),
    "MXP": ("Milão", "Itália", "🇮🇹", "https://images.unsplash.com/photo-1513581166391-887a96ddeafd?auto=format&fit=crop&w=480&q=70"),
    "LIS": ("Lisboa", "Portugal", "🇵🇹", "https://images.unsplash.com/photo-1585208798174-6cedd86e019a?auto=format&fit=crop&w=480&q=70"),
    "CDG": ("Paris", "França", "🇫🇷", "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=480&q=70"),
    "LON": ("Londres", "Reino Unido", "🇬🇧", "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=480&q=70"),
    "KEF": ("Reykjavík", "Islândia", "🇮🇸", "https://images.unsplash.com/photo-1476610182048-b716b8518aae?auto=format&fit=crop&w=480&q=70"),
    "MVD": ("Montevidéu", "Uruguai", "🇺🇾", "https://images.unsplash.com/photo-1589909202802-8f4aadce1849?auto=format&fit=crop&w=480&q=70"),
    "EZE": ("Buenos Aires", "Argentina", "🇦🇷", "https://images.unsplash.com/photo-1589909202802-8f4aadce1849?auto=format&fit=crop&w=480&q=70"),
    "JNB": ("Joanesburgo", "África do Sul", "🇿🇦", "https://images.unsplash.com/photo-1577948000111-9c970dfe3743?auto=format&fit=crop&w=480&q=70"),
    "CPT": ("Cidade do Cabo", "África do Sul", "🇿🇦", "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?auto=format&fit=crop&w=480&q=70"),
    "YUL": ("Montreal", "Canadá", "🇨🇦", "https://images.unsplash.com/photo-1519178614-68673b201f36?auto=format&fit=crop&w=480&q=70"),
    "YQB": ("Quebec", "Canadá", "🇨🇦", "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?auto=format&fit=crop&w=480&q=70"),
    "MCO": ("Orlando", "Estados Unidos", "🇺🇸", "https://images.unsplash.com/photo-1575089776834-8be34696ffb9?auto=format&fit=crop&w=480&q=70"),
}

# Uma página só: alertas de milhas no topo + passagens.


def css():
    st.markdown(
        """
        <style>
        #MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"] {display: none;}
        [data-testid="stMain"]::before,
        [data-testid="stMain"]:focus-visible::before {
            content: none !important;
            display: none !important;
            box-shadow: none !important;
        }
        [data-testid="stMain"]:focus,
        [data-testid="stMain"]:focus-visible {outline: none !important;}
        [data-testid="stAppViewContainer"] {background: #f5f7fb;}
        [data-testid="stAppViewContainer"] .main .block-container {
            padding: 22px 28px 48px 24px;
            max-width: 1180px;
        }
        /* Menu na lateral esquerda (sidebar nativa) */
        [data-testid="stSidebar"] {
            background: #fbfcfe !important;
            border-right: 1px solid #e8edf5;
            min-width: 248px !important;
        }
        [data-testid="stSidebar"] > div:first-child {padding: 18px 14px 24px;}
        [data-testid="stSidebar"] .marca {
            display: flex; gap: 10px; align-items: flex-start;
            margin: 2px 2px 18px; overflow: visible;
        }
        [data-testid="stSidebar"] .marca-icone {
            width: 34px; height: 34px; border-radius: 10px; flex: none;
            background: #2563eb; color: white; display: grid; place-items: center;
            font-size: 15px;
        }
        [data-testid="stSidebar"] .marca b {
            display: block; color: #1e3a5f;
            font-size: 12.5px; line-height: 1.35; font-weight: 700;
            white-space: normal; overflow: visible; word-break: normal;
        }
        [data-testid="stSidebar"] [role="radiogroup"] {
            display: flex; flex-direction: column; gap: 4px;
            background: transparent !important; border: 0 !important; padding: 0 !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            background: transparent !important; color: #475569 !important;
            border: 0 !important; border-radius: 10px !important;
            padding: 10px 12px !important;
            font-size: 13px !important; line-height: 1.35 !important;
            white-space: normal !important; overflow: visible !important;
            word-break: break-word !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: #e8eefc !important; color: #1d4ed8 !important; font-weight: 600 !important;
        }
        .hero {
            height: auto; min-height: 128px; border-radius: 18px; overflow: hidden; position: relative;
            background: #0f2744 url("https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=1600&q=70") center/cover;
            margin-bottom: 16px;
        }
        .hero .velo {
            position: absolute; inset: 0;
            background: linear-gradient(90deg, rgba(8,20,40,.45), rgba(8,20,40,.12) 72%);
        }
        .hero .texto {position: relative; padding: 26px 22px; color: white;}
        .hero h1 {
            margin: 0; font-size: 24px; letter-spacing: -0.3px;
            line-height: 1.25; white-space: normal; overflow: visible;
        }
        .hero p {margin: 6px 0 0; opacity: .92; font-size: 14px; line-height: 1.4;}
        .atualizar-ancora {display: none;}
        div.element-container:has(.atualizar-ancora) {display: none; height: 0; margin: 0;}
        div.element-container:has(.atualizar-ancora) + div.element-container {
            display: flex; justify-content: flex-end; align-self: stretch;
            width: 100% !important; margin-bottom: 12px;
        }
        div.element-container:has(.atualizar-ancora) + div.element-container .stButton {width: auto;}
        div.element-container:has(.atualizar-ancora) + div.element-container button {
            width: auto !important; min-height: 36px; padding: 6px 14px;
        }
        @media (max-width: 860px) {
            [data-testid="stAppViewContainer"] .main .block-container {padding: 16px 14px 36px;}
            .pills {overflow-x: auto; padding-bottom: 2px;}
            .secao {flex-direction: column; align-items: flex-start; gap: 4px;}
            .hero .texto {padding: 20px 16px;}
            .hero h1 {font-size: 20px;}
            .hero p {font-size: 13px;}
            [data-testid="stHorizontalBlock"] {flex-wrap: wrap;}
            [data-testid="column"] {width: 100% !important; flex: 1 1 100% !important;}
        }
        .pills {display: flex; gap: 8px; margin: 8px 0 18px; flex-wrap: nowrap;}
        .pills a {
            text-decoration: none; background: white; color: #334155;
            border-radius: 999px; padding: 8px 14px; font-size: 14px;
            border: 1px solid #e6ebf2; white-space: nowrap;
        }
        .pills a.ativo {background: #1d4ed8; color: white; border-color: #1d4ed8;}
        .secao {display: flex; justify-content: space-between; align-items: center; margin: 8px 0 12px;}
        .secao h2 {margin: 0; color: #1e293b; font-size: 22px;}
        .secao a {color: #2563eb; text-decoration: none; font-size: 14px;}
        .cartao {
            background: white; border-radius: 16px; overflow: hidden;
            border: 1px solid #e8edf5; display: flex; align-items: stretch;
            min-height: 156px; height: 100%;
            box-shadow: 0 8px 20px rgba(15,23,42,.04);
        }
        .cartao .foto {width: 124px; flex: 0 0 124px; background-size: cover; background-position: center;}
        .cartao .miolo {padding: 14px 14px 12px; flex: 1; min-width: 0; display: flex; flex-direction: column;}
        .cartao .topo {display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;}
        .cartao h3 {margin: 0; font-size: 17px; line-height: 1.2; color: #0f172a;}
        .cartao .pais {color: #64748b; font-weight: 500; font-size: 13px; margin-top: 2px;}
        .badge {
            flex: none; align-self: flex-start; line-height: 1.2; white-space: nowrap;
            background: #e8f8ef; color: #15803d; border-radius: 999px;
            padding: 4px 8px; font-size: 12px; font-weight: 700;
        }
        .cartao .rota {color: #334155; font-size: 13px; font-weight: 600; margin-top: 10px;}
        .cartao .datas {color: #64748b; font-size: 12px; margin-top: 1px;}
        .cartao .base {display: flex; justify-content: space-between; align-items: flex-end; gap: 8px; margin-top: auto; padding-top: 10px;}
        .cartao .preco-linha {display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap;}
        .cartao .preco {font-size: 20px; font-weight: 750; color: #0f172a; letter-spacing: -0.3px;}
        .cartao .media {color: #94a3b8; font-size: 12px; font-weight: 500;}
        .cartao .media s {text-decoration: line-through;}
        .cartao .it {color: #64748b; font-size: 12px; margin-top: 2px;}
        .link-voo {
            display: inline-block; color: #475569; background: #f8fafc;
            border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 5px 12px; font-size: 13px; font-weight: 600;
            text-decoration: none; white-space: nowrap; line-height: 1.2;
        }
        .link-voo:hover { background: #f1f5f9; color: #1e293b; }
        .stButton > button {
            background: #f8fafc; color: #334155; border: 1px solid #e2e8f0;
            border-radius: 8px; font-weight: 600;
        }
        .stButton > button:hover { background: #f1f5f9; color: #1e293b; border-color: #cbd5e1; }
        .tabela {width: 100%; border-collapse: collapse; background: white; border-radius: 14px; overflow: hidden;}
        .tabela th {text-align: left; color: #64748b; font-weight: 600; font-size: 13px; padding: 12px; background: #f8fafc;}
        .tabela td {padding: 12px; border-top: 1px solid #eef2f7; color: #1e293b; font-size: 14px;}
        .eco {background: #e8f8ef; color: #15803d; border-radius: 999px; padding: 3px 8px; font-weight: 700; font-size: 13px;}
        .score {background: #e8f8ef; color: #166534; border-radius: 999px; padding: 3px 8px; font-weight: 700; font-size: 13px;}
        .alertas-milhas {display: flex; flex-direction: column; gap: 8px; margin: 0 0 14px;}
        .balao-milhas {
            display: flex; align-items: flex-start; gap: 12px;
            background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;
            padding: 12px 14px 12px 12px;
        }
        .balao-milhas.excelente {background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border-color: #bbf7d0;}
        .balao-milhas.regular {background: linear-gradient(135deg, #fffbeb 0%, #f8fafc 100%); border-color: #fde68a;}
        .balao-milhas.ruim {background: linear-gradient(135deg, #fef2f2 0%, #f8fafc 100%); border-color: #fecaca;}
        .balao-milhas .icone {
            flex: none; width: 34px; height: 34px; border-radius: 10px;
            background: #64748b; color: white; display: grid; place-items: center;
            font-size: 16px; font-weight: 700;
        }
        .balao-milhas.excelente .icone {background: #059669;}
        .balao-milhas.regular .icone {background: #d97706;}
        .balao-milhas.ruim .icone {background: #dc2626;}
        .balao-milhas .corpo {flex: 1; min-width: 0;}
        .balao-milhas .topo-tags {display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 4px;}
        .balao-milhas .rotulo, .balao-milhas .selo {
            display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .04em;
            text-transform: uppercase; border-radius: 999px; padding: 2px 8px;
        }
        .balao-milhas .rotulo {color: #475569; background: #e2e8f0;}
        .balao-milhas .selo.excelente {color: #047857; background: #d1fae5;}
        .balao-milhas .selo.regular {color: #b45309; background: #fef3c7;}
        .balao-milhas .selo.ruim {color: #b91c1c; background: #fee2e2;}
        .balao-milhas .titulo {margin: 0; color: #0f172a; font-size: 14px; font-weight: 700; line-height: 1.3;}
        .balao-milhas .texto {margin: 2px 0 0; color: #334155; font-size: 13px; line-height: 1.35;}
        .balao-milhas .milheiro {
            margin: 8px 0 0; padding: 8px 10px; border-radius: 10px;
            background: rgba(15,23,42,.04); color: #0f172a; font-size: 12px; line-height: 1.35;
        }
        .balao-milhas .milheiro strong {display: block; font-size: 13px; margin-bottom: 2px;}
        .balao-milhas .nota {margin: 6px 0 0; color: #475569; font-size: 12px; line-height: 1.35;}
        .balao-milhas .meta {margin: 4px 0 0; color: #64748b; font-size: 12px;}
        .balao-milhas a.ver {
            flex: none; align-self: center; text-decoration: none; white-space: nowrap;
            background: #0f172a; color: white; border-radius: 8px;
            padding: 7px 12px; font-size: 12px; font-weight: 650;
        }
        .balao-milhas a.ver:hover {background: #1e293b;}
        @media (max-width: 860px) {
            .balao-milhas {flex-wrap: wrap;}
            .balao-milhas a.ver {width: 100%; text-align: center;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def obter_data_dir():
    aqui = os.path.dirname(__file__)
    for caminho in (
        os.environ.get("CSV_DATA_DIR", ""),
        os.path.join(aqui, "..", "data"),
        "./data",
        "../data",
    ):
        if caminho and os.path.isdir(caminho):
            return caminho
    os.makedirs("./data", exist_ok=True)
    return "./data"


def texto(valor, padrao=""):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return padrao
    saida = str(valor).strip()
    return padrao if saida.lower() == "nan" else saida


def lugar(codigo):
    codigo = texto(codigo).upper()
    if codigo in LUGARES:
        return LUGARES[codigo]
    return (codigo, "", "✈️", "")


def reais(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "—"
    inteiro = abs(numero - round(numero)) < 0.005
    bruto = f"{numero:,.0f}" if inteiro else f"{numero:,.2f}"
    return "R$ " + bruto.replace(",", "X").replace(".", ",").replace("X", ".")


def data_curta(valor):
    bruto = texto(valor)[:10]
    try:
        dia = datetime.strptime(bruto, "%Y-%m-%d")
    except ValueError:
        return bruto
    return f"{dia.day} {MESES[dia.month - 1]}"


def periodo(ida, volta):
    ida_txt, volta_txt = texto(ida)[:10], texto(volta)[:10]
    try:
        a = datetime.strptime(ida_txt, "%Y-%m-%d")
        b = datetime.strptime(volta_txt, "%Y-%m-%d")
    except ValueError:
        return ida_txt
    if a.year == b.year:
        return f"{a.day} {MESES[a.month - 1]} – {b.day} {MESES[b.month - 1]} {a.year}"
    return f"{data_curta(ida_txt)} {a.year} – {data_curta(volta_txt)} {b.year}"


def itinerario(voo):
    tipo = texto(voo.get("tipo_voo_ida"), "—")
    duracao = texto(voo.get("duracao_total_ida"))
    partes = [tipo]
    if duracao:
        partes.append(duracao)
    ida = texto(voo.get("conexoes_ida"))
    volta = texto(voo.get("conexoes_volta"))
    if volta not in {"", "0", ida}:
        partes.append(f"{volta} na volta")
    mudanca = texto(voo.get("mudanca_aeroporto")).lower()
    if mudanca == "sim":
        aeroportos = texto(voo.get("aeroportos_conexao"))
        partes.append("troca de aeroporto" + (f" {aeroportos}" if aeroportos else ""))
    return " · ".join(partes)


def ler_config():
    caminho = os.path.join(os.path.dirname(__file__), "..", "config-rotina.json")
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def limites_estadia():
    janela = ler_config().get("janela", {})
    return int(janela.get("estadia_dias_min", 7)), int(janela.get("estadia_dias_max", 15))


def desconto_minimo():
    config = ler_config()
    alerta = config.get("alerta") or {}
    if "desconto_minimo_percentual" in alerta:
        return float(alerta["desconto_minimo_percentual"])
    return float(config.get("desconto_minimo_percentual", 25))


@st.cache_data(ttl=300)
def carregar_dados(data_dir):
    voos = pd.DataFrame()
    milhas = pd.DataFrame()
    stats = {}
    voos_path = os.path.join(data_dir, "voos_ativos.csv")
    if os.path.exists(voos_path):
        voos = pd.read_csv(voos_path)
        for coluna in ("conexoes_ida", "conexoes_volta", "mudanca_aeroporto", "aeroportos_conexao"):
            if coluna not in voos.columns:
                voos[coluna] = ""
        voos["preco_por_pessoa"] = pd.to_numeric(voos["preco_por_pessoa"], errors="coerce")
        voos["preco_referencia"] = pd.to_numeric(voos.get("preco_referencia"), errors="coerce")
        voos["desconto_percentual"] = pd.to_numeric(voos["desconto_percentual"], errors="coerce")
        voos["score"] = pd.to_numeric(voos["score"], errors="coerce")
        voos = voos[voos["origem"].isin(ORIGENS_BRASIL)].copy()
        minimo, maximo = limites_estadia()
        ida = pd.to_datetime(voos["data_ida"], errors="coerce")
        volta = pd.to_datetime(voos["data_volta"], errors="coerce")
        dias = (volta - ida).dt.days
        voos = voos[dias.between(minimo, maximo)].copy()
        referencia = voos["preco_referencia"]
        preco = voos["preco_por_pessoa"]
        voos["desconto_percentual"] = (referencia - preco) / referencia.replace(0, pd.NA) * 100
        # Sem média acima do preço, o valor exibido é o do link. Com média, só fica o desconto de pelo menos 25%.
        tem_media = referencia.notna() & preco.notna() & (referencia > preco)
        voos = voos[~tem_media | (voos["desconto_percentual"] >= desconto_minimo())].copy()
    milhas_path = os.path.join(data_dir, "milhas_ativas.csv")
    if os.path.exists(milhas_path):
        milhas = pd.read_csv(milhas_path)
    stats_path = os.path.join(data_dir, "estatisticas.json")
    if os.path.exists(stats_path):
        with open(stats_path, encoding="utf-8") as arquivo:
            stats = json.load(arquivo)
    return voos, milhas, stats


PAGINAS = [
    ("passagens", "Passagens"),
    ("milhas", "Compra de milhas"),
]
PAGINA_ROTULOS = {chave: rotulo for chave, rotulo in PAGINAS}
PAGINA_CHAVES = {rotulo: chave for chave, rotulo in PAGINAS}


def pagina_atual() -> str:
    # Navegação interna (sem <a href>), para não abrir outro link a cada clique.
    if "pagina" not in st.session_state:
        st.session_state.pagina = "passagens"
    atual = st.session_state.pagina
    return atual if atual in PAGINA_ROTULOS else "passagens"


def nav(ativa: str) -> str:
    """Menu na lateral esquerda, sem abrir outro link a cada clique."""
    with st.sidebar:
        st.markdown(
            """
            <div class="marca">
              <div class="marca-icone">✈</div>
              <div><b>Radar de<br>Voos &amp; Milhas</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        rotulos = [rotulo for _, rotulo in PAGINAS]
        indice = next((i for i, (chave, _) in enumerate(PAGINAS) if chave == ativa), 0)
        escolha = st.radio(
            "Navegação",
            rotulos,
            index=indice,
            label_visibility="collapsed",
            key="nav_pagina_radio",
        )
    chave = PAGINA_CHAVES.get(escolha, "passagens")
    if chave != st.session_state.get("pagina"):
        st.session_state.pagina = chave
    return chave


def caminho_script_milhas() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "buscar_promocoes_milhas.py"))


def atualizar_promocoes_milhas() -> tuple[bool, str]:
    script = caminho_script_milhas()
    if not os.path.exists(script):
        return False, "Script de milhas não encontrado."
    import subprocess

    try:
        proc = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=90,
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        )
    except subprocess.TimeoutExpired:
        return False, "A busca de promoções de milhas demorou demais."
    if proc.returncode != 0:
        detalhe = (proc.stderr or proc.stdout or "erro desconhecido").strip()
        return False, f"Falha ao buscar milhas: {detalhe[:240]}"
    linha = (proc.stdout or "").strip().splitlines()
    return True, (linha[0] if linha else "Promoções de milhas atualizadas.")


def atualizar_dados():
    st.markdown('<div class="atualizar-ancora"></div>', unsafe_allow_html=True)
    if st.button("Atualizar dados"):
        ok, mensagem = atualizar_promocoes_milhas()
        if ok:
            st.toast(mensagem)
        else:
            st.warning(mensagem)
        st.cache_data.clear()
        st.rerun()


def hero():
    st.markdown(
        """
        <div class="hero"><div class="velo"></div><div class="texto">
          <h1>Radar de Voos & Milhas</h1>
          <p>As melhores oportunidades de viagem, em um só lugar.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )


def promocao_ativa(linha) -> bool:
    ativo = texto(linha.get("ativo"), "sim").lower()
    if ativo in {"nao", "não", "false", "0", "off", "inativo"}:
        return False
    validade = texto(linha.get("validade_promocao"))[:10]
    if not validade:
        return True
    try:
        return datetime.strptime(validade, "%Y-%m-%d").date() >= datetime.now().date()
    except ValueError:
        return True


def _classe_css(classificacao: str) -> str:
    mapa = {"Excelente": "excelente", "Regular": "regular", "Ruim": "ruim"}
    return mapa.get(classificacao, "regular")


def promocoes_ativas(tabela) -> list:
    if tabela is None or getattr(tabela, "empty", True):
        return []
    ativas = [linha for _, linha in tabela.iterrows() if promocao_ativa(linha)]
    ordem = {"Excelente": 0, "Regular": 1, "Ruim": 2}
    ativas.sort(key=lambda item: ordem.get(texto(item.get("classificacao"), "Regular"), 9))
    return ativas


def montar_balao_milhas(item) -> str:
    programa = html.escape(texto(item.get("programa"), "Programa"))
    tipo = html.escape(texto(item.get("tipo_promocao")))
    descricao = html.escape(texto(item.get("descricao"), "Promoção ativa de milhas."))
    classificacao = texto(item.get("classificacao"), "Regular")
    classe = _classe_css(classificacao)
    nota = html.escape(texto(item.get("nota_avaliacao")))
    custo_base = texto(item.get("custo_por_milheiro"))
    custo_efetivo = texto(item.get("custo_efetivo_milheiro"))
    bonus_t = texto(item.get("bonus_transferencia_percentual"))
    validade = texto(item.get("validade_promocao"))[:10]
    meta = f"Válida até {data_curta(validade)}" if validade else "Promoção em andamento"
    link = texto(item.get("link"))
    botao = (
        f'<a class="ver" href="{html.escape(link)}" target="_blank" rel="noopener">Ver oferta</a>'
        if link.startswith("http")
        else ""
    )
    titulo = programa if not tipo else f"{programa} · {tipo}"
    if custo_efetivo:
        bonus_txt = f" (com {bonus_t}% de bônus de transferência)" if bonus_t else ""
        milheiro_html = (
            "<div class='milheiro'>"
            "<strong>Custo efetivo do milheiro após bônus de transferência: "
            f"R$ {html.escape(custo_efetivo.replace('.', ','))}</strong>"
            + (
                f"Base da promoção: R$ {html.escape(custo_base.replace('.', ','))}{html.escape(bonus_txt)}."
                if custo_base
                else ""
            )
            + "</div>"
        )
    elif custo_base:
        milheiro_html = (
            "<div class='milheiro'>"
            f"<strong>Milheiro da promoção: R$ {html.escape(custo_base.replace('.', ','))}</strong>"
            "Sem bônus de transferência informado para recalcular o efetivo."
            "</div>"
        )
    else:
        milheiro_html = (
            "<div class='milheiro'>"
            "<strong>Custo efetivo do milheiro após bônus de transferência:</strong>"
            "Não informado na oferta — depende do bônus vigente na transferência."
            "</div>"
        )
    nota_html = f"<p class='nota'>{nota}</p>" if nota else ""
    # Sem indentação: o Markdown do Streamlit trata linhas indentadas como código cru.
    return (
        f"<div class='balao-milhas {classe}'>"
        "<div class='icone'>★</div>"
        "<div class='corpo'>"
        "<div class='topo-tags'>"
        "<span class='rotulo'>Promoção de milhas</span>"
        f"<span class='selo {classe}'>{html.escape(classificacao)}</span>"
        "</div>"
        f"<p class='titulo'>{titulo}</p>"
        f"<p class='texto'>{descricao}</p>"
        f"{milheiro_html}"
        f"{nota_html}"
        f"<p class='meta'>{html.escape(meta)}</p>"
        "</div>"
        f"{botao}"
        "</div>"
    )


def pagina_milhas(tabela):
    st.markdown(
        '<div class="secao"><h2>Compra de milhas</h2></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Excelente: milheiro competitivo. Regular: depende de bônus/destino/emissão. "
        "Ruim: custo elevado na compra isolada — às vezes útil só com transferência bonificada."
    )
    ativas = promocoes_ativas(tabela)
    if not ativas:
        st.info("Nenhuma promoção de compra de milhas ativa no momento. Toque em Atualizar dados.")
        return

    programas = ["Todos"] + sorted({texto(item.get("programa")) for item in ativas if texto(item.get("programa"))})
    classes = ["Todas", "Excelente", "Regular", "Ruim"]
    c1, c2 = st.columns(2)
    filtro_prog = c1.selectbox("Programa", programas)
    filtro_classe = c2.selectbox("Avaliação", classes)

    filtradas = ativas
    if filtro_prog != "Todos":
        filtradas = [item for item in filtradas if texto(item.get("programa")) == filtro_prog]
    if filtro_classe != "Todas":
        filtradas = [
            item for item in filtradas if texto(item.get("classificacao"), "Regular") == filtro_classe
        ]

    if not filtradas:
        st.info("Nenhuma promoção com esses filtros.")
        return

    st.markdown(
        "<div class='alertas-milhas'>"
        + "".join(montar_balao_milhas(item) for item in filtradas)
        + "</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"{len(filtradas)} oportunidade(s) de compra de milhas.")


def desconto_visto(voo):
    desconto = voo.get("desconto_percentual")
    referencia = voo.get("preco_referencia")
    preco = voo.get("preco_por_pessoa")
    if pd.isna(desconto) or pd.isna(referencia) or pd.isna(preco):
        return None
    if float(referencia) <= float(preco) or float(desconto) < desconto_minimo():
        return None
    return float(desconto)


def cartao(voo):
    cidade, pais, _, foto = lugar(voo.get("destino"))
    if not foto:
        foto = "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=480&q=70"
    desconto = desconto_visto(voo)
    badge = f'<span class="badge">{desconto:.0f}%</span>' if desconto is not None else ""
    referencia = voo.get("preco_referencia")
    preco = voo.get("preco_por_pessoa")
    antes = ""
    if pd.notna(referencia) and pd.notna(preco) and float(referencia) > float(preco):
        antes = f'<span class="media">média <s>{reais(referencia)}</s></span>'
    link = link_ida_volta(
        texto(voo.get("origem")),
        texto(voo.get("destino")),
        texto(voo.get("data_ida"))[:10],
        texto(voo.get("data_volta"))[:10],
    )
    pais_html = f'<div class="pais">{html.escape(pais)}</div>' if pais else ""
    return f"""
    <div class="cartao">
      <div class="foto" style="background-image:url('{html.escape(foto, quote=True)}')"></div>
      <div class="miolo">
        <div class="topo">
          <div>
            <h3>{html.escape(cidade)}</h3>
            {pais_html}
          </div>{badge}
        </div>
        <div class="rota">{html.escape(texto(voo.get("origem")))} → {html.escape(texto(voo.get("destino")))}</div>
        <div class="datas">{html.escape(periodo(voo.get("data_ida"), voo.get("data_volta")))} · ida e volta</div>
        <div class="base">
          <div>
            <div class="preco-linha"><span class="preco">{reais(preco)}</span>{antes}</div>
            <div class="it">{html.escape(itinerario(voo))}</div>
          </div>
          <a class="link-voo" href="{html.escape(link, quote=True)}" target="_blank" rel="noopener">Link</a>
        </div>
      </div>
    </div>
    """


def passagens(voos):
    st.markdown(
        '<div class="secao"><h2>Destaques da Semana</h2><a href="#todas">Ver todas as oportunidades →</a></div>',
        unsafe_allow_html=True,
    )
    if voos.empty:
        st.info(
            f"Nenhuma passagem de ida e volta está pelo menos {desconto_minimo():.0f}% abaixo da média."
        )
        return
    destaques = voos.sort_values(["desconto_percentual", "score"], ascending=False).head(3)
    colunas = st.columns(3)
    for coluna, (_, voo) in zip(colunas, destaques.iterrows()):
        coluna.markdown(cartao(voo), unsafe_allow_html=True)

    st.markdown('<div id="todas" class="secao"><h2>Outras oportunidades</h2></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    origens = ["Todos"] + sorted(voos["origem"].dropna().unique().tolist())
    destinos = ["Todos"] + sorted(voos["destino"].dropna().unique().tolist())
    periodos = ["Todos"] + sorted({periodo(a, b) for a, b in zip(voos["data_ida"], voos["data_volta"])})
    origem = c1.selectbox("Origem", origens)
    destino = c2.selectbox("Destino", destinos)
    janela = c3.selectbox("Período", periodos)
    with st.expander("Mais filtros"):
        f1, f2, f3 = st.columns(3)
        preco_max = f1.number_input("Preço máximo", min_value=0, value=10000, step=500)
        tipos = ["Todos", "Direto", "1 conexão", "2+ conexões"]
        tipo = f2.selectbox("Itinerário", tipos)
        mudanca = f3.selectbox("Mudança de aeroporto", ["Todas", "Sim", "Não", "não informado"])

    filtrados = voos.copy()
    if origem != "Todos":
        filtrados = filtrados[filtrados["origem"] == origem]
    if destino != "Todos":
        filtrados = filtrados[filtrados["destino"] == destino]
    if janela != "Todos":
        filtrados = filtrados[filtrados.apply(lambda v: periodo(v["data_ida"], v["data_volta"]) == janela, axis=1)]
    filtrados = filtrados[filtrados["preco_por_pessoa"] <= preco_max]
    if tipo != "Todos":
        filtrados = filtrados[filtrados["tipo_voo_ida"] == tipo]
    if mudanca != "Todas":
        filtrados = filtrados[filtrados["mudanca_aeroporto"].fillna("").astype(str) == mudanca]

    linhas = []
    for _, voo in filtrados.sort_values(["desconto_percentual", "score"], ascending=False).iterrows():
        cidade, _, _, _ = lugar(voo.get("destino"))
        desconto = desconto_visto(voo)
        eco = f"{desconto:.0f}%" if desconto is not None else "—"
        score = f"{voo['score']:.0f}/100" if pd.notna(voo.get("score")) else "—"
        link = link_ida_volta(
            texto(voo.get("origem")),
            texto(voo.get("destino")),
            texto(voo.get("data_ida"))[:10],
            texto(voo.get("data_volta"))[:10],
        )
        seta = (
            f'<a class="link-voo" href="{html.escape(link, quote=True)}" target="_blank" rel="noopener">Link</a>'
            if link
            else "—"
        )
        linhas.append(
            "<tr>"
            f"<td>{html.escape(cidade)}</td>"
            f"<td>{texto(voo.get('origem'))} → {texto(voo.get('destino'))}</td>"
            f"<td>{periodo(voo.get('data_ida'), voo.get('data_volta'))} · ida e volta</td>"
            f"<td>✈ {itinerario(voo)}</td>"
            f"<td><b>{reais(voo.get('preco_por_pessoa'))}</b></td>"
            f"<td><span class='eco'>{eco}</span></td>"
            f"<td><span class='score'>{score}</span></td>"
            f"<td>{seta}</td>"
            "</tr>"
        )
    st.markdown(
        """
        <table class="tabela">
          <thead><tr>
            <th>Destino</th><th>Rota</th><th>Datas</th><th>Itinerário</th>
            <th>Preço (por pessoa)</th><th>Economia</th><th>Score</th><th></th>
          </tr></thead>
          <tbody>
        """
        + "".join(linhas)
        + "</tbody></table>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"{len(filtrados)} passagens de ida e volta, com estadia de 7 a 15 dias. "
        "O preço é o menor valor por pessoa no link. O percentual aparece quando ele fica pelo menos "
        f"{desconto_minimo():.0f}% abaixo do preço normal."
    )


def milhas_desatualizadas(data_dir: str) -> bool:
    caminho = os.path.join(data_dir, "milhas_ativas.csv")
    if not os.path.exists(caminho) or os.path.getsize(caminho) < 40:
        return True
    idade_h = (datetime.now().timestamp() - os.path.getmtime(caminho)) / 3600
    return idade_h >= 6


def main():
    css()
    ativa = pagina_atual()
    ativa = nav(ativa)
    atualizar_dados()
    data_dir = obter_data_dir()
    # Na primeira carga (ou CSV velho), busca promoções automaticamente uma vez por sessão.
    if milhas_desatualizadas(data_dir) and not st.session_state.get("milhas_buscadas"):
        st.session_state["milhas_buscadas"] = True
        atualizar_promocoes_milhas()
        st.cache_data.clear()
    voos, tabela_milhas, _ = carregar_dados(data_dir)
    if ativa == "milhas":
        pagina_milhas(tabela_milhas)
        return
    hero()
    passagens(voos)


main()
