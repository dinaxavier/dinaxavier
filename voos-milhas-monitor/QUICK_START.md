# ⚡ Guia Rápido - Começar em 5 Minutos

## 🎯 Objetivo

Configurar e rodar o **Monitor de Voos e Milhas** em menos de 5 minutos.

## ✅ Pré-requisitos

- Node.js 18+ instalado
- Python 3.9+ instalado
- Chave da API Kiwi.com (gratuita)

## 🚀 Passos

### 1. Setup Automático (30 segundos)

**Linux/Mac:**
```bash
./setup.sh
```

**Windows:**
```bat
setup.bat
```

### 2. Configurar API (1 minuto)

Abra o arquivo `.env` e adicione sua chave:

```bash
KIWI_API_KEY=sua-chave-aqui
```

**Onde obter:**
1. Acesse https://partners.kiwi.com/
2. Crie conta gratuita
3. Gere API key em "API Documentation"

### 3. Testar Integração (30 segundos)

```bash
node testar-csv.js
```

**Resultado esperado:**
```
✓ Kiwi API: OK
✓ Encontrados 5 voos
✓ CSV Storage: OK
✓ Arquivos criados:
  ✓ voos_ativos.csv (2.3 KB)
  ✓ estatisticas.json (245 bytes)
  ✓ logs.csv (156 bytes)
```

### 4. Iniciar Dashboard (1 minuto)

```bash
cd dashboard
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

export CSV_DATA_DIR=../data  # Linux/Mac
# ou
set CSV_DATA_DIR=../data  # Windows

streamlit run app.py
```

Abra: http://localhost:8501 🎉

### 5. Testar Agente (opcional)

```bash
npx @grok/agent-sdk serve --dir . --mode single --dev
```

Abra: http://localhost:3000/playground

## 📁 Estrutura de Arquivos

```
voos-milhas-monitor/
├── bot/                    # Código do agente
├── dashboard/              # Dashboard Streamlit
├── data/                   # Dados gerados (CSVs)
├── .env                    # Configuração
├── setup.sh                # Setup Linux/Mac
├── setup.bat               # Setup Windows
└── testar-csv.js           # Script de teste
```

## 🎨 Resultado Visual

Após executar, você verá:

### Dashboard

```
┌────────────────────────────────────────────┐
│ ✈️ Radar de Voos & Milhas                 │
├─────┬─────┬─────┬─────┬─────────────────┤
│ 32  │ 9   │ 47% │ R$  │ 01/06 09:24    │
│ Opor│ Nova│ Desc│ 2,80│ ✅ Ativo        │
└─────┴─────┴─────┴─────┴─────────────────┘

🎴 Destaques da Semana

┌──────────────┬──────────────┬──────────────┐
│ Lisboa 🇵🇹    │ Roma 🇮🇹      │ Madri 🇪🇸     │
│ GRU → LIS    │ GRU → FCO    │ CNF → MAD    │
│ R$ 2.890     │ R$ 3.680     │ R$ 3.250     │
│ -42%         │ -32%         │ -34%         │
└──────────────┴──────────────┴──────────────┘

📋 Todas as Oportunidades (com filtros)
```

## 🔧 Configuração Rápida

### Mudar Origens/Destinos

Edite `.env`:

```bash
ORIGENS=GRU,CGH,VCP
DESTINOS=CDG,LIS,BCN,FCO,MAD,LON
```

### Ajustar Período

```bash
DATA_IDA_INICIO=2026-12-01
DATA_IDA_FIM=2027-03-31
```

### Filtrar por Preço

```bash
PRECO_MAXIMO=3000
DESCONTO_MINIMO=15
```

## 🎯 Uso Diário

### Ver Oportunidades

```bash
# Iniciar dashboard
cd dashboard && streamlit run app.py
```

### Buscar Manualmente

```bash
npx @grok/agent-sdk run --dir . --message "Busque passagens de GRU para CDG em janeiro"
```

### Execução Automática

O agente roda automaticamente toda **segunda-feira às 06:00 BRT**.

Para forçar execução manual:

```bash
npx @grok/agent-sdk run --dir . --message "Execute a validação semanal completa"
```

## 🐛 Solução de Problemas

### Dashboard não inicia

```bash
# Reinstalar dependências
cd dashboard
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Sem dados no dashboard

```bash
# Verificar se CSVs existem
ls -lh data/

# Executar teste novamente
node testar-csv.js
```

### Erro de API key

```bash
# Verificar se está configurada
grep KIWI_API_KEY .env

# Testar conexão
node testar-csv.js
```

## 📚 Documentação Completa

- **README.md** - Visão geral completa
- **SETUP_CSV.md** - Detalhes do sistema CSV
- **SETUP_APIS.md** - Todas as integrações
- **dashboard/README.md** - Customizar dashboard
- **CHANGELOG.md** - Histórico de mudanças

## 💡 Dicas

### Performance

```bash
# Limitar busca para testar mais rápido
ORIGENS=GRU
DESTINOS=LIS
PRECO_MAXIMO=5000
```

### Customização

```bash
# Alterar cores do dashboard
# Edite dashboard/app.py na seção CSS
```

### Deploy

```bash
# Streamlit Cloud (gratuito)
# 1. Commitar código no GitHub
# 2. Conectar em share.streamlit.io
# 3. Deploy automático!
```

## 🎉 Pronto!

Você agora tem:
- ✅ Agente monitorando voos automaticamente
- ✅ Dashboard visual com oportunidades
- ✅ Dados salvos em CSV
- ✅ Sistema rodando localmente

## 🚀 Próximos Passos

1. **Personalize** suas preferências no `.env`
2. **Explore** o dashboard em `http://localhost:8501`
3. **Aguarde** a primeira execução automática (segunda 06:00)
4. **Compartilhe** fazendo deploy no Streamlit Cloud

## 🤝 Suporte

Problemas? Verifique:
1. Logs em `data/logs.csv`
2. Documentação completa em `README.md`
3. Validação: `npx @grok/agent-sdk validate --dir .`

---

**Tempo total de setup:** ~5 minutos ⏱️  
**Dificuldade:** ⭐⭐ (Fácil)  
**Resultado:** Dashboard profissional com dados reais! 🎉
