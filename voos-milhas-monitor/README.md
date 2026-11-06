# 🛫 Monitor de Voos e Milhas

Agente de inteligência de preços de passagens aéreas e programas de fidelidade, com validação semanal automática e dashboard Streamlit.

## 📚 Documentação

- **[⚡ QUICK_START.md](QUICK_START.md)** - Começar em 5 minutos
- **[📁 SETUP_CSV.md](SETUP_CSV.md)** - Sistema de armazenamento CSV
- **[🔌 SETUP_APIS.md](SETUP_APIS.md)** - Configuração de APIs
- **[🎨 dashboard/README.md](dashboard/README.md)** - Customizar dashboard
- **[📋 CHANGELOG.md](CHANGELOG.md)** - Histórico de mudanças

## 🚀 Início Rápido

```bash
# Setup automático
./setup.sh  # Linux/Mac
setup.bat   # Windows

# Configurar API
nano .env  # Adicionar KIWI_API_KEY

# Testar
node testar-csv.js

# Dashboard
cd dashboard && streamlit run app.py
```

**Leia [QUICK_START.md](QUICK_START.md) para tutorial completo!**

## 📋 Visão Geral

Este agente monitora periodicamente:
- **Passagens aéreas** com análise logística detalhada
- **Promoções de compra de milhas** em programas de fidelidade
- **Oportunidades combinadas** (compra de milhas + emissão)

E identifica **oportunidades reais de economia** comparando com referências históricas.

## 🎯 Funcionalidades Principais

### 1. Coleta Inteligente de Dados

Para cada passagem, coleta:
- ✅ Informações básicas (preços, datas, companhia, bagagem)
- ✅ Dados logísticos completos (conexões, durações, alertas)
- ✅ Classificação de qualidade do itinerário
- ✅ Score composto (preço + logística)

### 2. Validação Semanal Automática

- Revalida todas as oportunidades registradas
- Atualiza preços e disponibilidade
- Move ofertas expiradas para o histórico
- Mantém apenas oportunidades confirmadas

### 3. Armazenamento em CSV

**Arquivos gerados automaticamente:**
- `voos_ativos.csv`: Oportunidades ativas de passagens
- `milhas_ativas.csv`: Promoções ativas de milhas
- `historico.csv`: Todas as oportunidades (ativas + expiradas)
- `logs.csv`: Registro de todas as execuções
- `estatisticas.json`: Métricas gerais do dashboard

### 4. Dashboard Streamlit

Interface interativa com:
- Visão geral com indicadores
- Filtros avançados por rota, preço, logística
- Detalhamento de cada conexão
- Histórico e tendências
- Configurações editáveis

## 🏗️ Arquitetura

```
voos-milhas-monitor/
├── bot/
│   ├── agent.ts                    # Configuração do agente
│   ├── instructions.md             # Instruções detalhadas (português)
│   ├── tools/
│   │   ├── validar-passagens.ts   # Revalidação semanal
│   │   ├── buscar-voos.ts         # Busca de passagens
│   │   ├── buscar-milhas.ts       # Busca de promoções
│   │   ├── atualizar-planilha.ts  # Integração Google Sheets
│   │   └── enviar-email.ts        # Envio de relatórios
│   ├── schedules/
│   │   └── (sem agendamento)      # A busca só roda quando for pedida
│   ├── lib/
│   │   └── tipos.ts               # Tipos TypeScript compartilhados
│   └── hooks/
│       └── memory.ts              # Memória entre sessões
└── evals/
    ├── evals.config.ts
    └── smoke.eval.ts              # Testes básicos
```

## 🚀 Como Usar

### 1. Configurar Variáveis de Ambiente

Crie um arquivo `.env`:

```bash
# Busca de Voos
ORIGENS=GRU,CGH,VCP
DESTINOS=CDG,LIS,BCN,FCO,MXP,MAD,LON,KEF
ORIGENS_AMERICA_SUL=GRU,CGH,VCP
DESTINOS_AMERICA_SUL=MVD,EZE
ORIGENS_AFRICA=CNF
DESTINOS_AFRICA=JNB,CPT
ORIGENS_CANADA=GRU,CGH,VCP,CNF
DESTINOS_CANADA=YUL,YQB
ORIGENS_ORLANDO=GRU,CGH,VCP,CNF
DESTINOS_ORLANDO=MCO
DATA_IDA_INICIO=2026-12-01
DATA_IDA_FIM=2027-03-31
DATA_VOLTA_INICIO=2026-12-08
DATA_VOLTA_FIM=2027-04-07
PASSAGEIROS=1
PRECO_MAXIMO=3000
DESCONTO_MINIMO=15
VOO_DIRETO=false
MAX_CONEXOES=2
ACEITAR_MUDANCA_AEROPORTO=false

# Busca de Milhas
PROGRAMAS_MILHAS=Smiles,Latam Pass,Livelo,TudoAzul
CUSTO_MAXIMO_MILHEIRO=350
DESCONTO_MINIMO_MILHAS=10

# Kiwi API (obrigatório)
KIWI_API_KEY=sua-chave-api-aqui

# Armazenamento CSV
CSV_DATA_DIR=./data
```

### 2. Validar o Agente

```bash
npx @grok/agent-sdk validate --dir ./voos-milhas-monitor
npx tsc --noEmit -p ./voos-milhas-monitor
```

### 3. Testar Localmente

```bash
# Iniciar playground
npx @grok/agent-sdk serve --dir ./voos-milhas-monitor --mode single --dev

# Abrir http://127.0.0.1:3000/playground
```

### 4. Executar Testes

```bash
npx @grok/agent-sdk eval --dir ./voos-milhas-monitor
```

### 5. Testar Busca Manual

```bash
npx @grok/agent-sdk run --dir ./voos-milhas-monitor --message "Busque passagens de GRU para CDG"
```

## 📊 Dashboard Streamlit

O dashboard lê os arquivos CSV gerados pelo agente:

```bash
# Navegar para pasta do dashboard
cd dashboard

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variável de ambiente
export CSV_DATA_DIR=../data  # Linux/Mac
# ou
set CSV_DATA_DIR=../data  # Windows

# Executar localmente
streamlit run app.py

# Abrir navegador em http://localhost:8501
```

## 🔐 Configuração da Kiwi API

### 1. Obter Chave da API

1. Acesse [Kiwi.com Partners](https://partners.kiwi.com/)
2. Crie uma conta ou faça login
3. Navegue até API Documentation
4. Gere uma chave de API (gratuita para testes)
5. Configure `KIWI_API_KEY` no `.env`

### 2. Testar Integração

```bash
node testar-csv.js
```

Isso irá:
- Testar conexão com Kiwi API
- Buscar voos de exemplo
- Salvar em CSV
- Verificar arquivos gerados

## 🔄 Fluxo de Execução Semanal

```
Segunda-feira 09:00 UTC (06:00 BRT)
│
├─ 1. Revalidar oportunidades existentes
│   └─ Classificar: ATIVA | ATUALIZADA | EXPIRADA | INCONCLUSIVA
│
├─ 2. Buscar novas passagens
│   └─ Analisar logística + calcular economia
│
├─ 3. Buscar promoções de milhas
│   └─ Calcular custo por milheiro
│
├─ 4. Salvar em arquivos CSV
│   ├─ voos_ativos.csv
│   ├─ milhas_ativas.csv
│   ├─ historico.csv (append)
│   ├─ logs.csv (append)
│   └─ estatisticas.json
│
└─ 5. Dashboard Streamlit atualiza automaticamente
    └─ Lê os arquivos CSV e exibe visualizações
```

## 📝 Exemplo de Uso no Playground

```
Usuário: Busque passagens de São Paulo para Paris em janeiro

Agente: Vou buscar passagens de GRU/CGH/VCP para CDG em janeiro...
[chama buscar_voos]
Encontrei 3 oportunidades:

1. ✈️ GRU → CDG (Air France)
   • Ida: 15/jan - Volta: 25/jan
   • Preço: R$ 2.890/pessoa
   • Economia: R$ 610 (17.4%)
   • Voo direto - Classificação: Excelente
   • Score: 92/100

2. ✈️ GRU → CDG (TAP)
   • Ida: 20/jan - Volta: 30/jan
   • Preço: R$ 2.450/pessoa
   • Economia: R$ 1.050 (30%)
   • 1 conexão em LIS (2h30)
   • Classificação: Boa
   • Score: 88/100

...
```

## 🛠️ Próximas Implementações

### Integrações de APIs

- [ ] Skyscanner API
- [ ] Google Flights (scraping)
- [ ] Kayak API
- [ ] Kiwi.com API
- [ ] Sites de promoção de milhas

### Funcionalidades

- [ ] Alertas por Telegram
- [ ] Análise de sazonalidade
- [ ] Previsão de preços com ML
- [ ] Comparação entre datas flexíveis
- [ ] Busca de voos one-way
- [ ] Multi-city / stopover
- [ ] Histórico de preços por rota

## 📄 Licença

Este projeto é privado e de uso pessoal.

## 🤝 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `LOG_EXECUCOES`
2. Consulte a documentação do Agent SDK
3. Revise as variáveis de ambiente
