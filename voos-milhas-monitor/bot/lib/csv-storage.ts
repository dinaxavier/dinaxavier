import * as fs from 'fs';
import * as path from 'path';

/**
 * Cliente simples para armazenamento em CSV
 * Substitui Google Sheets por arquivos CSV locais
 */
export class CSVStorage {
  private dataDir: string;

  constructor(dataDir?: string) {
    // Usar diretório configurável ou padrão
    this.dataDir = dataDir || process.env.CSV_DATA_DIR || './data';
    
    // Criar diretório se não existe
    if (!fs.existsSync(this.dataDir)) {
      fs.mkdirSync(this.dataDir, { recursive: true });
      console.log(`✓ Diretório de dados criado: ${this.dataDir}`);
    }
  }

  /**
   * Salva oportunidades de voos em CSV
   */
  async salvarVoos(voos: any[]): Promise<boolean> {
    try {
      const arquivo = path.join(this.dataDir, 'voos_ativos.csv');
      
      if (voos.length === 0) {
        console.log('⚠ Nenhum voo para salvar');
        return true;
      }

      // Cabeçalhos
      const cabecalhos = [
        'id',
        'timestamp',
        'origem',
        'destino',
        'cidade_origem',
        'cidade_destino',
        'companhia',
        'data_ida',
        'data_volta',
        'preco_por_pessoa',
        'preco_total',
        'preco_referencia',
        'desconto_percentual',
        'economia_estimada',
        'tipo_voo_ida',
        'tipo_voo_volta',
        'total_conexoes',
        'duracao_total_ida',
        'duracao_total_volta',
        'mudanca_aeroporto',
        'classificacao_logistica',
        'score',
        'bagagem_incluida',
        'link',
      ];

      // Converter dados para linhas CSV
      const linhas = voos.map((voo) => {
        return [
          this.escaparCSV(voo.id || ''),
          this.escaparCSV(voo.timestamp || new Date().toISOString()),
          this.escaparCSV(voo.origem || ''),
          this.escaparCSV(voo.destino || ''),
          this.escaparCSV(voo.cidade_origem || ''),
          this.escaparCSV(voo.cidade_destino || ''),
          this.escaparCSV(voo.companhia || ''),
          this.escaparCSV(voo.data_ida || ''),
          this.escaparCSV(voo.data_volta || ''),
          voo.preco_por_pessoa?.toFixed(2) || '0',
          voo.preco_total?.toFixed(2) || '0',
          voo.preco_referencia?.toFixed(2) || '0',
          voo.desconto_percentual?.toFixed(1) || '0',
          voo.economia_estimada?.toFixed(2) || '0',
          this.escaparCSV(voo.tipo_voo_ida || ''),
          this.escaparCSV(voo.tipo_voo_volta || ''),
          voo.total_conexoes || 0,
          this.escaparCSV(voo.duracao_total_ida || ''),
          this.escaparCSV(voo.duracao_total_volta || ''),
          voo.mudanca_aeroporto ? 'Sim' : 'Não',
          this.escaparCSV(voo.classificacao_logistica || 'Boa'),
          voo.score?.toFixed(0) || '0',
          this.escaparCSV(voo.bagagem_incluida || ''),
          this.escaparCSV(voo.link || ''),
        ].join(',');
      });

      // Montar CSV completo
      const csv = [cabecalhos.join(','), ...linhas].join('\n');

      // Salvar arquivo
      fs.writeFileSync(arquivo, csv, 'utf-8');
      console.log(`✓ Salvos ${voos.length} voos em ${arquivo}`);

      return true;
    } catch (error: any) {
      console.error('✗ Erro ao salvar voos em CSV:', error.message);
      return false;
    }
  }

  /**
   * Salva promoções de milhas em CSV
   */
  async salvarMilhas(milhas: any[]): Promise<boolean> {
    try {
      const arquivo = path.join(this.dataDir, 'milhas_ativas.csv');

      if (milhas.length === 0) {
        console.log('⚠ Nenhuma promoção de milhas para salvar');
        return true;
      }

      const cabecalhos = [
        'id',
        'timestamp',
        'programa',
        'tipo_promocao',
        'descricao',
        'custo_por_milheiro',
        'bonus_percentual',
        'desconto_percentual',
        'score',
        'validade_promocao',
        'link',
      ];

      const linhas = milhas.map((milha) => {
        return [
          this.escaparCSV(milha.id || ''),
          this.escaparCSV(milha.timestamp || new Date().toISOString()),
          this.escaparCSV(milha.programa || ''),
          this.escaparCSV(milha.tipo_promocao || ''),
          this.escaparCSV(milha.descricao || ''),
          (milha.custo_por_milheiro / 100)?.toFixed(2) || '0',
          milha.bonus_percentual || '0',
          milha.desconto_percentual?.toFixed(1) || '0',
          milha.score?.toFixed(0) || '0',
          this.escaparCSV(milha.validade_promocao || ''),
          this.escaparCSV(milha.link_oficial || ''),
        ].join(',');
      });

      const csv = [cabecalhos.join(','), ...linhas].join('\n');
      fs.writeFileSync(arquivo, csv, 'utf-8');
      console.log(`✓ Salvas ${milhas.length} promoções em ${arquivo}`);

      return true;
    } catch (error: any) {
      console.error('✗ Erro ao salvar milhas em CSV:', error.message);
      return false;
    }
  }

  /**
   * Adiciona ao histórico (append mode)
   */
  async adicionarAoHistorico(registros: any[]): Promise<boolean> {
    try {
      const arquivo = path.join(this.dataDir, 'historico.csv');

      // Verificar se arquivo existe
      const existe = fs.existsSync(arquivo);

      const cabecalhos = [
        'id',
        'timestamp',
        'tipo',
        'origem',
        'destino',
        'preco',
        'status',
        'motivo',
      ];

      const linhas = registros.map((reg) => {
        return [
          this.escaparCSV(reg.id || ''),
          this.escaparCSV(new Date().toISOString()),
          this.escaparCSV(reg.tipo || 'voo'),
          this.escaparCSV(reg.origem || ''),
          this.escaparCSV(reg.destino || ''),
          reg.preco || '0',
          this.escaparCSV(reg.status || 'EXPIRADA'),
          this.escaparCSV(reg.motivo || ''),
        ].join(',');
      });

      // Se arquivo não existe, adicionar cabeçalho
      let conteudo = existe ? '' : cabecalhos.join(',') + '\n';
      conteudo += linhas.join('\n') + '\n';

      fs.appendFileSync(arquivo, conteudo, 'utf-8');
      console.log(`✓ Adicionados ${registros.length} registros ao histórico`);

      return true;
    } catch (error: any) {
      console.error('✗ Erro ao adicionar ao histórico:', error.message);
      return false;
    }
  }

  /**
   * Registra log de execução
   */
  async registrarLog(logData: any): Promise<boolean> {
    try {
      const arquivo = path.join(this.dataDir, 'logs.csv');
      const existe = fs.existsSync(arquivo);

      const cabecalhos = [
        'execucao_id',
        'data_hora',
        'ofertas_verificadas',
        'ofertas_confirmadas',
        'novas_oportunidades',
        'status',
      ];

      const linha = [
        this.escaparCSV(logData.execucao_id || ''),
        this.escaparCSV(logData.inicio || new Date().toISOString()),
        logData.ofertas_verificadas || 0,
        logData.ofertas_confirmadas || 0,
        logData.novas_oportunidades || 0,
        this.escaparCSV(logData.status || 'OK'),
      ].join(',');

      let conteudo = existe ? '' : cabecalhos.join(',') + '\n';
      conteudo += linha + '\n';

      fs.appendFileSync(arquivo, conteudo, 'utf-8');
      console.log('✓ Log registrado');

      return true;
    } catch (error: any) {
      console.error('✗ Erro ao registrar log:', error.message);
      return false;
    }
  }

  /**
   * Salva estatísticas gerais
   */
  async salvarEstatisticas(stats: any): Promise<boolean> {
    try {
      const arquivo = path.join(this.dataDir, 'estatisticas.json');
      
      const dados = {
        ultima_atualizacao: new Date().toISOString(),
        total_oportunidades: stats.total_oportunidades || 0,
        novas_semana: stats.novas_semana || 0,
        maior_desconto: stats.maior_desconto || 0,
        melhor_custo_milheiro: stats.melhor_custo_milheiro || 0,
        melhor_preco: stats.melhor_preco || 0,
      };

      fs.writeFileSync(arquivo, JSON.stringify(dados, null, 2), 'utf-8');
      console.log('✓ Estatísticas salvas');

      return true;
    } catch (error: any) {
      console.error('✗ Erro ao salvar estatísticas:', error.message);
      return false;
    }
  }

  /**
   * Lê arquivo CSV (para o Streamlit)
   */
  lerCSV(nomeArquivo: string): string | null {
    try {
      const arquivo = path.join(this.dataDir, nomeArquivo);
      
      if (!fs.existsSync(arquivo)) {
        console.log(`⚠ Arquivo não encontrado: ${arquivo}`);
        return null;
      }

      return fs.readFileSync(arquivo, 'utf-8');
    } catch (error: any) {
      console.error(`✗ Erro ao ler ${nomeArquivo}:`, error.message);
      return null;
    }
  }

  /**
   * Escapa valores para CSV (lida com vírgulas e aspas)
   */
  private escaparCSV(valor: string): string {
    if (typeof valor !== 'string') {
      valor = String(valor);
    }

    // Se contém vírgula, aspas ou quebra de linha, envolve em aspas
    if (valor.includes(',') || valor.includes('"') || valor.includes('\n')) {
      // Duplica aspas internas
      valor = valor.replace(/"/g, '""');
      return `"${valor}"`;
    }

    return valor;
  }

  /**
   * Retorna caminho do diretório de dados
   */
  getCaminhoDados(): string {
    return path.resolve(this.dataDir);
  }
}
