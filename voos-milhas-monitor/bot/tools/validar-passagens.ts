import { defineTool } from "@grok/agent-sdk";
import { z } from "zod";

export default defineTool({
  description:
    "Revalida todas as oportunidades de passagens aéreas existentes na planilha, verificando disponibilidade, preços e condições atuais. Use esta ferramenta no INÍCIO de cada execução semanal, antes de buscar novas oportunidades.",
  inputSchema: z.object({
    ids_oportunidades: z
      .array(z.string())
      .optional()
      .describe(
        "IDs específicos para validar. Se omitido, valida todas as oportunidades ativas."
      ),
    verificar_logistica: z
      .boolean()
      .optional()
      .default(true)
      .describe(
        "Se deve verificar também alterações no itinerário (conexões, horários, aeroportos)"
      ),
  }),
  effect: "read",
  execution: "server",

  async execute({ ids_oportunidades, verificar_logistica }, ctx) {
    // Esta ferramenta será implementada para integrar com:
    // 1. Leitura da planilha Google Sheets (aba VOOS_ATIVOS)
    // 2. APIs de busca de passagens (exemplo: Skyscanner, Google Flights, etc)
    // 3. Comparação de dados atuais vs. registrados

    const resultado = {
      timestamp: new Date().toISOString(),
      total_verificadas: 0,
      ativas: [] as any[],
      atualizadas: [] as any[],
      expiradas: [] as any[],
      inconclusivas: [] as any[],
      erros: [] as string[],
    };

    try {
      // TODO: Implementar integração real
      // Por enquanto, retorna estrutura de exemplo
      
      // 1. Buscar oportunidades da planilha via Google Sheets API
      const oportunidades = await buscarOportunidadesAtivas(
        ctx,
        ids_oportunidades
      );
      resultado.total_verificadas = oportunidades.length;

      // 2. Para cada oportunidade, verificar disponibilidade atual
      for (const oportunidade of oportunidades) {
        try {
          const statusAtual = await verificarDisponibilidadeVoo(
            oportunidade,
            verificar_logistica
          );

          if (statusAtual.disponivel && statusAtual.preco <= oportunidade.preco) {
            if (statusAtual.preco === oportunidade.preco && !statusAtual.alteracoes) {
              resultado.ativas.push({
                id: oportunidade.id,
                status: "ATIVA",
                preco_anterior: oportunidade.preco,
                preco_atual: statusAtual.preco,
              });
            } else {
              resultado.atualizadas.push({
                id: oportunidade.id,
                status: "ATUALIZADA",
                preco_anterior: oportunidade.preco,
                preco_atual: statusAtual.preco,
                alteracoes: statusAtual.alteracoes || [],
              });
            }
          } else if (!statusAtual.disponivel) {
            resultado.expiradas.push({
              id: oportunidade.id,
              status: "EXPIRADA",
              motivo: statusAtual.motivo || "Não disponível",
            });
          } else {
            resultado.expiradas.push({
              id: oportunidade.id,
              status: "EXPIRADA",
              motivo: `Preço aumentou de ${oportunidade.preco} para ${statusAtual.preco}`,
            });
          }
        } catch (error: any) {
          resultado.inconclusivas.push({
            id: oportunidade.id,
            status: "VERIFICAÇÃO_INCONCLUSIVA",
            erro: error.message,
          });
        }
      }

      // 3. Registrar resultado no log
      await registrarNoLog(ctx, "VALIDACAO", resultado);

      return {
        sucesso: true,
        ...resultado,
        mensagem: `Validação concluída: ${resultado.ativas.length} ativas, ${resultado.atualizadas.length} atualizadas, ${resultado.expiradas.length} expiradas, ${resultado.inconclusivas.length} inconclusivas`,
      };
    } catch (error: any) {
      resultado.erros.push(error.message);
      return {
        sucesso: false,
        ...resultado,
        mensagem: `Erro na validação: ${error.message}`,
      };
    }
  },
});

// Funções auxiliares
async function buscarOportunidadesAtivas(ctx: any, ids?: string[]): Promise<any[]> {
  try {
    const { SheetsClient } = await import('../lib/sheets-client.js');
    const client = new SheetsClient();

    const dados = await client.lerDadosComoObjetos('VOOS_ATIVOS');

    if (!ids || ids.length === 0) {
      return dados;
    }

    return dados.filter((d: any) => ids.includes(d.ID || d.id));
  } catch (error: any) {
    console.error('✗ Erro ao buscar oportunidades:', error.message);
    return [];
  }
}

async function verificarDisponibilidadeVoo(oportunidade: any, verificarLogistica: boolean) {
  try {
    // Buscar voo similar na API
    const { KiwiClient } = await import('../lib/kiwi-client.js');
    const client = new KiwiClient();

    const origem = oportunidade.Origem || oportunidade.origem;
    const destino = oportunidade.Destino || oportunidade.destino;
    const dataIda = oportunidade['Data Ida'] || oportunidade.data_ida;
    const dataVolta = oportunidade['Data Volta'] || oportunidade.data_volta;

    if (!origem || !destino || !dataIda) {
      return {
        disponivel: false,
        preco: 0,
        alteracoes: null,
        motivo: 'Dados incompletos',
      };
    }

    // Buscar voo nas datas específicas (janela de 2 dias)
    const voos = await client.buscarVoos({
      origens: [origem],
      destinos: [destino],
      dataIdaInicio: dataIda,
      dataIdaFim: dataIda,
      dataVoltaInicio: dataVolta || undefined,
      dataVoltaFim: dataVolta || undefined,
      passageiros: 1,
      maxConexoes: 3,
      limite: 20,
    });

    if (voos.length === 0) {
      return {
        disponivel: false,
        preco: 0,
        alteracoes: null,
        motivo: 'Voo não encontrado',
      };
    }

    // Encontrar voo mais similar
    const precoOriginal = parseFloat(
      oportunidade['Preço/Pessoa'] || oportunidade.preco_por_pessoa || '0'
    );
    const vooSimilar = voos[0]; // Pegar o mais barato

    const diferencaPreco = vooSimilar.preco_por_pessoa - precoOriginal;
    const diferencaPercentual = (diferencaPreco / precoOriginal) * 100;

    return {
      disponivel: true,
      preco: vooSimilar.preco_por_pessoa,
      alteracoes:
        Math.abs(diferencaPercentual) > 5
          ? [`Preço mudou ${diferencaPercentual > 0 ? '+' : ''}${diferencaPercentual.toFixed(1)}%`]
          : null,
      motivo: null,
    };
  } catch (error: any) {
    console.error('✗ Erro ao verificar disponibilidade:', error.message);
    return {
      disponivel: false,
      preco: 0,
      alteracoes: null,
      motivo: `Erro: ${error.message}`,
    };
  }
}

async function registrarNoLog(ctx: any, tipo: string, dados: any) {
  console.log(`[${tipo}]`, JSON.stringify(dados, null, 2));
  // Log também fica salvo no ctx.host.kv
  await ctx.host.kv.put(`log:${tipo}:${Date.now()}`, dados);
}
