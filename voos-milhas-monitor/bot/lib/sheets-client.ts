import { google } from 'googleapis';
import { GoogleAuth } from 'google-auth-library';

/**
 * Cliente para interação com Google Sheets API
 * Gerencia leitura e escrita de dados na planilha
 */
export class SheetsClient {
  private sheets: any;
  private spreadsheetId: string;

  constructor() {
    const credentialsPath = process.env.GOOGLE_APPLICATION_CREDENTIALS;
    const spreadsheetId = process.env.GOOGLE_SHEETS_ID;

    if (!credentialsPath) {
      throw new Error(
        'GOOGLE_APPLICATION_CREDENTIALS não configurada. Configure no .env'
      );
    }

    if (!spreadsheetId) {
      throw new Error('GOOGLE_SHEETS_ID não configurada. Configure no .env');
    }

    const auth = new GoogleAuth({
      keyFile: credentialsPath,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    this.sheets = google.sheets({ version: 'v4', auth });
    this.spreadsheetId = spreadsheetId;
  }

  /**
   * Testa a conexão com o Google Sheets
   */
  async testarConexao(): Promise<boolean> {
    try {
      const response = await this.sheets.spreadsheets.get({
        spreadsheetId: this.spreadsheetId,
      });
      console.log(
        '✓ Conexão com Google Sheets OK:',
        response.data.properties.title
      );
      return true;
    } catch (error: any) {
      console.error('✗ Erro ao conectar com Google Sheets:', error.message);
      return false;
    }
  }

  /**
   * Lê dados de uma aba da planilha
   */
  async lerDados(aba: string): Promise<any[][]> {
    try {
      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: `${aba}!A:Z`,
      });

      const valores = response.data.values || [];
      console.log(`📖 Lidos ${valores.length} linhas da aba ${aba}`);
      return valores;
    } catch (error: any) {
      console.error(`✗ Erro ao ler aba ${aba}:`, error.message);
      return [];
    }
  }

  /**
   * Lê dados como objetos (primeira linha = cabeçalhos)
   */
  async lerDadosComoObjetos(aba: string): Promise<any[]> {
    const valores = await this.lerDados(aba);

    if (valores.length === 0) {
      return [];
    }

    const cabecalhos = valores[0];
    const linhas = valores.slice(1);

    return linhas.map((linha) => {
      const objeto: any = {};
      cabecalhos.forEach((cabecalho, index) => {
        objeto[cabecalho] = linha[index] || '';
      });
      return objeto;
    });
  }

  /**
   * Escreve dados em uma aba (substitui conteúdo)
   */
  async escreverDados(
    aba: string,
    valores: any[][],
    linhaInicio: number = 1
  ): Promise<boolean> {
    try {
      await this.sheets.spreadsheets.values.update({
        spreadsheetId: this.spreadsheetId,
        range: `${aba}!A${linhaInicio}`,
        valueInputOption: 'RAW',
        requestBody: {
          values: valores,
        },
      });

      console.log(`✓ Escritos ${valores.length} linhas na aba ${aba}`);
      return true;
    } catch (error: any) {
      console.error(`✗ Erro ao escrever na aba ${aba}:`, error.message);
      return false;
    }
  }

  /**
   * Adiciona linhas ao final da aba
   */
  async adicionarLinhas(aba: string, valores: any[][]): Promise<boolean> {
    try {
      await this.sheets.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: `${aba}!A:A`,
        valueInputOption: 'RAW',
        insertDataOption: 'INSERT_ROWS',
        requestBody: {
          values: valores,
        },
      });

      console.log(`✓ Adicionadas ${valores.length} linhas na aba ${aba}`);
      return true;
    } catch (error: any) {
      console.error(`✗ Erro ao adicionar linhas na aba ${aba}:`, error.message);
      return false;
    }
  }

  /**
   * Limpa dados de uma aba (mantém cabeçalhos)
   */
  async limparAba(aba: string, manterCabecalho: boolean = true): Promise<boolean> {
    try {
      const range = manterCabecalho ? `${aba}!A2:Z` : `${aba}!A:Z`;

      await this.sheets.spreadsheets.values.clear({
        spreadsheetId: this.spreadsheetId,
        range,
      });

      console.log(`✓ Aba ${aba} limpa`);
      return true;
    } catch (error: any) {
      console.error(`✗ Erro ao limpar aba ${aba}:`, error.message);
      return false;
    }
  }

  /**
   * Cria cabeçalhos padrão para aba de voos
   */
  async criarCabecalhosVoos(): Promise<boolean> {
    const cabecalhos = [
      [
        'ID',
        'Data Identificação',
        'Data Verificação',
        'Status',
        'Origem',
        'Destino',
        'Companhia',
        'Data Ida',
        'Data Volta',
        'Passageiros',
        'Preço/Pessoa',
        'Preço Total',
        'Preço Referência',
        'Desconto %',
        'Economia',
        'Tipo Voo Ida',
        'Conexões Ida',
        'Conexões Volta',
        'Duração Ida',
        'Duração Volta',
        'Mudança Aeroporto',
        'Bagagem',
        'Tipo Bilhete',
        'Classificação Logística',
        'Score',
        'Link',
        'Alertas',
      ],
    ];

    return await this.escreverDados('VOOS_ATIVOS', cabecalhos, 1);
  }

  /**
   * Cria cabeçalhos padrão para aba de milhas
   */
  async criarCabecalhosMilhas(): Promise<boolean> {
    const cabecalhos = [
      [
        'ID',
        'Data Identificação',
        'Status',
        'Programa',
        'Tipo Promoção',
        'Descrição',
        'Qtd Base',
        'Bônus %',
        'Qtd Total',
        'Preço Total',
        'Custo/Milheiro',
        'Referência',
        'Economia/Milheiro',
        'Desconto %',
        'Elegibilidade',
        'Validade Promoção',
        'Validade Milhas',
        'Score',
        'Link',
      ],
    ];

    return await this.escreverDados('MILHAS_ATIVAS', cabecalhos, 1);
  }

  /**
   * Cria cabeçalhos padrão para aba de log
   */
  async criarCabecalhosLog(): Promise<boolean> {
    const cabecalhos = [
      [
        'ID Execução',
        'Data Início',
        'Data Fim',
        'Fontes Consultadas',
        'Ofertas Verificadas',
        'Ofertas Confirmadas',
        'Ofertas Expiradas',
        'Novas Oportunidades',
        'Falhas',
        'Status Planilha',
        'Status Dashboard',
      ],
    ];

    return await this.escreverDados('LOG_EXECUCOES', cabecalhos, 1);
  }

  /**
   * Inicializa todas as abas com cabeçalhos
   */
  async inicializarPlanilha(): Promise<boolean> {
    console.log('📋 Inicializando planilha com cabeçalhos...');

    try {
      await this.criarCabecalhosVoos();
      await this.criarCabecalhosMilhas();
      await this.criarCabecalhosLog();

      console.log('✓ Planilha inicializada com sucesso');
      return true;
    } catch (error: any) {
      console.error('✗ Erro ao inicializar planilha:', error.message);
      return false;
    }
  }
}
