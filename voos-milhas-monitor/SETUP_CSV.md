# 📁 Configuração e Uso do Sistema CSV

Este documento explica como o agente armazena dados em arquivos CSV e como o dashboard Streamlit os consome.

## 🎯 Visão Geral

O sistema foi simplificado para **não depender do Google Sheets**. Tudo é armazenado localmente em arquivos CSV que o dashboard lê diretamente.

```
Agente → CSV Files → Dashboard Streamlit
```

## 📂 Estrutura de Arquivos

### Diretório de Dados

Por padrão: `./data/` (configurável via `CSV_DATA_DIR`)

```
data/
├── voos_ativos.csv       # Oportunidades atuais de passagens
├── milhas_ativas.csv     # Promoções atuais de milhas
├── historico.csv         # Histórico de todas oportunidades
├── logs.csv              # Logs de execução do agente
└── estatisticas.json     # Métricas para o dashboard
```

## 📋 Formato dos Arquivos

### voos_ativos.csv

Contém todas as oportunidades de passagens aéreas ativas:

```csv
id,timestamp,origem,destino,cidade_origem,cidade_destino,companhia,data_ida,data_volta,preco_por_pessoa,preco_total,preco_referencia,desconto_percentual,economia_estimada,tipo_voo_ida,tipo_voo_volta,total_conexoes,duracao_total_ida,duracao_total_volta,mudanca_aeroporto,classificacao_logistica,score,bagagem_incluida,link
```

**Campos principais:**
- `id`: Identificador único da oportunidade
- `timestamp`: Data/hora da descoberta
- `origem`/`destino`: Códigos IATA dos aeroportos
- `preco_por_pessoa`: Preço em R$ por passageiro
- `desconto_percentual`: % de economia vs. referência histórica
- `tipo_voo_ida`: "Direto" | "1 conexão" | "2+ conexões"
- `classificacao_logistica`: "Excelente" | "Boa" | "Moderada" | "Atenção"
- `score`: Pontuação geral (0-100)
- `link`: Deep link para compra

### milhas_ativas.csv

Promoções de compra de milhas:

```csv
id,timestamp,programa,tipo_promocao,descricao,custo_por_milheiro,bonus_percentual,desconto_percentual,score,validade_promocao,link
```

**Campos principais:**
- `programa`: "Smiles", "Latam Pass", "Livelo", "TudoAzul"
- `tipo_promocao`: "Compra" | "Transferência" | "Bônus"
- `custo_por_milheiro`: Custo em centavos por 1.000 milhas
- `bonus_percentual`: % de bônus oferecido
- `desconto_percentual`: % de economia vs. histórico

### historico.csv

Registro de todas as oportunidades (append-only):

```csv
id,timestamp,tipo,origem,destino,preco,status,motivo
```

**Status possíveis:**
- `ATIVA`: Ainda disponível
- `ATUALIZADA`: Preço/condições mudaram
- `EXPIRADA`: Não está mais disponível
- `VERIFICAÇÃO INCONCLUSIVA`: Não foi possível revalidar

### logs.csv

Logs de execução do agente:

```csv
execucao_id,data_hora,ofertas_verificadas,ofertas_confirmadas,novas_oportunidades,status
```

### estatisticas.json

Métricas gerais para o dashboard:

```json
{
  "ultima_atualizacao": "2026-11-04T15:30:00Z",
  "total_oportunidades": 32,
  "novas_semana": 9,
  "maior_desconto": 47,
  "melhor_custo_milheiro": 280,
  "melhor_preco": 1690
}
```

## 🔧 Configuração

### 1. Variável de Ambiente

Configure onde os CSVs serão salvos:

```bash
# No .env do agente
CSV_DATA_DIR=./data
```

### 2. Agente (Node.js)

O agente usa `CSVStorage` para salvar dados:

```typescript
import { CSVStorage } from './bot/lib/csv-storage.js';

const storage = new CSVStorage();

// Salvar voos
await storage.salvarVoos(voos);

// Salvar milhas
await storage.salvarMilhas(milhas);

// Adicionar ao histórico
await storage.adicionarAoHistorico(registros);

// Salvar estatísticas
await storage.salvarEstatisticas(stats);

// Registrar log
await storage.registrarLog(logData);
```

### 3. Dashboard (Streamlit)

O dashboard lê os CSVs com Pandas:

```python
import pandas as pd
import os

DATA_DIR = os.environ.get('CSV_DATA_DIR', './data')

# Ler voos
voos_df = pd.read_csv(os.path.join(DATA_DIR, 'voos_ativos.csv'))

# Ler milhas
milhas_df = pd.read_csv(os.path.join(DATA_DIR, 'milhas_ativas.csv'))

# Ler estatísticas
with open(os.path.join(DATA_DIR, 'estatisticas.json')) as f:
    stats = json.load(f)
```

## 🚀 Como Testar

### 1. Testar Geração de CSV

```bash
# Executa agente e gera CSVs de teste
node testar-csv.js
```

Isso irá:
- Buscar voos reais na Kiwi API
- Salvar em `data/voos_ativos.csv`
- Gerar `data/estatisticas.json`
- Criar `data/logs.csv`

### 2. Verificar Arquivos Gerados

```bash
ls -lh data/
cat data/estatisticas.json
head data/voos_ativos.csv
```

### 3. Iniciar Dashboard

```bash
cd dashboard
export CSV_DATA_DIR=../data
streamlit run app.py
```

Abra `http://localhost:8501` e veja os dados!

## 📊 Fluxo Completo

### Execução Semanal do Agente

```
1. Agente executa (toda segunda 06:00 BRT)
   ↓
2. Busca voos na Kiwi API
   ↓
3. Analisa logística e calcula scores
   ↓
4. Salva em voos_ativos.csv (sobrescreve)
   ↓
5. Adiciona ao historico.csv (append)
   ↓
6. Salva estatisticas.json
   ↓
7. Registra em logs.csv (append)
```

### Dashboard Streamlit

```
1. Usuário acessa http://localhost:8501
   ↓
2. Streamlit lê data/voos_ativos.csv
   ↓
3. Lê data/estatisticas.json
   ↓
4. Renderiza cards e tabelas
   ↓
5. Cache de 5 minutos (@st.cache_data)
   ↓
6. Botão "Atualizar" recarrega dados
```

## 🎨 Customização do Dashboard

### Alterar Layout

Edite `dashboard/app.py`:

```python
# Mudar número de colunas nas métricas
col1, col2, col3 = st.columns(3)  # Antes: 5 colunas

# Adicionar novos gráficos
import plotly.express as px
fig = px.bar(voos_df, x='destino', y='preco_por_pessoa')
st.plotly_chart(fig)

# Customizar CSS
st.markdown("""
<style>
    .metric-card { background: #f0f0f0; }
</style>
""", unsafe_allow_html=True)
```

### Adicionar Filtros

```python
# Filtro por companhia
companhias = st.multiselect(
    'Companhias',
    options=voos_df['companhia'].unique()
)

if companhias:
    voos_df = voos_df[voos_df['companhia'].isin(companhias)]
```

## 🔄 Deploy

### Opção 1: Compartilhar Pasta (Rede Local)

```bash
# Agente e dashboard rodam na mesma máquina
# data/ fica acessível para ambos
```

### Opção 2: Cloud Storage

```python
# No agente: upload CSVs para S3/GCS após salvar
# No dashboard: download CSVs do S3/GCS antes de ler
```

### Opção 3: Streamlit Cloud

```bash
# 1. Fazer commit dos CSVs no repo (ou usar artifacts)
# 2. Deploy no Streamlit Cloud
# 3. Agendar GitHub Actions para rodar agente e commitar CSVs
```

## ⚠️ Observações

### Concorrência

- **Leitura**: Dashboard lê enquanto agente escreve = OK
- **Escrita**: Agente sobrescreve arquivos atomicamente
- **Append**: `historico.csv` e `logs.csv` são thread-safe

### Tamanho dos Arquivos

- `voos_ativos.csv`: ~50 KB (100 oportunidades)
- `historico.csv`: Cresce infinitamente (fazer rotação mensal)
- `logs.csv`: Cresce ~1 KB/semana

### Rotação de Histórico

Adicionar ao agente:

```typescript
// Manter apenas últimos 3 meses de histórico
const MESES_MANTER = 3;
const corte = new Date();
corte.setMonth(corte.getMonth() - MESES_MANTER);

// Filtrar e sobrescrever historico.csv
```

## 🐛 Troubleshooting

### Dashboard não mostra dados

```bash
# Verificar se CSVs existem
ls data/

# Verificar conteúdo
head data/voos_ativos.csv

# Verificar variável de ambiente
echo $CSV_DATA_DIR
```

### Erro de encoding

```python
# Usar UTF-8 explicitamente
pd.read_csv('voos.csv', encoding='utf-8')
```

### Dashboard não atualiza

```python
# Limpar cache do Streamlit
st.cache_data.clear()
st.rerun()
```

## 📚 Referências

- [Streamlit Docs](https://docs.streamlit.io/)
- [Pandas CSV](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [Agent SDK](https://docs.cursor.com/agent-sdk/)
