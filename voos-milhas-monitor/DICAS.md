# 💡 Dicas Práticas - Monitor de Voos e Milhas

## 🎯 Começando do Zero

### Passo 1: Testar Localmente (2 minutos)

```bash
cd /workspace/voos-milhas-monitor

# Iniciar playground
npx @grok/agent-sdk serve --dir . --mode single --dev

# Abrir http://127.0.0.1:3000/playground
# Testar: "Busque passagens de GRU para CDG"
```

O agente responderá mesmo sem APIs configuradas (retornará estruturas vazias).

### Passo 2: Configurar Google Sheets (15 minutos)

**Mais fácil para começar:**

1. Criar planilha: https://sheets.new
2. Renomear abas para: `VOOS_ATIVOS`, `MILHAS_ATIVAS`, `OPORTUNIDADES_COMBINADAS`, `HISTORICO`, `CONFIGURACOES`, `LOG_EXECUCOES`
3. Adicionar cabeçalhos na primeira linha de cada aba
4. Tornar pública (ou compartilhar com service account)
5. Copiar ID da URL

**Cabeçalhos sugeridos para VOOS_ATIVOS:**
```
ID | Data Identificação | Data Verificação | Status | Origem | Destino | Companhia | Data Ida | Data Volta | Preço/Pessoa | Preço Total | Desconto % | Economia | Logística | Score | Link
```

### Passo 3: API de Voos Mais Fácil (30 minutos)

**Recomendação: Kiwi.com (mais simples)**

1. Criar conta: https://tequila.kiwi.com/portal/login
2. Obter API key (gratuita para testes)
3. Adicionar ao `.env`: `KIWI_API_KEY=sua-chave`
4. Implementar em `bot/tools/buscar-voos.ts` (exemplo em `IMPLEMENTACAO.md`)

**Alternativa gratuita: Google Flights (scraping básico)**
```typescript
// Usar Puppeteer ou Playwright para scraping
// Menos confiável mas totalmente gratuito
```

### Passo 4: E-mail Básico (10 minutos)

**Gmail com App Password (mais fácil):**

1. Ativar 2FA no Gmail
2. Criar App Password: https://myaccount.google.com/apppasswords
3. Adicionar ao `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASS=sua-senha-app-aqui
EMAIL_FROM=Monitor <seu-email@gmail.com>
EMAIL_DESTINATARIOS=seu-email@gmail.com
```

---

## 🚀 Fluxo de Desenvolvimento Recomendado

### Fase 1: Setup Básico (1 hora)
1. ✅ Estrutura criada
2. Configurar `.env`
3. Testar playground
4. Criar planilha Google Sheets manual

### Fase 2: MVP (2-3 horas)
1. Implementar Google Sheets (leitura/escrita)
2. Implementar Kiwi.com ou scraping básico
3. Testar ferramenta `buscar-voos`
4. Configurar e-mail Gmail

### Fase 3: Dados Reais (2-3 horas)
1. Adicionar cálculo de histórico
2. Implementar `validar-passagens`
3. Adicionar promoções de milhas (1-2 fontes)
4. Testar fluxo completo manual

### Fase 4: Automação (1 hora)
1. Testar schedule manualmente
2. Configurar schedule para rodar semanalmente
3. Monitorar primeira execução
4. Ajustar parâmetros

### Fase 5: Dashboard (2-4 horas)
1. Seguir `DASHBOARD.md`
2. Criar dashboard básico Streamlit
3. Deploy no Streamlit Cloud (gratuito)
4. Adicionar link no `.env`

---

## 💰 Custos Estimados

### Opção 1: Totalmente Gratuito
- Google Sheets: Gratuito
- Kiwi.com API: Gratuito até 100 requisições/mês
- Gmail SMTP: Gratuito
- Streamlit Cloud: Gratuito (plano community)
- **Total: R$ 0/mês**

### Opção 2: Baixo Custo
- Google Sheets: Gratuito
- Skyscanner API (RapidAPI): ~$10/mês (500 req/mês)
- SendGrid: Gratuito até 100 emails/dia
- Streamlit Cloud: Gratuito
- **Total: ~R$ 50/mês**

### Opção 3: Produção
- Google Sheets: Gratuito
- Múltiplas APIs: ~$50/mês
- SendGrid Pro: ~$15/mês
- Cursor Deploy: Incluído
- **Total: ~R$ 300/mês**

---

## 🔥 Hacks e Atalhos

### 1. Teste Sem APIs

Adicione dados fake diretamente na planilha:

```typescript
// Em buscar-voos.ts, retorne dados fake para testes
async function buscarVoosDisponiveis(params: any): Promise<any[]> {
  return [
    {
      origem: "GRU",
      destino: "CDG",
      data_ida: "2027-03-15",
      data_volta: "2027-03-25",
      companhia: "Air France",
      preco_total: 2890,
      tipo_voo_ida: "Direto",
      duracao_total_ida: "11h30m",
      link: "https://www.google.com/flights",
    }
  ];
}
```

### 2. Google Sheets Simplificado

Use biblioteca mais simples:

```bash
npm install simple-google-spreadsheet
```

```typescript
import { GoogleSpreadsheet } from 'simple-google-spreadsheet';

const doc = new GoogleSpreadsheet(process.env.GOOGLE_SHEETS_ID);
await doc.useServiceAccountAuth(require('./credentials.json'));
await doc.loadInfo();

const sheet = doc.sheetsByTitle['VOOS_ATIVOS'];
await sheet.addRow({
  origem: 'GRU',
  destino: 'CDG',
  preco: 2890,
});
```

### 3. E-mail de Teste (Mailtrap)

Teste e-mails sem enviar de verdade:

1. Criar conta: https://mailtrap.io
2. Usar SMTP de teste
3. Ver e-mails na interface web

```bash
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=seu-usuario-mailtrap
SMTP_PASS=sua-senha-mailtrap
```

### 4. Dashboard Ultra-Simples

Sem autenticação, sem Google Sheets, só dados estáticos:

```python
# app.py
import streamlit as st
import pandas as pd

st.title("Monitor de Voos")

# Dados fake
voos = pd.DataFrame({
    'Origem': ['GRU', 'GRU', 'CGH'],
    'Destino': ['CDG', 'LIS', 'BCN'],
    'Preço': [2890, 2450, 3100],
    'Economia': [610, 1050, 400],
})

st.dataframe(voos)
```

### 5. Schedule Manual

Não espere segunda-feira, teste agora:

```bash
# Chamar o schedule diretamente
npx @grok/agent-sdk tool call semanal --dir ./voos-milhas-monitor
```

Ou adicione comando HTTP no schedule:

```typescript
// POST http://localhost:3000/v1/dev/schedules/semanal
// (quando server estiver rodando em --dev)
```

---

## 🐛 Problemas Comuns

### "Google Sheets not found"
- Verificar ID da planilha
- Verificar compartilhamento
- Service account tem acesso?

### "API rate limit"
- Adicionar delay entre requisições
- Usar cache para respostas
- Considerar plano pago

### "Schedule não executa"
- Verificar fuso horário (UTC vs local)
- Testar manualmente primeiro
- Ver logs: `ctx.host.kv.get('execucao:...')`

### "E-mail não envia"
- Testar SMTP manualmente
- Verificar firewall/porta
- Gmail: App Password configurado?

### "Dashboard não atualiza"
- Verificar cache do Streamlit
- Adicionar botão "Atualizar"
- `st.cache_data.clear()`

---

## 📊 Métricas de Sucesso

### Semana 1
- [ ] Playground funcionando
- [ ] 1 ferramenta integrada (Google Sheets)
- [ ] Dados manuais na planilha

### Semana 2
- [ ] API de voos integrada
- [ ] Primeira busca real funcionando
- [ ] E-mail de teste enviado

### Semana 3
- [ ] Validação automática
- [ ] 2+ fontes de dados
- [ ] Schedule executando semanalmente

### Semana 4
- [ ] Dashboard básico online
- [ ] Primeira oportunidade real identificada
- [ ] Sistema rodando automaticamente

---

## 🎯 Metas de Qualidade

### Precisão
- **Meta**: 80%+ das oportunidades ainda disponíveis após 24h
- **Como**: Revalidar frequentemente, fontes confiáveis

### Economia Real
- **Meta**: 15%+ de desconto vs. histórico
- **Como**: Histórico de 90 dias, mediana de preços

### Relevância
- **Meta**: 70%+ classificação logística "Boa" ou melhor
- **Como**: Filtros de conexão, duração, alertas

### Performance
- **Meta**: Execução semanal < 5 minutos
- **Como**: APIs paralelas, cache, limites

---

## 🔐 Segurança

### Checklist
- [ ] `.env` no `.gitignore`
- [ ] `credentials.json` no `.gitignore`
- [ ] Senha forte no dashboard
- [ ] Service Account com permissões mínimas
- [ ] API keys em variáveis de ambiente
- [ ] HTTPS em produção

### Boas Práticas
```bash
# Nunca commite segredos
git add .env  # ❌ NUNCA!

# Use .env.example sem valores reais
cp .env .env.example
# Editar .env.example, remover valores
git add .env.example  # ✅ OK

# Rodar verificação
git diff --cached | grep -i "password\|key\|secret"
```

---

## 📚 Recursos Úteis

### APIs de Voos Gratuitas/Baratas
- Kiwi.com Tequila (gratuita, 100 req/mês)
- Skyscanner RapidAPI ($10/mês)
- Amadeus Self-Service (gratuita dev)

### Scraping (Alternativa)
- Puppeteer (headless Chrome)
- Playwright (mais moderno)
- Scrapy (Python, para batch)

### Promoções de Milhas
- Melhores Destinos (RSS feed)
- Pontos pra Voar (scraping)
- Maxmilhas (API comercial)

### Dashboards
- Streamlit (Python, fácil)
- Gradio (Python, IA-friendly)
- Dash (Python, profissional)
- Next.js (React, full-featured)

---

## 🎓 Aprendizado Contínuo

### Melhorias Futuras
1. **ML para previsão de preços**
   - Treinar modelo com histórico
   - Prever se preço vai subir/cair

2. **Alertas em tempo real**
   - WhatsApp via Twilio
   - Telegram Bot
   - Push notifications

3. **Multi-usuário**
   - Cada usuário tem preferências
   - Alertas personalizados
   - Dashboard compartilhado

4. **Análise avançada**
   - Sazonalidade por rota
   - Melhor dia para comprar
   - Correlação com eventos

---

**Boa sorte com seu monitor!** 🚀✈️

Para dúvidas, consulte:
- `README.md` - Visão geral
- `QUICKSTART.md` - Início rápido
- `IMPLEMENTACAO.md` - Código detalhado
- `DASHBOARD.md` - Dashboard Streamlit
