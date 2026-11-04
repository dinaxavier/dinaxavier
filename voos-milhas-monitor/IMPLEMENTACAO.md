# 🔧 Guia de Implementação - Integrações de APIs

Este documento fornece exemplos de código para implementar as integrações pendentes.

## 📊 Google Sheets API

### Instalar Dependência

```bash
npm install googleapis
```

### Implementar Cliente Sheets

Crie `bot/lib/sheets-client.ts`:

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

  async lerDados(aba: string): Promise<any[][]> {
    const response = await this.sheets.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range: `${aba}!A:Z`,
    });

    return response.data.values || [];
  }

  async escreverDados(aba: string, valores: any[][], linha: number = 1) {
    await this.sheets.spreadsheets.values.update({
      spreadsheetId: this.spreadsheetId,
      range: `${aba}!A${linha}`,
      valueInputOption: 'RAW',
      requestBody: {
        values: valores,
      },
    });
  }

  async adicionarLinhas(aba: string, valores: any[][]) {
    await this.sheets.spreadsheets.values.append({
      spreadsheetId: this.spreadsheetId,
      range: `${aba}!A:A`,
      valueInputOption: 'RAW',
      insertDataOption: 'INSERT_ROWS',
      requestBody: {
        values: valores,
      },
    });
  }

  async limparAba(aba: string) {
    await this.sheets.spreadsheets.values.clear({
      spreadsheetId: this.spreadsheetId,
      range: `${aba}!A2:Z`,
    });
  }
}
```

### Usar em `atualizar-planilha.ts`

```typescript
import { SheetsClient } from "../lib/sheets-client.js";

async function atualizarVoos(
  spreadsheetId: string,
  voos: any[],
  modo: string,
  ctx: any
): Promise<number> {
  const client = new SheetsClient();

  // Preparar dados
  const linhas = voos.map((voo) => [
    voo.id,
    voo.timestamp,
    new Date().toISOString(),
    "ATIVA",
    voo.destino,
    voo.origem,
    voo.companhia,
    voo.data_ida,
    voo.data_volta || "",
    voo.preco_por_pessoa,
    voo.preco_total,
    voo.desconto_percentual,
    voo.economia_estimada,
    voo.classificacao_logistica,
    voo.score,
    voo.link || "",
  ]);

  if (modo === "substituir") {
    await client.limparAba("VOOS_ATIVOS");
  }

  await client.adicionarLinhas("VOOS_ATIVOS", linhas);

  return voos.length;
}
```

## ✈️ Integração com APIs de Voos

### Opção 1: Skyscanner via RapidAPI

```bash
npm install axios
```

```typescript
import axios from 'axios';

const RAPID_API_KEY = process.env.RAPID_API_KEY;
const RAPID_API_HOST = 'skyscanner-flight-search.p.rapidapi.com';

async function buscarVoosDisponiveis(params: any): Promise<any[]> {
  const options = {
    method: 'GET',
    url: `https://${RAPID_API_HOST}/v3/flights/live/search/create`,
    params: {
      fromEntityId: params.origens[0],
      toEntityId: params.destinos[0],
      departDate: params.data_ida_inicio,
      returnDate: params.data_volta_inicio,
      adults: params.passageiros,
      currency: 'BRL',
      locale: 'pt-BR',
      market: 'BR',
    },
    headers: {
      'x-rapidapi-key': RAPID_API_KEY,
      'x-rapidapi-host': RAPID_API_HOST,
    },
  };

  try {
    const response = await axios.request(options);
    const sessionToken = response.data.sessionToken;

    // Aguardar resultados
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Buscar resultados
    const resultsOptions = {
      method: 'POST',
      url: `https://${RAPID_API_HOST}/v3/flights/live/search/poll`,
      headers: {
        'x-rapidapi-key': RAPID_API_KEY,
        'x-rapidapi-host': RAPID_API_HOST,
        'Content-Type': 'application/json',
      },
      data: {
        sessionToken,
      },
    };

    const resultsResponse = await axios.request(resultsOptions);
    const itineraries = resultsResponse.data?.content?.results?.itineraries || {};

    // Processar resultados
    const voos = Object.values(itineraries).map((it: any) => {
      const pricing = it.pricingOptions?.[0];

      return {
        origem: params.origens[0],
        destino: params.destinos[0],
        data_ida: params.data_ida_inicio,
        data_volta: params.data_volta_inicio,
        companhia: it.legs?.[0]?.carriers?.marketing?.[0]?.name || 'Desconhecida',
        preco_total: pricing?.price?.amount || 0,
        tipo_voo_ida: it.legs?.[0]?.stopCount === 0 ? 'Direto' : `${it.legs[0].stopCount} Conexão`,
        tipo_voo_volta: it.legs?.[1]?.stopCount === 0 ? 'Direto' : `${it.legs[1]?.stopCount} Conexão`,
        conexoes_ida: extrairConexoes(it.legs?.[0]),
        conexoes_volta: extrairConexoes(it.legs?.[1]),
        duracao_total_ida: formatarDuracao(it.legs?.[0]?.durationInMinutes),
        duracao_total_volta: formatarDuracao(it.legs?.[1]?.durationInMinutes),
        tempo_voo_ida: formatarDuracao(it.legs?.[0]?.durationInMinutes),
        tempo_voo_volta: formatarDuracao(it.legs?.[1]?.durationInMinutes),
        bagagem_incluida: 'Verificar no site',
        tipo_bilhete: 'Econômica',
        link: pricing?.items?.[0]?.deepLink || null,
      };
    });

    return voos;
  } catch (error: any) {
    console.error('Erro ao buscar voos:', error.message);
    return [];
  }
}

function extrairConexoes(leg: any): any[] {
  if (!leg || leg.stopCount === 0) return [];

  return leg.segments?.slice(0, -1).map((seg: any, index: number) => {
    const proximoSeg = leg.segments[index + 1];
    return {
      aeroporto_chegada: seg.destination.id,
      cidade_chegada: seg.destination.name,
      pais_chegada: seg.destination.country || '',
      aeroporto_partida: proximoSeg.origin.id,
      cidade_partida: proximoSeg.origin.name,
      horario_chegada: seg.arrival,
      horario_partida: proximoSeg.departure,
      tempo_conexao_minutos: calcularTempoConexao(seg.arrival, proximoSeg.departure),
      companhia: proximoSeg.marketingCarrier.name,
      troca_companhia: seg.marketingCarrier.id !== proximoSeg.marketingCarrier.id,
      mudanca_aeroporto: seg.destination.id !== proximoSeg.origin.id,
      troca_terminal: false,
      redespacho_bagagem: false,
    };
  });
}

function formatarDuracao(minutos: number): string {
  const horas = Math.floor(minutos / 60);
  const mins = minutos % 60;
  return `${horas}h${mins > 0 ? mins + 'm' : ''}`;
}

function calcularTempoConexao(chegada: string, partida: string): number {
  const chegadaTime = new Date(chegada).getTime();
  const partidaTime = new Date(partida).getTime();
  return Math.floor((partidaTime - chegadaTime) / (1000 * 60));
}
```

### Opção 2: Kiwi.com API

```typescript
import axios from 'axios';

const KIWI_API_KEY = process.env.KIWI_API_KEY;

async function buscarVoosKiwi(params: any): Promise<any[]> {
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
    max_fly_duration: 48,
    limit: 100,
  };

  try {
    const response = await axios.get(url, {
      params: queryParams,
      headers: {
        'apikey': KIWI_API_KEY,
      },
    });

    const voos = response.data.data.map((item: any) => ({
      origem: item.flyFrom,
      destino: item.flyTo,
      data_ida: item.route[0].local_departure,
      data_volta: item.route[item.route.length - 1]?.local_departure || null,
      companhia: item.airlines.join(', '),
      preco_total: item.price,
      tipo_voo_ida: item.route[0].route.length === 1 ? 'Direto' : `${item.route[0].route.length - 1} Conexão`,
      duracao_total_ida: formatarDuracao(item.route[0].duration),
      bagagem_incluida: item.baglimit?.hand_weight ? 'Mão incluída' : 'Não incluída',
      link: item.deep_link,
    }));

    return voos;
  } catch (error: any) {
    console.error('Erro ao buscar voos Kiwi:', error.message);
    return [];
  }
}
```

## 💳 Scraping de Promoções de Milhas

### Usando Cheerio (HTML parsing)

```bash
npm install cheerio axios
```

```typescript
import axios from 'axios';
import * as cheerio from 'cheerio';

async function buscarPromocoesSmiles(): Promise<any[]> {
  try {
    const response = await axios.get('https://www.smiles.com.br/comprar-milhas');
    const $ = cheerio.load(response.data);

    const promocoes: any[] = [];

    $('.promo-box').each((i, el) => {
      const titulo = $(el).find('.title').text().trim();
      const bonus = parseInt($(el).find('.bonus').text().match(/\\d+/)?.[0] || '0');
      const preco = parseFloat($(el).find('.price').text().replace(/[^0-9,]/g, '').replace(',', '.'));

      promocoes.push({
        programa: 'Smiles',
        tipo: 'Compra com bônus',
        descricao: titulo,
        quantidade_base: 10000,
        bonus_percentual: bonus,
        quantidade_total: 10000 * (1 + bonus / 100),
        preco_total: preco,
        validade_promocao: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        validade_milhas: '24 meses',
        elegibilidade: 'Geral',
        condicoes: [],
        link: 'https://www.smiles.com.br/comprar-milhas',
      });
    });

    return promocoes;
  } catch (error) {
    console.error('Erro ao buscar promoções Smiles:', error);
    return [];
  }
}
```

## 📧 Envio de E-mail

### Usando Nodemailer

```bash
npm install nodemailer @types/nodemailer
```

```typescript
import nodemailer from 'nodemailer';

async function enviarEmail(dados: {
  para: string[];
  assunto: string;
  html: string;
}): Promise<boolean> {
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: false,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });

  try {
    await transporter.sendMail({
      from: process.env.EMAIL_FROM,
      to: dados.para.join(','),
      subject: dados.assunto,
      html: dados.html,
    });

    console.log('E-mail enviado com sucesso');
    return true;
  } catch (error: any) {
    console.error('Erro ao enviar e-mail:', error.message);
    return false;
  }
}
```

## 📊 Cálculo de Preços Históricos

### Usando Planilha como Histórico

```typescript
import { SheetsClient } from "../lib/sheets-client.js";

async function buscarPrecoHistorico(
  origem: string,
  destino: string,
  ctx: any
): Promise<number> {
  const client = new SheetsClient();
  const historico = await client.lerDados("HISTORICO");

  // Filtrar por rota
  const rotaHistorico = historico.filter(
    (linha) =>
      linha[4] === origem && // coluna origem
      linha[5] === destino && // coluna destino
      linha[3] === "ATIVA" // apenas ativas
  );

  if (rotaHistorico.length === 0) {
    // Sem histórico, usar valor médio estimado
    return 3000; // BRL
  }

  // Calcular mediana dos últimos 90 dias
  const data90DiasAtras = new Date();
  data90DiasAtras.setDate(data90DiasAtras.getDate() - 90);

  const precosRecentes = rotaHistorico
    .filter((linha) => {
      const dataVoo = new Date(linha[1]); // coluna timestamp
      return dataVoo >= data90DiasAtras;
    })
    .map((linha) => parseFloat(linha[9])); // coluna preco_por_pessoa

  if (precosRecentes.length === 0) {
    return 3000;
  }

  precosRecentes.sort((a, b) => a - b);
  const meio = Math.floor(precosRecentes.length / 2);

  return precosRecentes.length % 2 === 0
    ? (precosRecentes[meio - 1] + precosRecentes[meio]) / 2
    : precosRecentes[meio];
}
```

## 🔄 Exemplo de Fluxo Completo

```typescript
// Em bot/schedules/semanal.ts

import { SheetsClient } from "../lib/sheets-client.js";

async function executarFluxoCompleto(ctx: any) {
  // 1. Inicializar cliente Sheets
  const sheetsClient = new SheetsClient();

  // 2. Ler configurações
  const configData = await sheetsClient.lerDados("CONFIGURACOES");
  const config = parseConfig(configData);

  // 3. Revalidar passagens
  const validacao = await ctx.callTool("validar_passagens", {
    verificar_logistica: true,
  });

  // 4. Buscar novas passagens
  const busca = await ctx.callTool("buscar_voos", {
    origens: config.origens,
    destinos: config.destinos,
    // ... outros parâmetros
  });

  // 5. Atualizar planilha
  await ctx.callTool("atualizar_planilha", {
    operacao: "atualizar_completo",
    dados: {
      voos: busca.oportunidades,
      expiradas: validacao.expiradas,
      log: { /* dados do log */ },
    },
  });

  // 6. Enviar e-mail
  if (config.email_destinatarios.length > 0) {
    await ctx.callTool("enviar_email", {
      destinatarios: config.email_destinatarios,
      dados: {
        resumo: calcularResumo(validacao, busca),
        passagens: busca.oportunidades,
        data_verificacao: new Date().toISOString(),
      },
    });
  }
}
```

## 🧪 Testes Locais

### Testar Google Sheets

```bash
npx @grok/agent-sdk tool call atualizar-planilha --dir ./voos-milhas-monitor \
  --input '{
    "operacao": "registrar_log",
    "dados": {
      "execucao_id": "TEST_001",
      "timestamp": "2027-01-01T10:00:00Z"
    }
  }'
```

### Testar Busca de Voos

```bash
npx @grok/agent-sdk tool call buscar-voos --dir ./voos-milhas-monitor \
  --input '{
    "origens": ["GRU"],
    "destinos": ["CDG"],
    "data_ida_inicio": "2027-03-01",
    "data_ida_fim": "2027-03-31",
    "passageiros": 1
  }'
```

## 📚 Recursos Adicionais

- [Google Sheets API Node.js](https://github.com/googleapis/google-api-nodejs-client)
- [Skyscanner API Docs](https://rapidapi.com/skyscanner/api/skyscanner-flight-search)
- [Kiwi.com API Docs](https://tequila.kiwi.com/portal/docs)
- [Nodemailer Docs](https://nodemailer.com/)
- [Cheerio Docs](https://cheerio.js.org/)

---

**Pronto para implementar!** 🚀

Comece com Google Sheets, depois adicione uma fonte de voos, e finalmente configure o e-mail.
