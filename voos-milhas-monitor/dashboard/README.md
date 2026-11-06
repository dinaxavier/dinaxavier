# ✈️ Dashboard Radar de Voos & Milhas

Dashboard interativo em Streamlit que exibe oportunidades de viagem monitoradas pelo agente.

## 🎨 Design

O dashboard foi projetado para ser **visualmente atraente** e **fácil de usar**, com:

- 📊 Cards de métricas destacando oportunidades
- 🎴 Cards visuais dos destaques da semana
- 📋 Tabela filtrada de todas as oportunidades
- 🔄 Atualização automática a cada 5 minutos
- 🎯 Filtros avançados por origem, destino, tipo, preço

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
cd dashboard
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configurar Dados

```bash
# Definir onde estão os CSVs
export CSV_DATA_DIR=../data  # Linux/Mac
# ou
set CSV_DATA_DIR=../data  # Windows
```

### 3. Executar

```bash
streamlit run app.py
```

Abra: http://localhost:8501

## 📊 Estrutura da Interface

### Header

```
┌────────────────────────────────────────────────────┐
│  ✈️  Radar de Voos & Milhas                       │
│  As melhores oportunidades de viagem, em um só lugar │
└────────────────────────────────────────────────────┘
```

### Métricas Principais

```
┌────────────┬────────────┬────────────┬────────────┬────────────┐
│ ✈️ 32      │ ⭐ 9       │ 💰 47%     │ 💳 R$ 2,80 │ 🕐 01/06   │
│ Oportunid. │ Novas      │ Maior Desc.│ Melhor $   │ Atualização│
└────────────┴────────────┴────────────┴────────────┴────────────┘
```

### Abas

1. **✈️ Passagens Aéreas**
   - Destaques da Semana (top 3 cards visuais)
   - Filtros avançados
   - Tabela com todas oportunidades

2. **💳 Promoções de Milhas**
   - Lista de promoções ativas
   - Custo por milheiro
   - Links diretos

3. **🎯 Oportunidades Combinadas**
   - Em breve: comparação compra + emissão vs. dinheiro

### Destaques da Semana

Cards visuais dos 3 melhores voos:

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Lisboa 🇵🇹           │ Roma 🇮🇹             │ Madri 🇪🇸            │
│ GRU → LIS           │ GRU → FCO           │ CNF → MAD           │
│ 15 set - 28 set 2025│ 05 nov - 19 nov 2025│ 10 out - 24 out 2025│
│                     │                     │                     │
│ R$ 2.890            │ R$ 3.680            │ R$ 3.250            │
│ Direto • 10h35      │ 1 conexão • 15h10   │ Direto • 11h20      │
│                     │                     │                     │
│     -42%            │     -32%            │     -34%            │
│ [Ver Passagem →]    │ [Ver Passagem →]    │ [Ver Passagem →]    │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

### Filtros

```
┌────────────┬────────────┬────────────┬────────────┐
│ Origem     │ Destino    │ Tipo       │ Preço Max  │
│ [Todos  ▼] │ [Todos  ▼] │ [Todos  ▼] │ [10000   ] │
└────────────┴────────────┴────────────┴────────────┘
```

### Tabela de Oportunidades

```
┌──────────┬────────┬───────────┬─────────┬───────────┬─────────┬──────────┬───────────┬────────┐
│ Destino  │ Origem │ Data Ida  │ Preço   │ Desconto  │ Tipo    │ Duração  │ Logística │ Score  │
├──────────┼────────┼───────────┼─────────┼───────────┼─────────┼──────────┼───────────┼────────┤
│ LIS      │ GRU    │ 15/09/2025│ R$ 2.890│ -42%      │ Direto  │ 10h35    │ Excelente │ 95/100 │
│ FCO      │ GRU    │ 05/11/2025│ R$ 3.680│ -32%      │ 1 conex │ 15h10    │ Boa       │ 87/100 │
│ MAD      │ CNF    │ 10/10/2025│ R$ 3.250│ -34%      │ Direto  │ 11h20    │ Excelente │ 88/100 │
└──────────┴────────┴───────────┴─────────┴───────────┴─────────┴──────────┴───────────┴────────┘
```

## 🎨 Personalização

### Cores e Tema

Edite o CSS no início de `app.py`:

```python
st.markdown("""
<style>
    /* Header com gradiente */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Badge de desconto verde */
    .desconto-badge {
        background: #10b981;  /* Alterar cor aqui */
    }
</style>
""", unsafe_allow_html=True)
```

### Logo e Título

```python
# Substituir emoji por imagem
st.image('logo.png', width=50)
st.markdown("# Radar de Voos & Milhas")
```

### Métricas

Adicionar ou remover colunas:

```python
# Antes: 5 colunas
col1, col2, col3, col4, col5 = st.columns(5)

# Depois: 3 colunas
col1, col2, col3 = st.columns(3)
```

### Gráficos

Adicionar visualizações com Plotly:

```python
import plotly.express as px

# Gráfico de barras por destino
fig = px.bar(
    voos_df,
    x='destino',
    y='preco_por_pessoa',
    title='Preços por Destino',
    color='desconto_percentual',
    color_continuous_scale='RdYlGn'
)
st.plotly_chart(fig, use_container_width=True)

# Gráfico de linha - evolução de preços
historico_df = pd.read_csv(os.path.join(DATA_DIR, 'historico.csv'))
fig = px.line(
    historico_df,
    x='timestamp',
    y='preco',
    color='destino',
    title='Evolução de Preços'
)
st.plotly_chart(fig)
```

### Filtros Adicionais

```python
# Filtro por companhia
companhias = st.multiselect(
    'Companhias Aéreas',
    options=voos_df['companhia'].unique()
)

# Filtro por classificação logística
logistica = st.select_slider(
    'Classificação Logística',
    options=['Atenção', 'Moderada', 'Boa', 'Excelente']
)

# Filtro por score mínimo
score_min = st.slider('Score Mínimo', 0, 100, 70)
voos_df = voos_df[voos_df['score'] >= score_min]
```

## 📱 Responsividade

O dashboard é responsivo e funciona bem em:
- 🖥️ Desktop (recomendado)
- 💻 Laptop
- 📱 Tablet (layout adaptado)
- 📱 Mobile (limitado)

## 🔄 Atualização de Dados

### Automática

O dashboard usa cache de 5 minutos:

```python
@st.cache_data(ttl=300)  # 300 segundos = 5 minutos
def carregar_dados():
    # ...
```

Após 5 minutos, recarrega automaticamente.

### Manual

Clique no botão **"🔄 Atualizar Dados"** no rodapé.

Ou pressione **R** no teclado (atalho do Streamlit).

## 🚀 Deploy

### Opção 1: Streamlit Cloud (Recomendado)

```bash
# 1. Commitar dashboard no GitHub
git add dashboard/
git commit -m "Add Streamlit dashboard"
git push

# 2. Acessar https://share.streamlit.io/
# 3. Conectar repositório GitHub
# 4. Apontar para dashboard/app.py
# 5. Definir CSV_DATA_DIR nas secrets
```

**Secrets no Streamlit Cloud:**

```toml
# .streamlit/secrets.toml
CSV_DATA_DIR = "/mount/data"
```

### Opção 2: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

ENV CSV_DATA_DIR=/data

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t dashboard-voos .
docker run -p 8501:8501 -v $(pwd)/../data:/data dashboard-voos
```

### Opção 3: Servidor Linux

```bash
# Instalar systemd service
sudo nano /etc/systemd/system/dashboard-voos.service

# Conteúdo:
[Unit]
Description=Dashboard Voos e Milhas
After=network.target

[Service]
Type=simple
User=usuario
WorkingDirectory=/home/usuario/dashboard
Environment="CSV_DATA_DIR=/home/usuario/data"
ExecStart=/home/usuario/venv/bin/streamlit run app.py

[Install]
WantedBy=multi-user.target

# Ativar
sudo systemctl enable dashboard-voos
sudo systemctl start dashboard-voos
```

## 🐛 Troubleshooting

### Dashboard em branco

```python
# Verificar se dados existem
import os
print(os.listdir(os.environ.get('CSV_DATA_DIR', './data')))
```

### Erro de encoding

```python
# Adicionar encoding explícito
pd.read_csv(arquivo, encoding='utf-8')
```

### Gráficos não aparecem

```bash
# Reinstalar Plotly
pip uninstall plotly
pip install plotly
```

### Cache não atualiza

```python
# Forçar limpeza
st.cache_data.clear()
st.rerun()
```

### Porta já em uso

```bash
# Mudar porta
streamlit run app.py --server.port=8502
```

## 📚 Recursos

- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
- [Pandas](https://pandas.pydata.org/)
- [Streamlit Gallery](https://streamlit.io/gallery)

## 🤝 Contribuindo

Sugestões de melhorias:

1. **Mapas**: Adicionar mapa interativo com Folium
2. **Notificações**: Integrar com Telegram/Slack
3. **Comparações**: Gráficos de benchmark de preços
4. **Alertas**: Sistema de alertas customizados
5. **Exportação**: Download de dados em Excel/PDF

## 📄 Licença

Uso pessoal/privado.
