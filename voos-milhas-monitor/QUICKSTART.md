# 🚀 Guia de Início Rápido - Monitor de Voos e Milhas

## ✅ O que foi criado

Agente completo de monitoramento de passagens aéreas e milhas com:

- ✅ **5 ferramentas** especializadas
- ✅ **Execução semanal** automática (segundas 09:00 UTC)
- ✅ **Instruções detalhadas** em português
- ✅ **Validação de tipos** TypeScript completa
- ✅ **Estrutura de planilha** Google Sheets definida
- ✅ **Dashboard Streamlit** (documentação completa)
- ⚡ **E-mail opcional** (ferramenta disponível mas não usada por padrão)

## 📦 Ferramentas Disponíveis

1. **`validar-passagens`**: Revalida oportunidades existentes
2. **`buscar-voos`**: Busca novas passagens com análise logística
3. **`buscar-milhas`**: Busca promoções de compra de milhas
4. **`atualizar-planilha`**: Sincroniza com Google Sheets
5. **`enviar-email`**: Envia relatório semanal

## 🎯 Próximos Passos

### 1. Configurar Variáveis de Ambiente

```bash
# Copiar exemplo
cp .env.example .env

# Editar com seus valores
nano .env
```

**Mínimo necessário para testes:**
```bash
ORIGENS=GRU,CGH
DESTINOS=CDG,LIS
DATA_IDA_INICIO=2027-02-01
DATA_IDA_FIM=2027-04-30
```

### 2. Testar Localmente

```bash
# Validar estrutura
npx @grok/agent-sdk validate --dir ./voos-milhas-monitor

# Verificar tipos
npx tsc --noEmit -p ./voos-milhas-monitor

# Listar ferramentas
npx @grok/agent-sdk info --dir ./voos-milhas-monitor

# Testar ferramenta específica
npx @grok/agent-sdk tool call buscar-voos --dir ./voos-milhas-monitor \
  --input '{
    "origens": ["GRU"],
    "destinos": ["CDG"],
    "data_ida_inicio": "2027-03-01",
    "data_ida_fim": "2027-03-31",
    "passageiros": 1
  }'
```

### 3. Iniciar Playground

```bash
# Servidor local (porta 3000)
npx @grok/agent-sdk serve --dir ./voos-milhas-monitor --mode single --dev

# Abrir http://127.0.0.1:3000/playground
```

**Mensagens de teste no playground:**
- "Busque passagens de GRU para CDG em março"
- "Quais são as melhores promoções de milhas agora?"
- "Revalide todas as oportunidades existentes"

### 4. Configurar Google Sheets (OBRIGATÓRIO)

**👉 Veja guia completo em [`SETUP_APIS.md`](./SETUP_APIS.md)**

#### a) Criar Service Account

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie/selecione projeto
3. Ative "Google Sheets API"
4. Crie Service Account
5. Baixe JSON de credenciais → salve como `credentials.json`

#### b) Criar Planilha

1. Crie nova planilha no Google Sheets
2. Crie 6 abas: `VOOS_ATIVOS`, `MILHAS_ATIVAS`, `OPORTUNIDADES_COMBINADAS`, `HISTORICO`, `CONFIGURACOES`, `LOG_EXECUCOES`
3. Compartilhe com e-mail da Service Account (Editor)
4. Copie ID da planilha (da URL)

#### c) Configurar .env

```bash
GOOGLE_SHEETS_ID=seu-id-aqui
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
```

### 5. Implementar Integrações de APIs

**👉 Veja guia completo em [`SETUP_APIS.md`](./SETUP_APIS.md)**

**🔧 TODO: Conectar com APIs de busca de voos**

As ferramentas estão prontas mas precisam de integração com APIs reais:

- **Skyscanner API**: [rapidapi.com/skyscanner](https://rapidapi.com/skyscanner/api/skyscanner-flight-search)
- **Kiwi.com API**: [tequila.kiwi.com/portal/docs](https://tequila.kiwi.com/portal/docs)
- **Amadeus API**: [developers.amadeus.com](https://developers.amadeus.com/)

Edite os arquivos:
- `bot/tools/buscar-voos.ts` → função `buscarVoosDisponiveis()`
- `bot/tools/buscar-milhas.ts` → função `buscarPromocoesAtivas()`
- `bot/tools/validar-passagens.ts` → função `verificarDisponibilidadeVoo()`

### 6. Dashboard Streamlit (Recomendado)

Veja instruções completas em [`DASHBOARD.md`](./DASHBOARD.md)

```bash
# Criar em diretório separado
cd ..
mkdir dashboard-voos
cd dashboard-voos

# Seguir guia completo em DASHBOARD.md
```

### 7. Deploy (Opcional)

Quando estiver pronto para produção:

```bash
# 1. Criar repositório Git
git init
git add .
git commit -m "feat: agente monitor de voos e milhas"
git remote add origin https://github.com/seu-usuario/voos-milhas-monitor.git
git push -u origin main

# 2. Validar antes do deploy
npx @grok/agent-sdk validate --dir ./voos-milhas-monitor
npx @grok/agent-sdk deploy --dir ./voos-milhas-monitor --dry-run

# 3. Deploy real (guarde o token)
npx @grok/agent-sdk deploy --dir ./voos-milhas-monitor

# 4. Gerenciar
# https://cursor.com/dashboard/deployed-agents
```


## 📁 Estrutura do Projeto

```
voos-milhas-monitor/
├── bot/
│   ├── agent.ts                 # Configuração do agente
│   ├── instructions.md          # Instruções em português (6.6KB)
│   ├── tools/                   # 5 ferramentas
│   │   ├── validar-passagens.ts
│   │   ├── buscar-voos.ts
│   │   ├── buscar-milhas.ts
│   │   ├── atualizar-planilha.ts
│   │   └── enviar-email.ts
│   ├── schedules/
│   │   └── semanal.ts           # Segundas 09:00 UTC
│   ├── lib/
│   │   └── tipos.ts             # Types compartilhados
│   └── hooks/
│       └── memory.ts            # Memória entre sessões
├── evals/
│   ├── evals.config.ts
│   └── smoke.eval.ts            # Testes (TODO)
├── .env.example                 # Template de configuração
├── .gitignore                   # Arquivos ignorados
├── README.md                    # Documentação completa
├── DASHBOARD.md                 # Guia do dashboard Streamlit
├── QUICKSTART.md                # Este arquivo
└── package.json                 # Dependências
```

## 🧪 Status de Implementação

### ✅ Completo
- [x] Estrutura do agente
- [x] Instruções em português
- [x] 5 ferramentas TypeScript
- [x] Agendamento semanal
- [x] Tipos e validações
- [x] Documentação completa
- [x] Template de configuração
- [x] Geração de e-mail HTML
- [x] Estrutura de planilha definida

### 🔧 Requer Implementação
- [ ] Integração com APIs de busca de voos
- [ ] Integração com Google Sheets API
- [ ] Integração com SMTP/SendGrid
- [ ] Scraping de promoções de milhas
- [ ] Cálculo de preços históricos
- [ ] Dashboard Streamlit (código)
- [ ] Testes automatizados (evals)

### 📊 Prioridade de Implementação

**Fase 1 - MVP Funcional:**
1. Integração Google Sheets (CRUD básico)
2. Uma fonte de dados de voos (ex: Skyscanner)
3. E-mail funcionando (Gmail App Password)

**Fase 2 - Dados Reais:**
4. Histórico de preços (planilha)
5. Promoções de milhas (scraping básico)
6. Validação de disponibilidade

**Fase 3 - Análise Avançada:**
7. Múltiplas fontes de dados
8. Oportunidades combinadas
9. Dashboard Streamlit completo

**Fase 4 - Produção:**
10. Testes automatizados
11. Deploy contínuo
12. Monitoramento e alertas

## 🆘 Solução de Problemas

### Erro: "Not signed in to Cursor"
```bash
npx @grok/agent-sdk login
```

### Erro: TypeScript
```bash
npx tsc --noEmit -p ./voos-milhas-monitor
# Corrigir erros mostrados
```

### Erro: Validação
```bash
npx @grok/agent-sdk validate --dir ./voos-milhas-monitor
# Seguir orientações
```

### Playground não abre
```bash
# Verificar se porta 3000 está livre
lsof -i :3000
# Usar porta alternativa
npx @grok/agent-sdk serve --dir ./voos-milhas-monitor --port 3001 --dev
```

### Ferramentas não aparecem
```bash
# Verificar info
npx @grok/agent-sdk info --dir ./voos-milhas-monitor
# Deve listar 5 tools
```

## 📚 Recursos

- [Agent SDK Docs](https://cursor.com/docs/bdk)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Skyscanner API](https://rapidapi.com/skyscanner)

## 📞 Suporte

1. Revisar logs: `LOG_EXECUCOES` (quando implementado)
2. Verificar `.env`: todas variáveis necessárias
3. Testar ferramentas individualmente: `tool call`
4. Consultar documentação completa: `README.md`

---

**Pronto para começar!** 🎉

Execute o playground e teste as ferramentas:
```bash
npx @grok/agent-sdk serve --dir ./voos-milhas-monitor --mode single --dev
```
