import { defineTool } from "@grok/agent-sdk";
import { z } from "zod";

export default defineTool({
  description:
    "Busca novas oportunidades de passagens aéreas com base nos parâmetros configurados. Coleta dados completos incluindo informações logísticas detalhadas (conexões, durações, tipo de voo). Use APÓS validar as oportunidades existentes.",
  inputSchema: z.object({
    origens: z
      .array(z.string())
      .describe("Códigos IATA dos aeroportos de origem (ex: ['GRU', 'CGH'])"),
    destinos: z
      .array(z.string())
      .describe("Códigos IATA dos aeroportos de destino (ex: ['CDG', 'BCN'])"),
    data_ida_inicio: z
      .string()
      .describe("Data inicial para ida no formato YYYY-MM-DD"),
    data_ida_fim: z
      .string()
      .describe("Data final para ida no formato YYYY-MM-DD"),
    data_volta_inicio: z
      .string()
      .optional()
      .describe("Data inicial para volta no formato YYYY-MM-DD (somente ida/volta)"),
    data_volta_fim: z
      .string()
      .optional()
      .describe("Data final para volta no formato YYYY-MM-DD (somente ida/volta)"),
    passageiros: z
      .number()
      .int()
      .positive()
      .default(1)
      .describe("Número de passageiros"),
    preco_maximo: z
      .number()
      .positive()
      .optional()
      .describe("Preço máximo aceitável por pessoa"),
    desconto_minimo: z
      .number()
      .min(0)
      .max(100)
      .default(15)
      .describe("Desconto mínimo percentual para considerar oportunidade (%)"),
    voo_direto_preferencial: z
      .boolean()
      .optional()
      .default(false)
      .describe("Priorizar voos diretos"),
    max_conexoes: z
      .number()
      .int()
      .min(0)
      .max(3)
      .optional()
      .describe("Número máximo de conexões permitido"),
    aceitar_mudanca_aeroporto: z
      .boolean()
      .optional()
      .default(false)
      .describe("Aceitar itinerários com mudança de aeroporto"),
  }),
  effect: "read",
  execution: "server",

  async execute(params, ctx) {
    const resultado = {
      timestamp: new Date().toISOString(),
      parametros: params,
      total_encontradas: 0,
      oportunidades: [] as any[],
      referencias_historicas: {} as Record<string, number>,
      erros: [] as string[],
    };

    try {
      // TODO: Implementar integração real com APIs de busca
      // Exemplos de APIs: Skyscanner, Google Flights, Amadeus, Kiwi.com
      
      // 1. Buscar preços históricos para cada rota
      for (const origem of params.origens) {
        for (const destino of params.destinos) {
          const chaveRota = `${origem}-${destino}`;
          resultado.referencias_historicas[chaveRota] = await buscarPrecoHistorico(
            origem,
            destino,
            ctx
          );
        }
      }

      // 2. Buscar voos disponíveis
      const voosEncontrados = await buscarVoosDisponiveis(params);
      resultado.total_encontradas = voosEncontrados.length;

      // 3. Analisar cada voo
      for (const voo of voosEncontrados) {
        const chaveRota = `${voo.origem}-${voo.destino}`;
        const precoReferencia = resultado.referencias_historicas[chaveRota];

        if (!precoReferencia) {
          resultado.erros.push(
            `Sem referência histórica para ${chaveRota}`
          );
          continue;
        }

        // Calcular economia
        const economia = precoReferencia - voo.preco_total / params.passageiros;
        const descontoPercentual = (economia / precoReferencia) * 100;

        // Verificar se atende critérios mínimos
        if (descontoPercentual < params.desconto_minimo) {
          continue;
        }

        if (params.preco_maximo && voo.preco_total / params.passageiros > params.preco_maximo) {
          continue;
        }

        // Análise logística
        const analiseLogistica = analisarLogistica(voo, params);

        // Calcular score composto (preço + logística)
        const scorePreco = Math.min(descontoPercentual / 50 * 100, 100);
        const scoreLogistica = analiseLogistica.score;
        const scoreFinal = (scorePreco * 0.6) + (scoreLogistica * 0.4);

        const oportunidade = {
          id: gerarIdOportunidade(voo),
          timestamp: resultado.timestamp,
          origem: voo.origem,
          destino: voo.destino,
          data_ida: voo.data_ida,
          data_volta: voo.data_volta,
          companhia: voo.companhia,
          preco_por_pessoa: voo.preco_total / params.passageiros,
          preco_total: voo.preco_total,
          preco_referencia: precoReferencia,
          economia_estimada: economia * params.passageiros,
          desconto_percentual: descontoPercentual,
          
          // Dados logísticos
          tipo_voo_ida: voo.tipo_voo_ida,
          tipo_voo_volta: voo.tipo_voo_volta,
          conexoes_ida: voo.conexoes_ida || [],
          conexoes_volta: voo.conexoes_volta || [],
          duracao_total_ida: voo.duracao_total_ida,
          duracao_total_volta: voo.duracao_total_volta,
          tempo_voo_ida: voo.tempo_voo_ida,
          tempo_voo_volta: voo.tempo_voo_volta,
          mudanca_aeroporto: analiseLogistica.mudanca_aeroporto,
          
          // Avaliação
          classificacao_logistica: analiseLogistica.classificacao,
          alertas_logisticos: analiseLogistica.alertas,
          score: scoreFinal,
          
          // Extras
          bagagem_incluida: voo.bagagem_incluida,
          tipo_bilhete: voo.tipo_bilhete,
          link: voo.link,
        };

        resultado.oportunidades.push(oportunidade);
      }

      // 4. Ordenar por score
      resultado.oportunidades.sort((a, b) => b.score - a.score);

      // 5. Registrar no log
      await registrarNoLog(ctx, "BUSCA_VOOS", {
        parametros: params,
        encontradas: resultado.total_encontradas,
        oportunidades: resultado.oportunidades.length,
      });

      return {
        sucesso: true,
        ...resultado,
        mensagem: `Busca concluída: ${resultado.oportunidades.length} oportunidades encontradas de ${resultado.total_encontradas} voos analisados`,
      };
    } catch (error: any) {
      resultado.erros.push(error.message);
      return {
        sucesso: false,
        ...resultado,
        mensagem: `Erro na busca: ${error.message}`,
      };
    }
  },
});

// Funções auxiliares
async function buscarPrecoHistorico(origem: string, destino: string, ctx: any): Promise<number> {
  try {
    // Importar SheetsClient dinamicamente
    const { SheetsClient } = await import('../lib/sheets-client.js');
    const client = new SheetsClient();

    // Buscar histórico da planilha
    const historico = await client.lerDadosComoObjetos('HISTORICO');

    // Filtrar por rota nos últimos 90 dias
    const data90DiasAtras = new Date();
    data90DiasAtras.setDate(data90DiasAtras.getDate() - 90);

    const rotaHistorico = historico.filter((linha: any) => {
      const origemMatch = linha.Origem === origem || linha.origem === origem;
      const destinoMatch = linha.Destino === destino || linha.destino === destino;
      const dataVoo = new Date(linha['Data Identificação'] || linha.timestamp);
      return origemMatch && destinoMatch && dataVoo >= data90DiasAtras;
    });

    if (rotaHistorico.length === 0) {
      console.log(`ℹ Sem histórico para ${origem}-${destino}, usando valor médio`);
      return 3000; // Valor médio estimado em BRL
    }

    // Calcular mediana dos preços
    const precos = rotaHistorico
      .map((linha: any) => parseFloat(linha['Preço/Pessoa'] || linha.preco_por_pessoa || 0))
      .filter((p: number) => p > 0)
      .sort((a: number, b: number) => a - b);

    const meio = Math.floor(precos.length / 2);
    const mediana =
      precos.length % 2 === 0
        ? (precos[meio - 1] + precos[meio]) / 2
        : precos[meio];

    console.log(
      `📊 Preço histórico ${origem}-${destino}: R$ ${mediana.toFixed(2)} (${precos.length} registros)`
    );
    return mediana;
  } catch (error: any) {
    console.warn(`⚠ Erro ao buscar histórico:`, error.message);
    return 3000; // Fallback
  }
}

async function buscarVoosDisponiveis(params: any): Promise<any[]> {
  try {
    // Importar KiwiClient dinamicamente
    const { KiwiClient } = await import('../lib/kiwi-client.js');
    const client = new KiwiClient();

    // Buscar voos
    const voos = await client.buscarVoos({
      origens: params.origens,
      destinos: params.destinos,
      dataIdaInicio: params.data_ida_inicio,
      dataIdaFim: params.data_ida_fim,
      dataVoltaInicio: params.data_volta_inicio,
      dataVoltaFim: params.data_volta_fim,
      passageiros: params.passageiros,
      maxConexoes: params.max_conexoes,
      limite: 100,
    });

    return voos;
  } catch (error: any) {
    console.error('✗ Erro ao buscar voos:', error.message);
    return [];
  }
}

function analisarLogistica(voo: any, params: any) {
  let score = 100;
  const alertas: string[] = [];
  let classificacao = "Excelente";
  let mudancaAeroporto = false;

  // Analisar conexões
  const totalConexoes = (voo.conexoes_ida?.length || 0) + (voo.conexoes_volta?.length || 0);

  if (totalConexoes === 0) {
    // Voo direto - excelente
    score = 100;
    classificacao = "Excelente";
  } else if (totalConexoes === 1) {
    score = 80;
    classificacao = "Boa";
  } else if (totalConexoes === 2) {
    score = 60;
    classificacao = "Moderada";
    alertas.push("Múltiplas conexões");
  } else {
    score = 40;
    classificacao = "Atenção";
    alertas.push("Muitas conexões");
  }

  // Verificar mudança de aeroporto
  const todasConexoes = [...(voo.conexoes_ida || []), ...(voo.conexoes_volta || [])];
  for (const conexao of todasConexoes) {
    if (conexao.mudanca_aeroporto) {
      mudancaAeroporto = true;
      score -= 25;
      classificacao = "Atenção";
      alertas.push(`Mudança de aeroporto em ${conexao.cidade}`);
    }

    // Conexão muito curta (< 1h)
    if (conexao.tempo_conexao_minutos < 60) {
      score -= 15;
      alertas.push(`Conexão curta em ${conexao.cidade} (${conexao.tempo_conexao_minutos}min)`);
    }

    // Conexão muito longa (> 6h)
    if (conexao.tempo_conexao_minutos > 360) {
      score -= 10;
      alertas.push(`Conexão longa em ${conexao.cidade} (${Math.floor(conexao.tempo_conexao_minutos / 60)}h)`);
    }

    // Troca de companhia
    if (conexao.troca_companhia) {
      score -= 10;
      alertas.push(`Troca de companhia em ${conexao.cidade}`);
    }
  }

  // Verificar parâmetros do usuário
  if (params.max_conexoes !== undefined && totalConexoes > params.max_conexoes) {
    score = 0; // Desqualifica
  }

  if (!params.aceitar_mudanca_aeroporto && mudancaAeroporto) {
    score = 0; // Desqualifica
  }

  return {
    score: Math.max(0, score),
    classificacao,
    alertas,
    mudanca_aeroporto: mudancaAeroporto,
  };
}

function gerarIdOportunidade(voo: any): string {
  const timestamp = Date.now();
  const hash = `${voo.origem}${voo.destino}${voo.data_ida}${timestamp}`.slice(0, 16);
  return `VOO_${hash}`;
}

async function registrarNoLog(ctx: any, tipo: string, dados: any) {
  console.log(`[${tipo}]`, JSON.stringify(dados, null, 2));
}
