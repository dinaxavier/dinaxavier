import html
import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Radar de Voos & Milhas",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
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

ICONES = {
    "aviao": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4 20-7z"/></svg>',
    "estrela": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 3 14.9 8.8 21 9.6 16.5 14 17.7 20.2 12 17.2 6.3 20.2 7.5 14 3 9.6 9.1 8.8"/></svg>',
    "desconto": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="7.5" cy="7.5" r="2.1"/><circle cx="16.5" cy="16.5" r="2.1"/></svg>',
    "milheiro": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><path d="M12 8v8M9.2 10.2h5.2a1.7 1.7 0 0 1 0 3.4h-4.4a1.7 1.7 0 0 0 0 3.4h5.2"/></svg>',
    "calendario": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M8 3.5v3M16 3.5v3M3.5 10h17"/></svg>',
}

PAGINAS = [
    ("inicio", "Início"),
    ("passagens", "Passagens Aéreas"),
    ("milhas", "Promoções de Milhas"),
    ("combinadas", "Oportunidades Combinadas"),
    ("historico", "Histórico e Tendências"),
    ("config", "Configurações"),
]


def css():
    st.markdown(
        """
        <style>
        #MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"] {display: none;}
        [data-testid="stAppViewContainer"] {background: #f5f7fb; margin-left: 228px;}
        [data-testid="stAppViewContainer"] .main .block-container {
            padding: 22px 28px 48px 24px;
            max-width: 1180px;
        }
        .nav-fixa {
            position: fixed; left: 0; top: 0; bottom: 0; width: 228px;
            background: #fbfcfe; border-right: 1px solid #e8edf5;
            padding: 22px 14px; z-index: 100;
        }
        .marca {display: flex; gap: 10px; align-items: center; margin: 4px 8px 22px;}
        .marca-icone {
            width: 36px; height: 36px; border-radius: 10px;
            background: #2563eb; color: white; display: grid; place-items: center;
            font-size: 18px;
        }
        .marca b {display: block; color: #1e3a5f; font-size: 14px; line-height: 1.15;}
        .marca span {color: #64748b; font-size: 12px;}
        .nav-fixa a {
            display: block; text-decoration: none; color: #475569;
            padding: 10px 12px; border-radius: 10px; margin-bottom: 4px; font-size: 14px;
        }
        .nav-fixa a.ativo {background: #e8eefc; color: #1d4ed8; font-weight: 600;}
        .hero {
            height: 148px; border-radius: 18px; overflow: hidden; position: relative;
            background: #0f2744 url("https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=1600&q=70") center/cover;
            margin-bottom: 16px;
        }
        .hero .velo {
            position: absolute; inset: 0;
            background: linear-gradient(90deg, rgba(8,20,40,.45), rgba(8,20,40,.12) 72%);
        }
        .hero .texto {position: relative; padding: 36px 32px; color: white;}
        .hero h1 {margin: 0; font-size: 32px; letter-spacing: -0.4px;}
        .hero p {margin: 4px 0 0; opacity: .92;}
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
        .metricas {
            display: grid; grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 12px; margin-bottom: 16px;
        }
        .metrica {
            background: white; border-radius: 16px; padding: 16px 14px;
            box-shadow: 0 1px 2px rgba(15,23,42,.04); border: 1px solid #e8edf5;
            display: flex; gap: 12px; align-items: center; min-height: 88px; min-width: 0;
        }
        .metrica .ico {
            width: 40px; height: 40px; border-radius: 12px; flex: 0 0 40px;
            background: #f3f6fb; color: #1e3a5f;
            display: grid; place-items: center; position: relative;
        }
        .metrica .ico svg {width: 20px; height: 20px; display: block;}
        .metrica .txt {min-width: 0;}
        .metrica b {
            display: block; color: #0f172a; font-size: 22px; line-height: 1.1;
            letter-spacing: -0.3px; font-variant-numeric: tabular-nums; white-space: nowrap;
        }
        .metrica.quando b {font-size: 16px; letter-spacing: -0.2px;}
        .metrica span {display: block; margin-top: 3px; color: #64748b; font-size: 12.5px; line-height: 1.3;}
        @media (max-width: 1100px) {
            .metricas {grid-template-columns: repeat(3, minmax(0, 1fr));}
        }
        @media (max-width: 860px) {
            [data-testid="stAppViewContainer"] {margin-left: 0;}
            [data-testid="stAppViewContainer"] .main .block-container {padding: 68px 14px 36px;}
            .nav-fixa {
                left: 0; right: 0; top: 0; bottom: auto; width: auto; height: auto;
                display: flex; gap: 4px; overflow-x: auto; padding: 8px 10px;
                border-right: 0; border-bottom: 1px solid #e8edf5;
            }
            .marca {display: none;}
            .nav-fixa a {white-space: nowrap; margin: 0; flex: none; padding: 8px 12px;}
            .metricas {grid-template-columns: 1fr 1fr;}
            .metrica.quando {grid-column: 1 / -1;}
            .pills {overflow-x: auto; padding-bottom: 2px;}
            .secao {flex-direction: column; align-items: flex-start; gap: 4px;}
            .hero {height: auto; min-height: 148px;}
            .hero h1 {font-size: 26px;}
            .hero .texto {padding: 24px 18px 22px;}
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
        .cartao .antes {color: #94a3b8; text-decoration: line-through; font-size: 12px; font-weight: 500;}
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


def pagina_atual():
    valor = st.query_params.get("pagina", "inicio")
    if isinstance(valor, list):
        valor = valor[0] if valor else "inicio"
    return valor if valor in {item[0] for item in PAGINAS} else "inicio"


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
    milhas_path = os.path.join(data_dir, "milhas_ativas.csv")
    if os.path.exists(milhas_path):
        milhas = pd.read_csv(milhas_path)
    stats_path = os.path.join(data_dir, "estatisticas.json")
    if os.path.exists(stats_path):
        with open(stats_path, encoding="utf-8") as arquivo:
            stats = json.load(arquivo)
    return voos, milhas, stats


def nav(ativa):
    itens = []
    for chave, rotulo in PAGINAS:
        classe = "ativo" if chave == ativa or (ativa == "inicio" and chave == "passagens") else ""
        if chave == "passagens" and ativa == "inicio":
            classe = "ativo"
        itens.append(f'<a class="{classe}" href="?pagina={chave}">{rotulo}</a>')
    st.markdown(
        f"""
        <div class="nav-fixa">
          <div class="marca">
            <div class="marca-icone">✈</div>
            <div><b>Radar de<br>Voos & Milhas</b></div>
          </div>
          {''.join(itens)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def atualizar_dados():
    st.markdown('<div class="atualizar-ancora"></div>', unsafe_allow_html=True)
    if st.button("Atualizar dados"):
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


def quando_curto(valor):
    bruto = texto(valor)
    if not bruto:
        return "—"
    try:
        momento = datetime.fromisoformat(bruto.replace("Z", "+00:00"))
    except ValueError:
        return bruto[:16]
    return momento.strftime("%d/%m · %H:%M")


def metrica(icone, valor, rotulo, extra=""):
    return (
        f'<div class="metrica {extra}">'
        f'<span class="ico">{ICONES[icone]}</span>'
        f'<div class="txt"><b>{valor}</b><span>{rotulo}</span></div>'
        f"</div>"
    )


def metricas(voos, stats):
    total = len(voos)
    novas = stats.get("novas_semana", total)
    maior = stats.get("maior_desconto", 0)
    milheiro = stats.get("melhor_custo_milheiro") or 0
    milheiro_txt = reais(milheiro / 100) if milheiro > 20 else reais(milheiro)
    cards = [
        metrica("aviao", total, "oportunidades ativas"),
        metrica("estrela", novas, "novas na semana"),
        metrica("desconto", f"{abs(float(maior)):.0f}%", "maior desconto"),
        metrica("milheiro", milheiro_txt, "melhor custo por milheiro"),
        metrica("calendario", quando_curto(stats.get("ultima_atualizacao")), "última atualização", "quando"),
    ]
    st.markdown(f'<div class="metricas">{"".join(cards)}</div>', unsafe_allow_html=True)


def pills(ativa):
    mapa = [("passagens", "Passagens Aéreas"), ("milhas", "Promoções de Milhas"), ("combinadas", "Oportunidades Combinadas")]
    atual = "passagens" if ativa == "inicio" else ativa
    html = []
    for chave, rotulo in mapa:
        classe = "ativo" if chave == atual else ""
        html.append(f'<a class="{classe}" href="?pagina={chave}">{rotulo}</a>')
    st.markdown(f'<div class="pills">{"".join(html)}</div>', unsafe_allow_html=True)


def cartao(voo):
    cidade, pais, _, foto = lugar(voo.get("destino"))
    if not foto:
        foto = "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=480&q=70"
    desconto = voo.get("desconto_percentual")
    badge = f'<span class="badge">{desconto:.0f}%</span>' if pd.notna(desconto) else ""
    referencia = voo.get("preco_referencia")
    preco = voo.get("preco_por_pessoa")
    antes = ""
    if pd.notna(referencia) and pd.notna(preco) and abs(float(referencia) - float(preco)) > 1:
        antes = f'<span class="antes">{reais(referencia)}</span>'
    link = texto(voo.get("link"), "#")
    pais_html = f'<div class="pais">{html.escape(pais)}</div>' if pais else ""
    return f"""
    <div class="cartao">
      <div class="foto" style="background-image:url('{html.escape(foto, quote=True)}')"></div>
      <div class="miolo">
        <div class="topo">
          <div>
            <h3>{html.escape(cidade)}</h3>
            {pais_html}
          </div>
          {badge}
        </div>
        <div class="rota">{html.escape(texto(voo.get("origem")))} → {html.escape(texto(voo.get("destino")))}</div>
        <div class="datas">{html.escape(periodo(voo.get("data_ida"), voo.get("data_volta")))}</div>
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
        st.info("Aguardando a primeira rodada com preços vistos nas páginas de busca.")
        return
    destaques = voos.sort_values("score", ascending=False).head(3)
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
    for _, voo in filtrados.sort_values("score", ascending=False).iterrows():
        cidade, _, _, _ = lugar(voo.get("destino"))
        desconto = voo.get("desconto_percentual")
        eco = f"{desconto:.0f}%" if pd.notna(desconto) else "—"
        score = f"{voo['score']:.0f}/100" if pd.notna(voo.get("score")) else "—"
        link = texto(voo.get("link"))
        seta = (
            f'<a class="link-voo" href="{html.escape(link, quote=True)}" target="_blank" rel="noopener">Link</a>'
            if link
            else "—"
        )
        linhas.append(
            "<tr>"
            f"<td>{html.escape(cidade)}</td>"
            f"<td>{texto(voo.get('origem'))} → {texto(voo.get('destino'))}</td>"
            f"<td>{periodo(voo.get('data_ida'), voo.get('data_volta'))}</td>"
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
    st.caption(f"{len(filtrados)} oportunidades. Saída sempre de um aeroporto no Brasil.")


def milhas(tabela):
    st.markdown('<div class="secao"><h2>Promoções de Milhas</h2></div>', unsafe_allow_html=True)
    if tabela.empty:
        st.info("Ainda não há promoções de milhas nesta rodada.")
        return
    for _, item in tabela.iterrows():
        st.markdown(
            f"**{texto(item.get('programa'))}** · {texto(item.get('tipo_promocao'))}  \n"
            f"{texto(item.get('descricao'))}  \n"
            f"Custo por milheiro: {reais(item.get('custo_por_milheiro'))} · "
            f"desconto {texto(item.get('desconto_percentual'), '0')}%"
        )
        link = texto(item.get("link"))
        if link:
            st.link_button("Ver promoção", link)


def combinadas():
    st.markdown('<div class="secao"><h2>Oportunidades Combinadas</h2></div>', unsafe_allow_html=True)
    st.info("A comparação entre comprar milhas e emitir, ou pagar a passagem em dinheiro, entra quando houver preço de milheiro e preço da passagem na mesma rota.")


def historico(data_dir):
    st.markdown('<div class="secao"><h2>Histórico e Tendências</h2></div>', unsafe_allow_html=True)
    caminho = os.path.join(data_dir, "historico.csv")
    if not os.path.exists(caminho):
        st.info("O histórico passa a ser preenchido quando uma rota deixa de aparecer na rodada seguinte.")
        return
    st.dataframe(pd.read_csv(caminho), use_container_width=True, hide_index=True)


def configuracoes():
    st.markdown('<div class="secao"><h2>Configurações</h2></div>', unsafe_allow_html=True)
    caminho = os.path.join(os.path.dirname(__file__), "..", "config-rotina.json")
    if not os.path.exists(caminho):
        st.info("Arquivo de rotas não encontrado.")
        return
    config = json.load(open(caminho, encoding="utf-8"))
    janela = config.get("janela", {})
    st.write(
        "A busca não roda sozinha. Em Atualizar dados, a tabela recarrega o arquivo salvo. "
        f"Quando uma busca nova for pedida, a estadia é de {janela.get('estadia_dias_min', 7)} "
        f"a {janela.get('estadia_dias_max', 20)} dias."
    )
    for grupo in config.get("grupos", []):
        st.markdown(
            f"**{grupo['nome']}**  \n"
            f"Sai de {', '.join(grupo['origens'])} para {', '.join(grupo['destinos'])}."
        )


def main():
    css()
    ativa = pagina_atual()
    nav(ativa)
    atualizar_dados()
    hero()
    data_dir = obter_data_dir()
    voos, tabela_milhas, stats = carregar_dados(data_dir)
    metricas(voos, stats)
    pills(ativa)
    if ativa in {"inicio", "passagens"}:
        passagens(voos)
    elif ativa == "milhas":
        milhas(tabela_milhas)
    elif ativa == "combinadas":
        combinadas()
    elif ativa == "historico":
        historico(data_dir)
    else:
        configuracoes()


main()
