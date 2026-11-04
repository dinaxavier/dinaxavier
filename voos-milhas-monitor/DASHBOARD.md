# 📊 Dashboard Streamlit - Guia de Implementação

Este documento descreve como criar o dashboard privado Streamlit que consome os dados da planilha.

## 🏗️ Estrutura de Arquivos

```
dashboard-voos/
├── app.py                          # Aplicação principal
├── pages/
│   ├── 1_📊_Visão_Geral.py
│   ├── 2_✈️_Passagens.py
│   ├── 3_💳_Milhas.py
│   ├── 4_🎯_Oportunidades_Combinadas.py
│   ├── 5_📈_Histórico.py
│   └── 6_⚙️_Configurações.py
├── utils/
│   ├── sheets_client.py            # Cliente Google Sheets
│   ├── data_processing.py          # Processamento de dados
│   └── visualizations.py           # Gráficos Plotly
├── .streamlit/
│   ├── config.toml                 # Configurações do Streamlit
│   └── secrets.toml                # Segredos (não commitar!)
├── requirements.txt
├── credentials.json                # Service Account (não commitar!)
└── README.md
```

## 📦 Dependências (requirements.txt)

```txt
streamlit==1.31.0
pandas==2.2.0
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.115.0
plotly==5.18.0
python-dotenv==1.0.1
```

## 🔐 Configuração de Autenticação

### Opção 1: Streamlit Community Cloud

Adicione em `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

[sheets]
spreadsheet_id = "seu-id-da-planilha"

[auth]
username = "admin"
password = "sua-senha-forte-aqui"
```

### Opção 2: Local

Crie `.env`:

```bash
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
SPREADSHEET_ID=seu-id-da-planilha
AUTH_USERNAME=admin
AUTH_PASSWORD=sua-senha-forte
```

## 📄 Exemplo: app.py (Principal)

```python
import streamlit as st
import pandas as pd
from utils.sheets_client import SheetsClient
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Monitor de Voos e Milhas",
    page_icon="🛫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Autenticação simples
def check_password():
    """Retorna True se o usuário forneceu a senha correta."""
    def password_entered():
        if (st.session_state["username"] == st.secrets["auth"]["username"]
            and st.session_state["password"] == st.secrets["auth"]["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", key="password", on_change=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", key="password", on_change=password_entered)
        st.error("Usuário ou senha incorretos")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Título principal
st.title("🛫 Monitor de Voos e Milhas")

# Conectar com Google Sheets
@st.cache_resource
def get_sheets_client():
    return SheetsClient()

client = get_sheets_client()

# Carregar dados
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    voos = client.get_data("VOOS_ATIVOS")
    milhas = client.get_data("MILHAS_ATIVAS")
    log = client.get_data("LOG_EXECUCOES")
    return voos, milhas, log

try:
    voos_df, milhas_df, log_df = load_data()
    
    # Última atualização
    if not log_df.empty:
        ultima_atualizacao = pd.to_datetime(log_df['data_hora_fim'].iloc[-1])
        st.info(f"📅 Última atualização: {ultima_atualizacao.strftime('%d/%m/%Y %H:%M')}")
    
    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Oportunidades Ativas", len(voos_df))
    
    with col2:
        if not voos_df.empty:
            maior_desconto = voos_df['desconto_percentual'].max()
            st.metric("Maior Desconto", f"{maior_desconto:.1f}%")
    
    with col3:
        if not voos_df.empty:
            maior_economia = voos_df['economia_estimada'].max()
            st.metric("Maior Economia", f"R$ {maior_economia:.2f}")
    
    with col4:
        if not milhas_df.empty:
            melhor_milheiro = milhas_df['custo_por_milheiro'].min()
            st.metric("Melhor Milheiro", f"R$ {melhor_milheiro/100:.2f}")
    
    # Top 5 Oportunidades
    st.subheader("🏆 Top 5 Melhores Oportunidades")
    
    if not voos_df.empty:
        top5 = voos_df.nlargest(5, 'score')
        
        for idx, row in top5.iterrows():
            with st.expander(f"✈️ {row['origem']} → {row['destino']} - R$ {row['preco_por_pessoa']:.2f}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Companhia:** {row['companhia']}")
                    st.write(f"**Datas:** {row['data_ida']} - {row['data_volta']}")
                    st.write(f"**Score:** {row['score']:.0f}/100")
                
                with col2:
                    st.write(f"**Preço:** R$ {row['preco_total']:.2f}")
                    st.write(f"**Economia:** R$ {row['economia_estimada']:.2f}")
                    st.write(f"**Desconto:** {row['desconto_percentual']:.1f}%")
                
                with col3:
                    st.write(f"**Logística:** {row['classificacao_logistica']}")
                    st.write(f"**Conexões Ida:** {row['conexoes_ida']}")
                    st.write(f"**Duração:** {row['duracao_total_ida']}")
                
                if row['link']:
                    st.link_button("🔗 Ver Passagem", row['link'])
    else:
        st.info("Nenhuma oportunidade disponível no momento.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Verifique se a planilha está configurada corretamente e compartilhada com a service account.")

# Sidebar
with st.sidebar:
    st.header("Navegação")
    st.page_link("app.py", label="🏠 Início", icon="🏠")
    st.page_link("pages/1_📊_Visão_Geral.py", label="Visão Geral")
    st.page_link("pages/2_✈️_Passagens.py", label="Passagens")
    st.page_link("pages/3_💳_Milhas.py", label="Milhas")
    st.page_link("pages/4_🎯_Oportunidades_Combinadas.py", label="Combinadas")
    st.page_link("pages/5_📈_Histórico.py", label="Histórico")
    st.page_link("pages/6_⚙️_Configurações.py", label="Configurações")
    
    st.divider()
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
```

## 📄 Exemplo: utils/sheets_client.py

```python
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd

class SheetsClient:
    def __init__(self):
        # Credenciais
        if 'gcp_service_account' in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        else:
            credentials = service_account.Credentials.from_service_account_file(
                'credentials.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        
        self.service = build('sheets', 'v4', credentials=credentials)
        self.spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
    
    def get_data(self, sheet_name: str) -> pd.DataFrame:
        """Lê dados de uma aba da planilha e retorna como DataFrame."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:Z"
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return pd.DataFrame()
            
            # Primeira linha como cabeçalho
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
        
        except Exception as e:
            st.error(f"Erro ao ler aba '{sheet_name}': {e}")
            return pd.DataFrame()
```

## 📄 Exemplo: pages/2_✈️_Passagens.py

```python
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.sheets_client import SheetsClient

st.set_page_config(page_title="Passagens", page_icon="✈️", layout="wide")

st.title("✈️ Passagens Aéreas")

# Cliente Sheets
client = SheetsClient()

# Carregar dados
@st.cache_data(ttl=300)
def load_voos():
    return client.get_data("VOOS_ATIVOS")

voos_df = load_voos()

if voos_df.empty:
    st.info("Nenhuma passagem disponível no momento.")
    st.stop()

# Filtros
st.sidebar.header("Filtros")

# Filtro por país/cidade
if 'destino' in voos_df.columns:
    destinos = ['Todos'] + sorted(voos_df['destino'].unique().tolist())
    destino_filtro = st.sidebar.selectbox("Destino", destinos)
    
    if destino_filtro != 'Todos':
        voos_df = voos_df[voos_df['destino'] == destino_filtro]

# Filtro por preço
if 'preco_por_pessoa' in voos_df.columns:
    voos_df['preco_por_pessoa'] = pd.to_numeric(voos_df['preco_por_pessoa'], errors='coerce')
    preco_min = voos_df['preco_por_pessoa'].min()
    preco_max = voos_df['preco_por_pessoa'].max()
    
    preco_range = st.sidebar.slider(
        "Faixa de Preço (R$)",
        float(preco_min),
        float(preco_max),
        (float(preco_min), float(preco_max))
    )
    
    voos_df = voos_df[
        (voos_df['preco_por_pessoa'] >= preco_range[0]) &
        (voos_df['preco_por_pessoa'] <= preco_range[1])
    ]

# Filtro por classificação logística
if 'classificacao_logistica' in voos_df.columns:
    classificacoes = st.sidebar.multiselect(
        "Classificação Logística",
        options=['Excelente', 'Boa', 'Moderada', 'Atenção'],
        default=['Excelente', 'Boa', 'Moderada', 'Atenção']
    )
    
    voos_df = voos_df[voos_df['classificacao_logistica'].isin(classificacoes)]

# Mostrar resultados
st.write(f"**{len(voos_df)} oportunidades encontradas**")

# Gráfico de dispersão
if not voos_df.empty and 'preco_por_pessoa' in voos_df.columns and 'economia_estimada' in voos_df.columns:
    voos_df['economia_estimada'] = pd.to_numeric(voos_df['economia_estimada'], errors='coerce')
    
    fig = px.scatter(
        voos_df,
        x='preco_por_pessoa',
        y='economia_estimada',
        color='classificacao_logistica',
        size='score',
        hover_data=['origem', 'destino', 'companhia'],
        title='Preço vs. Economia',
        labels={
            'preco_por_pessoa': 'Preço por Pessoa (R$)',
            'economia_estimada': 'Economia Estimada (R$)',
            'classificacao_logistica': 'Logística'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Lista de oportunidades
for idx, row in voos_df.iterrows():
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.subheader(f"{row['origem']} → {row['destino']}")
            st.caption(f"{row['companhia']} • {row['classificacao_logistica']}")
        
        with col2:
            st.metric("Preço", f"R$ {float(row['preco_por_pessoa']):.2f}")
        
        with col3:
            st.metric(
                "Economia",
                f"R$ {float(row['economia_estimada']):.2f}",
                f"-{float(row['desconto_percentual']):.1f}%"
            )
        
        with col4:
            if row['link']:
                st.link_button("Ver", row['link'])
        
        st.divider()
```

## 🚀 Deploy

### Streamlit Community Cloud (Gratuito)

1. Faça commit do código no GitHub (sem `secrets.toml` e `credentials.json`)
2. Acesse [streamlit.io/cloud](https://streamlit.io/cloud)
3. Conecte seu repositório
4. Configure os secrets no painel
5. Deploy!

### Alternativas

- **Heroku**: Suporta apps Python
- **Railway**: Deploy simples
- **Render**: Tier gratuito disponível
- **Self-hosted**: Docker + Nginx

## 🔒 Segurança

- ✅ Nunca commite `secrets.toml` ou `credentials.json`
- ✅ Use autenticação (senha ou OAuth)
- ✅ Configure Google Sheets para acesso somente leitura
- ✅ Use HTTPS em produção
- ✅ Limite IPs se possível

## 📚 Recursos

- [Documentação Streamlit](https://docs.streamlit.io/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Plotly Charts](https://plotly.com/python/)
