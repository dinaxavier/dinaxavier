import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json

# Configuração da página
st.set_page_config(
    page_title="Radar de Voos & Milhas",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado para o visual da imagem
st.markdown("""
<style>
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1a1a2e;
    }
    
    .metric-label {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* Cards de destaque */
    .destaque-card {
        background: white;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.3s;
    }
    
    .destaque-card:hover {
        transform: translateY(-5px);
    }
    
    .desconto-badge {
        background: #10b981;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .desconto-badge.negativo {
        background: #ef4444;
    }
    
    /* Tabela estilizada */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Botão customizado */
    .stButton>button {
        background: #3b82f6;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        border: none;
        font-weight: 600;
    }
    
    .stButton>button:hover {
        background: #2563eb;
    }
    
    /* Status online */
    .status-online {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

# Caminho dos dados - tentar múltiplos locais
def obter_data_dir():
    """Tenta encontrar o diretório de dados em múltiplos locais"""
    possiveis_dirs = [
        os.environ.get('CSV_DATA_DIR', ''),
        './data',
        '../data',
        '../../data',
        os.path.join(os.path.dirname(__file__), '..', 'data'),
    ]
    
    for dir_path in possiveis_dirs:
        if dir_path and os.path.isdir(dir_path):
            return dir_path
    
    # Se nenhum existe, criar ./data
    os.makedirs('./data', exist_ok=True)
    return './data'

DATA_DIR = obter_data_dir()

@st.cache_data(ttl=300)
def carregar_dados():
    """Carrega dados dos arquivos CSV"""
    try:
        voos_path = os.path.join(DATA_DIR, 'voos_ativos.csv')
        milhas_path = os.path.join(DATA_DIR, 'milhas_ativas.csv')
        stats_path = os.path.join(DATA_DIR, 'estatisticas.json')
        
        voos_df = pd.DataFrame()
        milhas_df = pd.DataFrame()
        stats = {}
        
        # Carregar voos
        if os.path.exists(voos_path):
            voos_df = pd.read_csv(voos_path)
            voos_df['desconto_percentual'] = pd.to_numeric(voos_df['desconto_percentual'], errors='coerce')
            voos_df['score'] = pd.to_numeric(voos_df['score'], errors='coerce')
            voos_df['preco_por_pessoa'] = pd.to_numeric(voos_df['preco_por_pessoa'], errors='coerce')
        
        # Carregar milhas
        if os.path.exists(milhas_path):
            milhas_df = pd.read_csv(milhas_path)
        
        # Carregar estatísticas
        if os.path.exists(stats_path):
            with open(stats_path, 'r') as f:
                stats = json.load(f)
        
        return voos_df, milhas_df, stats
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), pd.DataFrame(), {}

# Carregar dados
voos_df, milhas_df, stats = carregar_dados()

# Header
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.markdown("### ✈️")
with col_titulo:
    st.markdown("# Radar de Voos & Milhas")
    st.markdown("*As melhores oportunidades de viagem, em um só lugar.*")

# Métricas principais
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "✈️ Oportunidades",
        f"{len(voos_df)}",
        "abertas"
    )

with col2:
    novas = stats.get('novas_semana', 0)
    st.metric(
        "⭐ Novas",
        f"{novas}",
        "na semana"
    )

with col3:
    maior_desc = stats.get('maior_desconto', 0)
    st.metric(
        "💰 Maior Desconto",
        f"{maior_desc:.0f}%",
        ""
    )

with col4:
    melhor_custo = stats.get('melhor_custo_milheiro', 0)
    if melhor_custo < 999:
        st.metric(
            "💳 Melhor Custo",
            f"R$ {melhor_custo/100:.2f}",
            "por milheiro"
        )

with col5:
    ultima_atualizacao = stats.get('ultima_atualizacao', '')
    if ultima_atualizacao:
        dt = datetime.fromisoformat(ultima_atualizacao.replace('Z', '+00:00'))
        st.metric(
            "🕐 Atualização",
            dt.strftime('%d/%m %H:%M'),
            "✅ Ativo"
        )

st.markdown("---")

# Abas
tab1, tab2, tab3 = st.tabs(["✈️ Passagens Aéreas", "💳 Promoções de Milhas", "🎯 Oportunidades Combinadas"])

with tab1:
    st.markdown("### Destaques da Semana")
    
    if not voos_df.empty:
        # Top 3 para destaques
        top3 = voos_df.nlargest(3, 'score')
        
        cols = st.columns(3)
        for idx, (_, voo) in enumerate(top3.iterrows()):
            with cols[idx]:
                # Criar card de destaque
                desconto = voo['desconto_percentual']
                cor_desconto = 'negativo' if desconto < 0 else ''
                
                st.markdown(f"""
                <div class="destaque-card">
                    <div style="padding: 1rem;">
                        <h3>{voo['destino']} 🇧🇷 {voo['cidade_destino'][:20]}</h3>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin: 1rem 0;">
                            <div>
                                <p><strong>{voo['origem']} → {voo['destino']}</strong></p>
                                <p style="color: #666; font-size: 0.9rem;">{voo['data_ida'][:10]}</p>
                            </div>
                            <div class="desconto-badge {cor_desconto}">
                                {desconto:+.0f}%
                            </div>
                        </div>
                        <p><strong>R$ {voo['preco_por_pessoa']:,.2f}</strong></p>
                        <p style="color: #666; font-size: 0.85rem;">
                            {voo['tipo_voo_ida']} • {voo['duracao_total_ida']}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if voo['link'] and str(voo['link']) != 'nan':
                    st.link_button("Ver Passagem →", voo['link'], use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Outras Oportunidades")
        
        # Filtros
        col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
        
        with col_filtro1:
            origens = ['Todos'] + sorted(voos_df['origem'].unique().tolist())
            origem_filtro = st.selectbox("Origem", origens)
        
        with col_filtro2:
            destinos = ['Todos'] + sorted(voos_df['destino'].unique().tolist())
            destino_filtro = st.selectbox("Destino", destinos)
        
        with col_filtro3:
            tipos = ['Todos', 'Direto', '1 Conexão', '2+ Conexões']
            tipo_filtro = st.selectbox("Tipo de Voo", tipos)
        
        with col_filtro4:
            preco_max = st.number_input("Preço Máximo", min_value=0, value=10000, step=500)
        
        # Aplicar filtros
        voos_filtrados = voos_df.copy()
        
        if origem_filtro != 'Todos':
            voos_filtrados = voos_filtrados[voos_filtrados['origem'] == origem_filtro]
        
        if destino_filtro != 'Todos':
            voos_filtrados = voos_filtrados[voos_filtrados['destino'] == destino_filtro]
        
        if tipo_filtro != 'Todos':
            voos_filtrados = voos_filtrados[voos_filtrados['tipo_voo_ida'] == tipo_filtro]
        
        voos_filtrados = voos_filtrados[voos_filtrados['preco_por_pessoa'] <= preco_max]
        
        # Exibir tabela
        if not voos_filtrados.empty:
            # Preparar dados para exibição
            display_df = voos_filtrados[[
                'destino', 'origem', 'data_ida', 'preco_por_pessoa',
                'desconto_percentual', 'tipo_voo_ida', 'duracao_total_ida',
                'classificacao_logistica', 'score'
            ]].copy()
            
            display_df.columns = [
                'Destino', 'Origem', 'Data Ida', 'Preço',
                'Desconto %', 'Tipo', 'Duração', 'Logística', 'Score'
            ]
            
            # Formatar valores
            display_df['Preço'] = display_df['Preço'].apply(lambda x: f"R$ {x:,.2f}")
            display_df['Desconto %'] = display_df['Desconto %'].apply(lambda x: f"{x:+.0f}%")
            display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.0f}/100")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
            
            st.info(f"📊 {len(voos_filtrados)} oportunidades encontradas")
        else:
            st.warning("Nenhuma oportunidade encontrada com os filtros selecionados.")
    
    else:
        st.info("🔍 Aguardando primeira execução do agente...")
        st.markdown("""
        O agente monitora voos semanalmente. Após a primeira execução,
        as oportunidades aparecerão aqui automaticamente!
        """)

with tab2:
    st.markdown("### Promoções de Milhas")
    
    if not milhas_df.empty:
        for _, milha in milhas_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{milha['programa']}** - {milha['tipo_promocao']}")
                    st.caption(milha['descricao'])
                
                with col2:
                    custo = float(milha['custo_por_milheiro'])
                    st.metric("Custo/Milheiro", f"R$ {custo:.2f}")
                
                with col3:
                    desconto = float(milha['desconto_percentual'])
                    st.metric("Desconto", f"{desconto:.0f}%")
                
                if milha['link'] and str(milha['link']) != 'nan':
                    st.link_button("Ver Promoção", milha['link'])
                
                st.markdown("---")
    else:
        st.info("Aguardando dados de promoções de milhas...")

with tab3:
    st.markdown("### Oportunidades Combinadas")
    st.info("💡 Em breve: Comparação de compra de milhas + emissão vs. passagem em dinheiro")

# Footer
st.markdown("---")
col_footer1, col_footer2 = st.columns([3, 1])

with col_footer1:
    st.caption("Dados atualizados automaticamente toda segunda-feira às 06:00 (BRT)")

with col_footer2:
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
