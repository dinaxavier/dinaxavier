# 🔌 Setup de APIs - O que é necessário

## 📋 Resumo

Para o agente funcionar completamente, você precisa configurar **3 integrações**:

1. ✅ **Google Sheets API** - Para armazenar dados (OBRIGATÓRIO)
2. ✅ **API de Busca de Voos** - Para coletar passagens (OBRIGATÓRIO)
3. ⚡ **Promoções de Milhas** - Scraping ou APIs (OPCIONAL para MVP)

---

## 1️⃣ Google Sheets API (OBRIGATÓRIO)

### O que você precisa:

#### A) Service Account do Google Cloud

1. **Criar projeto no Google Cloud Console**
   - Acesse: https://console.cloud.google.com/
   - Clique em "Criar Projeto"
   - Nome: `voos-milhas-monitor`

2. **Ativar Google Sheets API**
   - No projeto criado, vá em: "APIs e Serviços" → "Biblioteca"
   - Busque: "Google Sheets API"
   - Clique em "Ativar"

3. **Criar Service Account**
   - Vá em: "APIs e Serviços" → "Credenciais"
   - Clique: "Criar Credenciais" → "Conta de serviço"
   - Nome: `voos-milhas-bot`
   - Clique em "Criar e continuar"
   - Função: "Editor" (ou mais restrito se preferir)
   - Clique em "Concluir"

4. **Baixar credenciais JSON**
   - Clique na service account criada
   - Aba "Chaves" → "Adicionar chave" → "Criar nova chave"
   - Tipo: JSON
   - Salve o arquivo como `credentials.json` na raiz do projeto
   - ⚠️ **NUNCA commite este arquivo!** Já está no `.gitignore`

#### B) Criar e Configurar Planilha

1. **Criar planilha**
   - Acesse: https://sheets.new
   - Título: "Monitor de Voos e Milhas"

2. **Criar 6 abas** (renomear as abas):
   - `VOOS_ATIVOS`
   - `MILHAS_ATIVAS`
   - `OPORTUNIDADES_COMBINADAS`
   - `HISTORICO`
   - `CONFIGURACOES`
   - `LOG_EXECUCOES`

3. **Compartilhar com Service Account**
   - Copie o e-mail da service account (do arquivo `credentials.json`, campo `client_email`)
   - Exemplo: `voos-milhas-bot@projeto-123456.iam.gserviceaccount.com`
   - Clique em "Compartilhar" na planilha
   - Cole o e-mail da service account
   - Permissão: **Editor**
   - Desmarque "Notificar pessoas"
   - Clique em "Compartilhar"

4. **Copiar ID da planilha**
   - Da URL: `https://docs.google.com/spreadsheets/d/[ID_AQUI]/edit`
   - Exemplo: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

#### C) Configurar no Projeto

Edite `.env`:
```bash
GOOGLE_SHEETS_ID=seu-id-da-planilha-aqui
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
```

#### D) Instalar Biblioteca

```bash
cd /workspace/voos-milhas-monitor
npm install googleapis
```

#### E) Testar Conexão

Adicione em `bot/lib/sheets-client.ts` (criar arquivo):

```typescript
import { google } from 'googleapis';
import { GoogleAuth } from 'google-auth-library';

export class SheetsClient {
  private sheets: any;
  private spreadsheetId: string;

  constructor() {
    const auth = new GoogleAuth({
      keyFile: process.env.GOOGLE_APPLICATION_CREDENTIALS,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    this.sheets = google.sheets({ version: 'v4', auth });
    this.spreadsheetId = process.env.GOOGLE_SHEETS_ID!;
  }

  async testarConexao(): Promise<boolean> {
    try {
      const response = await this.sheets.spreadsheets.get({
        spreadsheetId: this.spreadsheetId,
      });
      console.log('✓ Conexão com Google Sheets OK:', response.data.properties.title);
      return true;
    } catch (error: any) {
      console.error('✗ Erro ao conectar:', error.message);
      return false;
    }
  }

  async lerDados(aba: string): Promise<any[][]> {
    const response = await this.sheets.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range: `${aba}!A:Z`,
    });
    return response.data.values || [];
  }

  async escreverDados(aba: string, valores: any[][]) {
    await this.sheets.spreadsheets.values.append({
      spreadsheetId: this.spreadsheetId,
      range: `${aba}!A:A`,
      valueInputOption: 'RAW',
      insertDataOption: 'INSERT_ROWS',
      requestBody: { values: valores },
    });
  }
}
```

Teste:
```bash
node -e "import('./bot/lib/sheets-client.js').then(m => new m.SheetsClient().testarConexao())"
```

---

## 2️⃣ API de Busca de Voos (OBRIGATÓRIO)

### Opção A: Kiwi.com (Recomendado - Mais Fácil)

**Vantagens:**
- ✅ Gratuito para testes
- ✅ API simples e bem documentada
- ✅ Não precisa RapidAPI

**O que você precisa:**

1. **Criar conta**
   - Acesse: https://tequila.kiwi.com/portal/login
   - Registre-se (gratuito)

2. **Obter API Key**
   - Após login, vá em: "My Applications"
   - Clique em "Create new application"
   - Nome: `voos-milhas-monitor`
   - Copie a API Key gerada

3. **Configurar no projeto**

Edite `.env`:
```bash
KIWI_API_KEY=sua-api-key-aqui
```

4. **Instalar biblioteca**

```bash
npm install axios
```

5. **Implementar em `bot/tools/buscar-voos.ts`**

Substitua a função `buscarVoosDisponiveis`:

```typescript
import axios from 'axios';

async function buscarVoosDisponiveis(params: any): Promise<any[]> {
  const KIWI_API_KEY = process.env.KIWI_API_KEY;
  
  if (!KIWI_API_KEY) {
    console.error('KIWI_API_KEY não configurada');
    return [];
  }

  const url = 'https://api.tequila.kiwi.com/v2/search';

  const queryParams = {
    fly_from: params.origens.join(','),
    fly_to: params.destinos.join(','),
    date_from: params.data_ida_inicio.replace(/-/g, '/'),
    date_to: params.data_ida_fim.replace(/-/g, '/'),
    return_from: params.data_volta_inicio?.replace(/-/g, '/') || '',
    return_to: params.data_volta_fim?.replace(/-/g, '/') || '',
    adults: params.passageiros,
    curr: 'BRL',
    locale: 'pt',
    max_stopovers: params.max_conexoes || 2,
    limit: 50,
  };

  try {
    const response = await axios.get(url, {
      params: queryParams,
      headers: { 'apikey': KIWI_API_KEY },
    });

    return response.data.data.map((item: any) => ({
      origem: item.flyFrom,
      destino: item.flyTo,
      data_ida: item.local_departure,
      data_volta: item.local_arrival,
      companhia: item.airlines.join(', '),
      preco_total: item.price,
      tipo_voo_ida: item.route.length === 1 ? 'Direto' : `${item.route.length - 1} Conexão`,
      tipo_voo_volta: item.route.length === 1 ? 'Direto' : `${item.route.length - 1} Conexão`,
      conexoes_ida: [],
      conexoes_volta: [],
      duracao_total_ida: `${Math.floor(item.duration.departure / 60)}h${item.duration.departure % 60}m`,
      duracao_total_volta: `${Math.floor(item.duration.return / 60)}h${item.duration.return % 60}m`,
      tempo_voo_ida: `${Math.floor(item.duration.departure / 60)}h`,
      tempo_voo_volta: `${Math.floor(item.duration.return / 60)}h`,
      bagagem_incluida: item.baglimit?.hand_weight ? 'Mão incluída' : 'Verificar',
      tipo_bilhete: 'Econômica',
      link: item.deep_link,
    }));
  } catch (error: any) {
    console.error('Erro ao buscar voos Kiwi:', error.message);
    return [];
  }
}
```

6. **Testar**

```bash
npx @grok/agent-sdk tool call buscar-voos --dir ./voos-milhas-monitor \
  --input '{
    "origens": ["GRU"],
    "destinos": ["CDG"],
    "data_ida_inicio": "2027-03-01",
    "data_ida_fim": "2027-03-15",
    "data_volta_inicio": "2027-03-10",
    "data_volta_fim": "2027-03-20",
    "passageiros": 1
  }'
```

---

### Opção B: Skyscanner via RapidAPI (Mais Completo)

**Vantagens:**
- ✅ Dados mais completos
- ✅ Mais confiável

**Desvantagens:**
- ⚠️ Pago (mas barato: ~$10/mês para 500 req)

**O que você precisa:**

1. **Criar conta RapidAPI**
   - Acesse: https://rapidapi.com/
   - Registre-se (gratuito)

2. **Assinar Skyscanner API**
   - Busque: "Skyscanner Flight Search"
   - URL: https://rapidapi.com/skyscanner/api/skyscanner-flight-search
   - Escolha plano (Basic: $10/mês)

3. **Copiar API Key**
   - Na página da API, copie sua `X-RapidAPI-Key`

4. **Configurar**

```bash
RAPID_API_KEY=sua-key-aqui
```

5. **Implementar** (código em `IMPLEMENTACAO.md` seção Skyscanner)

---

## 3️⃣ Promoções de Milhas (OPCIONAL)

### Opção A: Scraping de Sites (Gratuito)

**Sites principais:**
- Melhores Destinos: https://www.melhoresdestinos.com.br/promocoes-milhas
- Pontos pra Voar: https://www.pontospvoar.com.br/
- MaxMilhas Blog: https://blog.maxmilhas.com.br/

**Ferramentas:**
```bash
npm install cheerio puppeteer
```

**Implementação básica:**

```typescript
import axios from 'axios';
import * as cheerio from 'cheerio';

async function buscarPromocoesAtivas(programas: string[]): Promise<any[]> {
  const promocoes: any[] = [];

  try {
    // Exemplo: Melhores Destinos
    const response = await axios.get('https://www.melhoresdestinos.com.br/promocoes-milhas');
    const $ = cheerio.load(response.data);

    $('.post-item').each((i, el) => {
      const titulo = $(el).find('.post-title').text().trim();
      const link = $(el).find('a').attr('href');

      if (titulo.toLowerCase().includes('smiles') || titulo.toLowerCase().includes('milhas')) {
        promocoes.push({
          programa: extrairPrograma(titulo),
          tipo: 'Compra com bônus',
          descricao: titulo,
          quantidade_base: 10000,
          bonus_percentual: extrairBonus(titulo),
          preco_total: 0,
          link: link,
        });
      }
    });
  } catch (error) {
    console.error('Erro ao buscar promoções:', error);
  }

  return promocoes;
}

function extrairPrograma(texto: string): string {
  if (texto.includes('Smiles')) return 'Smiles';
  if (texto.includes('Latam')) return 'Latam Pass';
  if (texto.includes('Livelo')) return 'Livelo';
  return 'Outros';
}

function extrairBonus(texto: string): number {
  const match = texto.match(/(\d+)%/);
  return match ? parseInt(match[1]) : 0;
}
```

---

## 📊 Resumo - Checklist de Setup

### Mínimo para MVP Funcional:

- [ ] **Google Sheets**
  - [ ] Projeto Google Cloud criado
  - [ ] Google Sheets API ativada
  - [ ] Service Account criada
  - [ ] Arquivo `credentials.json` baixado
  - [ ] Planilha criada com 6 abas
  - [ ] Planilha compartilhada com service account
  - [ ] ID da planilha copiado
  - [ ] Variáveis configuradas no `.env`
  - [ ] Biblioteca `googleapis` instalada
  - [ ] `SheetsClient` implementado
  - [ ] Conexão testada ✓

- [ ] **API de Voos**
  - [ ] Conta criada (Kiwi ou RapidAPI)
  - [ ] API Key obtida
  - [ ] Variável configurada no `.env`
  - [ ] Biblioteca `axios` instalada
  - [ ] Função `buscarVoosDisponiveis` implementada
  - [ ] Busca testada ✓

- [ ] **Integração Completa**
  - [ ] Ferramenta `atualizar-planilha` usando `SheetsClient`
  - [ ] Ferramenta `buscar-voos` usando API real
  - [ ] Schedule testado manualmente
  - [ ] Dados aparecendo na planilha ✓

---

## 🚀 Ordem de Implementação Recomendada

### Passo 1: Google Sheets (30 min)
1. Criar projeto + service account
2. Baixar credentials.json
3. Criar planilha + compartilhar
4. Configurar .env
5. Instalar `googleapis`
6. Implementar `SheetsClient`
7. Testar conexão

### Passo 2: Kiwi API (20 min)
1. Criar conta Kiwi
2. Obter API key
3. Configurar .env
4. Instalar `axios`
5. Implementar `buscarVoosDisponiveis`
6. Testar busca

### Passo 3: Conectar Tudo (30 min)
1. Atualizar `atualizar-planilha.ts` para usar `SheetsClient`
2. Testar fluxo: buscar → processar → salvar na planilha
3. Verificar dados na planilha
4. Testar schedule manualmente

### Passo 4: Dashboard (Separado)
1. Seguir `DASHBOARD.md`
2. Dashboard lê diretamente da planilha
3. Deploy no Streamlit Cloud

---

## 💰 Custos Estimados

| Serviço | Plano | Custo |
|---------|-------|-------|
| Google Sheets | Gratuito | R$ 0 |
| Google Cloud (API) | Gratuito | R$ 0 |
| Kiwi.com API | Gratuito (100 req/mês) | R$ 0 |
| **Total MVP** | | **R$ 0** |
| | | |
| Skyscanner (RapidAPI) | Basic (500 req/mês) | ~R$ 50/mês |
| Kiwi Pro | Premium | ~R$ 100/mês |
| **Total Produção** | | **R$ 50-100/mês** |

---

## 🔧 Configuração do E-mail (Referência do projeto "cãomer")

Como você mencionou que a configuração pode ser igual ao projeto "cãomer", mantenha a ferramenta `enviar-email` disponível caso queira usar no futuro.

Para reativar o e-mail:
1. Descomentar seção do e-mail em `bot/schedules/semanal.ts`
2. Configurar SMTP no `.env` (igual ao "cãomer")
3. Chamar a ferramenta `enviar_email` quando necessário

Por padrão, o schedule **não envia e-mail**, apenas atualiza a planilha.

---

## ❓ Dúvidas Frequentes

**P: Preciso pagar pelo Google Sheets?**  
R: Não! Totalmente gratuito.

**P: Preciso pagar pelas APIs de voos?**  
R: Kiwi.com tem plano gratuito (100 req/mês). Para MVP é suficiente.

**P: Como testar sem gastar requisições de API?**  
R: Use dados fake temporariamente (retorne arrays fixos).

**P: Posso usar scraping em vez de APIs?**  
R: Sim, mas é menos confiável e mais frágil.

**P: Quanto tempo leva para configurar tudo?**  
R: ~1h30 para Google Sheets + Kiwi API + integração básica.

---

## 📞 Próximos Passos

1. Comece com **Google Sheets** (seção 1)
2. Depois configure **Kiwi API** (seção 2)
3. Teste o fluxo completo
4. Implemente **milhas** (opcional)
5. Configure **dashboard** (DASHBOARD.md)

**Pronto!** Seu agente estará 100% funcional! 🎉
