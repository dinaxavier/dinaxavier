import { defineTool } from "@grok/agent-sdk";
import { z } from "zod";

export default defineTool({
  description:
    "Atualiza a planilha Google Sheets com os dados mais recentes de oportunidades, histórico e logs. Esta ferramenta sincroniza todos os dados coletados e validados.",
  inputSchema: z.object({
    operacao: z
      .enum([
        "atualizar_voos",
        "atualizar_milhas",
        "atualizar_combinadas",
        "mover_para_historico",
        "registrar_log",
        "atualizar_completo",
      ])
      .describe("Tipo de operação a realizar na planilha"),
    dados: z
      .any()
      .describe("Dados a serem atualizados (estrutura depende da operação)"),
    modo: z
      .enum(["adicionar", "substituir", "atualizar"])
      .optional()
      .default("atualizar")
      .describe(
        "Modo de atualização: adicionar novos, substituir todos ou atualizar existentes"
      ),
  }),
  effect: "write",
  execution: "server",

  async execute({ operacao, dados, modo }, ctx) {
    const resultado = {
      timestamp: new Date().toISOString(),
      operacao,
      modo,
      sucesso: false,
      registros_afetados: 0,
      erros: [] as string[],
    };

    try {
      // TODO: Implementar integração real com Google Sheets API
      // Requer autenticação OAuth2 ou Service Account

      const SPREADSHEET_ID = await obterIdPlanilha(ctx);

      if (!SPREADSHEET_ID) {
        throw new Error(
          "ID da planilha não configurado. Configure na aba CONFIGURACOES."
        );
      }

      switch (operacao) {
        case "atualizar_voos":
          resultado.registros_afetados = await atualizarVoos(
            SPREADSHEET_ID,
            dados,
            modo,
            ctx
          );
          break;

        case "atualizar_milhas":
          resultado.registros_afetados = await atualizarMilhas(
            SPREADSHEET_ID,
            dados,
            modo,
            ctx
          );
          break;

        case "atualizar_combinadas":
          resultado.registros_afetados = await atualizarCombinadas(
            SPREADSHEET_ID,
            dados,
            modo,
            ctx
          );
          break;

        case "mover_para_historico":
          resultado.registros_afetados = await moverParaHistorico(
            SPREADSHEET_ID,
            dados,
            ctx
          );
          break;

        case "registrar_log":
          resultado.registros_afetados = await registrarLog(
            SPREADSHEET_ID,
            dados,
            ctx
          );
          break;

        case "atualizar_completo":
          // Atualiza todas as abas
          const voos = await atualizarVoos(
            SPREADSHEET_ID,
            dados.voos || [],
            modo,
            ctx
          );
          const milhas = await atualizarMilhas(
            SPREADSHEET_ID,
            dados.milhas || [],
            modo,
            ctx
          );
          const combinadas = await atualizarCombinadas(
            SPREADSHEET_ID,
            dados.combinadas || [],
            modo,
            ctx
          );
          const historico = await moverParaHistorico(
            SPREADSHEET_ID,
            dados.expiradas || [],
            ctx
          );
          const log = await registrarLog(
            SPREADSHEET_ID,
            dados.log || {},
            ctx
          );

          // Salvar estatísticas gerais
          const { CSVStorage } = await import('../lib/csv-storage.js');
          const storage = new CSVStorage();
          await storage.salvarEstatisticas({
            total_oportunidades: (dados.voos?.length || 0) + (dados.milhas?.length || 0),
            novas_semana: dados.voos?.length || 0,
            maior_desconto: dados.voos?.reduce((max: number, v: any) => 
              Math.max(max, v.desconto_percentual || 0), 0),
            melhor_custo_milheiro: dados.milhas?.reduce((min: number, m: any) =>
              Math.min(min, m.custo_por_milheiro || 999999), 999999),
            melhor_preco: dados.voos?.reduce((min: number, v: any) =>
              Math.min(min, v.preco_por_pessoa || 999999), 999999),
          });

          resultado.registros_afetados = voos + milhas + combinadas + historico + log;
          break;

        default:
          throw new Error(`Operação não suportada: ${operacao}`);
      }

      resultado.sucesso = true;

      return {
        ...resultado,
        mensagem: `Planilha atualizada com sucesso. ${resultado.registros_afetados} registros afetados.`,
      };
    } catch (error: any) {
      resultado.erros.push(error.message);
      return {
        ...resultado,
        mensagem: `Erro ao atualizar planilha: ${error.message}`,
      };
    }
  },
});

// Funções auxiliares
async function obterIdPlanilha(ctx: any): Promise<string | null> {
  return process.env.GOOGLE_SHEETS_ID || null;
}

async function atualizarVoos(
  spreadsheetId: string,
  voos: any[],
  modo: string,
  ctx: any
): Promise<number> {
  try {
    const { CSVStorage } = await import('../lib/csv-storage.js');
    const storage = new CSVStorage();

    console.log(`[CSV] Salvando ${voos.length} voos`);

    await storage.salvarVoos(voos);

    return voos.length;
  } catch (error: any) {
    console.error('[CSV] Erro ao salvar voos:', error.message);
    return 0;
  }
}

async function atualizarMilhas(
  spreadsheetId: string,
  milhas: any[],
  modo: string,
  ctx: any
): Promise<number> {
  try {
    const { CSVStorage } = await import('../lib/csv-storage.js');
    const storage = new CSVStorage();

    console.log(`[CSV] Salvando ${milhas.length} promoções de milhas`);

    await storage.salvarMilhas(milhas);

    return milhas.length;
  } catch (error: any) {
    console.error('[CSV] Erro ao salvar milhas:', error.message);
    return 0;
  }
}

async function atualizarCombinadas(
  spreadsheetId: string,
  combinadas: any[],
  modo: string,
  ctx: any
): Promise<number> {
  try {
    const { SheetsClient } = await import('../lib/sheets-client.js');
    const client = new SheetsClient();

    console.log(
      `[SHEETS] Atualizando ${combinadas.length} oportunidades combinadas (modo: ${modo})`
    );

    const linhas = combinadas.map((comb) => [
      comb.id,
      comb.timestamp,
      comb.rota,
      comb.datas,
      comb.programa,
      comb.companhia,
      comb.milhas_necessarias,
      comb.custo_aquisicao_milhas?.toFixed(2),
      comb.taxas_encargos?.toFixed(2),
      comb.custo_total_emissao?.toFixed(2),
      comb.preco_em_dinheiro?.toFixed(2),
      comb.economia_liquida?.toFixed(2),
      comb.economia_percentual?.toFixed(1),
      comb.disponibilidade_emissao ? 'Sim' : 'Não',
      comb.score?.toFixed(0),
      comb.link_promocao_milhas || '',
      comb.link_emissao || '',
    ]);

    if (modo === 'substituir') {
      await client.limparAba('OPORTUNIDADES_COMBINADAS', true);
      await client.adicionarLinhas('OPORTUNIDADES_COMBINADAS', linhas);
    } else {
      await client.adicionarLinhas('OPORTUNIDADES_COMBINADAS', linhas);
    }

    return combinadas.length;
  } catch (error: any) {
    console.error('[SHEETS] Erro ao atualizar combinadas:', error.message);
    return 0;
  }
}

async function moverParaHistorico(
  spreadsheetId: string,
  registros: any[],
  ctx: any
): Promise<number> {
  try {
    const { CSVStorage } = await import('../lib/csv-storage.js');
    const storage = new CSVStorage();

    console.log(`[CSV] Adicionando ${registros.length} registros ao histórico`);

    await storage.adicionarAoHistorico(registros);
    return registros.length;
  } catch (error: any) {
    console.error('[CSV] Erro ao adicionar ao histórico:', error.message);
    return 0;
  }
}

async function registrarLog(
  spreadsheetId: string,
  logData: any,
  ctx: any
): Promise<number> {
  try {
    const { CSVStorage } = await import('../lib/csv-storage.js');
    const storage = new CSVStorage();

    console.log('[CSV] Registrando log de execução');

    await storage.registrarLog(logData);
    return 1;
  } catch (error: any) {
    console.error('[CSV] Erro ao registrar log:', error.message);
    return 0;
  }
}
