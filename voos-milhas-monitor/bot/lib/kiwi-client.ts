import axios from 'axios';

/**
 * Cliente para integração com Kiwi.com API
 * Busca passagens aéreas e informações de voos
 */
export class KiwiClient {
  private apiKey: string;
  private baseURL: string = 'https://api.tequila.kiwi.com/v2';

  constructor() {
    const apiKey = process.env.KIWI_API_KEY;

    if (!apiKey) {
      throw new Error('KIWI_API_KEY não configurada. Configure no .env');
    }

    this.apiKey = apiKey;
  }

  /**
   * Testa a conexão com a API
   */
  async testarConexao(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.baseURL}/locations/query`, {
        params: { term: 'GRU', locale: 'pt-BR' },
        headers: { apikey: this.apiKey },
      });

      console.log('✓ Conexão com Kiwi API OK');
      return true;
    } catch (error: any) {
      console.error('✗ Erro ao conectar com Kiwi API:', error.message);
      return false;
    }
  }

  /**
   * Busca passagens aéreas
   */
  async buscarVoos(parametros: {
    origens: string[];
    destinos: string[];
    dataIdaInicio: string;
    dataIdaFim: string;
    dataVoltaInicio?: string;
    dataVoltaFim?: string;
    passageiros: number;
    maxConexoes?: number;
    limite?: number;
  }): Promise<any[]> {
    try {
      const {
        origens,
        destinos,
        dataIdaInicio,
        dataIdaFim,
        dataVoltaInicio,
        dataVoltaFim,
        passageiros,
        maxConexoes = 2,
        limite = 50,
      } = parametros;

      // Formatar datas (dd/mm/yyyy)
      const formatarData = (data: string) => {
        const [ano, mes, dia] = data.split('-');
        return `${dia}/${mes}/${ano}`;
      };

      const queryParams: any = {
        fly_from: origens.join(','),
        fly_to: destinos.join(','),
        date_from: formatarData(dataIdaInicio),
        date_to: formatarData(dataIdaFim),
        adults: passageiros,
        curr: 'BRL',
        locale: 'pt',
        max_stopovers: maxConexoes,
        limit: limite,
        sort: 'price',
      };

      // Adicionar datas de volta se for ida e volta
      if (dataVoltaInicio && dataVoltaFim) {
        queryParams.return_from = formatarData(dataVoltaInicio);
        queryParams.return_to = formatarData(dataVoltaFim);
      }

      console.log(
        `🔍 Buscando voos: ${origens.join(',')} → ${destinos.join(',')}`
      );

      const response = await axios.get(`${this.baseURL}/search`, {
        params: queryParams,
        headers: { apikey: this.apiKey },
        timeout: 30000, // 30 segundos
      });

      const voos = response.data.data || [];
      console.log(`✓ Encontrados ${voos.length} voos`);

      return this.processarVoos(voos, passageiros);
    } catch (error: any) {
      if (error.response) {
        console.error('✗ Erro API Kiwi:', error.response.status, error.response.data);
      } else {
        console.error('✗ Erro ao buscar voos:', error.message);
      }
      return [];
    }
  }

  /**
   * Processa e formata dados dos voos
   */
  private processarVoos(voosRaw: any[], passageiros: number): any[] {
    return voosRaw.map((voo) => {
      // Separar rotas de ida e volta
      const rotaIda = voo.route.filter((r: any) => r.return === 0);
      const rotaVolta = voo.route.filter((r: any) => r.return === 1);

      // Analisar conexões
      const analisarConexoes = (rota: any[]) => {
        const conexoes = [];
        for (let i = 0; i < rota.length - 1; i++) {
          const atual = rota[i];
          const proximo = rota[i + 1];

          const chegada = new Date(atual.local_arrival);
          const partida = new Date(proximo.local_departure);
          const tempoConexao = Math.floor((partida.getTime() - chegada.getTime()) / 60000);

          conexoes.push({
            aeroporto_chegada: atual.flyTo,
            cidade_chegada: atual.cityTo,
            aeroporto_partida: proximo.flyFrom,
            cidade_partida: proximo.cityFrom,
            horario_chegada: atual.local_arrival,
            horario_partida: proximo.local_departure,
            tempo_conexao_minutos: tempoConexao,
            companhia: proximo.airline,
            troca_companhia: atual.airline !== proximo.airline,
            mudanca_aeroporto: atual.flyTo !== proximo.flyFrom,
          });
        }
        return conexoes;
      };

      const conexoesIda = analisarConexoes(rotaIda);
      const conexoesVolta = analisarConexoes(rotaVolta);

      // Verificar mudança de aeroporto
      const temMudancaAeroporto =
        conexoesIda.some((c) => c.mudanca_aeroporto) ||
        conexoesVolta.some((c) => c.mudanca_aeroporto);

      // Formatar duração
      const formatarDuracao = (minutos: number) => {
        const horas = Math.floor(minutos / 60);
        const mins = minutos % 60;
        return `${horas}h${mins > 0 ? mins.toString().padStart(2, '0') + 'm' : ''}`;
      };

      return {
        id_kiwi: voo.id,
        origem: voo.flyFrom,
        cidade_origem: voo.cityFrom,
        destino: voo.flyTo,
        cidade_destino: voo.cityTo,
        data_ida: voo.local_departure,
        data_volta: voo.local_arrival,
        companhia: voo.airlines?.join(', ') || 'Múltiplas',
        preco_total: voo.price,
        preco_por_pessoa: voo.price / passageiros,

        // Tipo de voo
        tipo_voo_ida:
          rotaIda.length === 1
            ? 'Direto'
            : rotaIda.length === 2
            ? '1 Conexão'
            : `${rotaIda.length - 1} Conexões`,
        tipo_voo_volta:
          rotaVolta.length === 0
            ? null
            : rotaVolta.length === 1
            ? 'Direto'
            : rotaVolta.length === 2
            ? '1 Conexão'
            : `${rotaVolta.length - 1} Conexões`,

        // Conexões
        conexoes_ida: conexoesIda,
        conexoes_volta: conexoesVolta,
        total_conexoes: conexoesIda.length + conexoesVolta.length,

        // Durações
        duracao_total_ida: formatarDuracao(
          rotaIda.reduce((acc: number, r: any) => acc + (r.duration?.total || 0), 0)
        ),
        duracao_total_volta:
          rotaVolta.length > 0
            ? formatarDuracao(
                rotaVolta.reduce((acc: number, r: any) => acc + (r.duration?.total || 0), 0)
              )
            : null,
        tempo_voo_ida: formatarDuracao(voo.duration?.departure || 0),
        tempo_voo_volta: formatarDuracao(voo.duration?.return || 0),

        // Logística
        mudanca_aeroporto: temMudancaAeroporto,
        voo_direto: rotaIda.length === 1 && rotaVolta.length <= 1,

        // Extras
        bagagem_incluida: this.analisarBagagem(voo),
        disponibilidade: voo.availability?.seats || null,
        deep_link: voo.deep_link,

        // Dados brutos para referência
        dados_brutos: {
          booking_token: voo.booking_token,
          quality: voo.quality,
        },
      };
    });
  }

  /**
   * Analisa informações de bagagem
   */
  private analisarBagagem(voo: any): string {
    const bagLimit = voo.baglimit;

    if (!bagLimit) {
      return 'Verificar no site';
    }

    const partes: string[] = [];

    if (bagLimit.hand_weight) {
      partes.push(`Mão: ${bagLimit.hand_weight}kg`);
    }
    if (bagLimit.hold_weight) {
      partes.push(`Despachada: ${bagLimit.hold_weight}kg`);
    }

    return partes.length > 0 ? partes.join(' | ') : 'Verificar no site';
  }
}
