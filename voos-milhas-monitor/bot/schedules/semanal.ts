import { defineSchedule } from "@grok/agent-sdk";

export default defineSchedule({
  // Executa toda segunda-feira às 09:00 (horário UTC)
  // Para horário de Brasília (UTC-3), isso será às 06:00
  cron: "0 9 * * 1",

  async run(ctx) {
    // Fluxo de execução semanal completo
    const execucaoId = `EXEC_${Date.now()}`;
    const inicio = new Date().toISOString();

    console.log(`\n[${execucaoId}] ===== INICIANDO EXECUÇÃO SEMANAL =====`);
    console.log(`[${execucaoId}] Horário: ${inicio}`);

    const resultados = {
      execucao_id: execucaoId,
      inicio,
      fim: null as string | null,
      validacao: null as any,
      busca_voos: null as any,
      busca_milhas: null as any,
      atualizacao_planilha: null as any,
      envio_email: null as any,
      erros: [] as string[],
    };

    try {
      // 1. REVALIDAR OPORTUNIDADES EXISTENTES
      console.log(`[${execucaoId}] Etapa 1: Revalidando oportunidades existentes...`);
      try {
        resultados.validacao = await ctx.callTool("validar_passagens", {
          verificar_logistica: true,
        });
        console.log(
          `[${execucaoId}] ✓ Validação concluída: ${resultados.validacao.mensagem}`
        );
      } catch (error: any) {
        const erro = `Erro na validação: ${error.message}`;
        resultados.erros.push(erro);
        console.error(`[${execucaoId}] ✗ ${erro}`);
      }

      // 2. BUSCAR NOVAS PASSAGENS
      console.log(`[${execucaoId}] Etapa 2: Buscando novas passagens...`);
      try {
        // Ler configurações da planilha ou usar padrões
        const config = await obterConfiguracoes(ctx);

        const oportunidades: any[] = [];
        const mensagens: string[] = [];

        for (const grupo of config.grupos_rotas) {
          console.log(
            `[${execucaoId}] Buscando ${grupo.nome}: ${grupo.origens.join(",")} → ${grupo.destinos.join(",")}`
          );
          const busca: any = await ctx.callTool("buscar_voos", {
            origens: grupo.origens,
            destinos: grupo.destinos,
            data_ida_inicio: config.data_ida_inicio || getDataFutura(30),
            data_ida_fim: config.data_ida_fim || getDataFutura(180),
            data_volta_inicio: config.data_volta_inicio || getDataFutura(37),
            data_volta_fim: config.data_volta_fim || getDataFutura(187),
            passageiros: config.passageiros || 1,
            preco_maximo: config.preco_maximo,
            desconto_minimo: config.desconto_minimo || 15,
            voo_direto_preferencial: config.voo_direto_preferencial || false,
            max_conexoes: config.max_conexoes,
            aceitar_mudanca_aeroporto: config.aceitar_mudanca_aeroporto || false,
          });
          oportunidades.push(...(busca?.oportunidades || []));
          if (busca?.mensagem) mensagens.push(busca.mensagem);
        }

        resultados.busca_voos = {
          oportunidades,
          mensagem: mensagens.join(" | "),
        };
        console.log(
          `[${execucaoId}] ✓ Busca de voos concluída: ${resultados.busca_voos.mensagem}`
        );
      } catch (error: any) {
        const erro = `Erro na busca de voos: ${error.message}`;
        resultados.erros.push(erro);
        console.error(`[${execucaoId}] ✗ ${erro}`);
      }

      // 3. BUSCAR PROMOÇÕES DE MILHAS
      console.log(`[${execucaoId}] Etapa 3: Buscando promoções de milhas...`);
      try {
        const config = await obterConfiguracoes(ctx);

        resultados.busca_milhas = await ctx.callTool("buscar_milhas", {
          programas: config.programas_milhas,
          custo_maximo_milheiro: config.custo_maximo_milheiro,
          desconto_minimo: config.desconto_minimo_milhas || 10,
        });
        console.log(
          `[${execucaoId}] ✓ Busca de milhas concluída: ${resultados.busca_milhas.mensagem}`
        );
      } catch (error: any) {
        const erro = `Erro na busca de milhas: ${error.message}`;
        resultados.erros.push(erro);
        console.error(`[${execucaoId}] ✗ ${erro}`);
      }

      // 4. ATUALIZAR PLANILHA
      console.log(`[${execucaoId}] Etapa 4: Atualizando planilha...`);
      try {
        const dadosAtualizacao = {
          voos: resultados.busca_voos?.oportunidades || [],
          milhas: resultados.busca_milhas?.oportunidades || [],
          combinadas: [], // TODO: Calcular oportunidades combinadas
          expiradas: resultados.validacao?.expiradas || [],
          log: {
            execucao_id: execucaoId,
            inicio,
            validacao: resultados.validacao,
            busca_voos: resultados.busca_voos,
            busca_milhas: resultados.busca_milhas,
          },
        };

        resultados.atualizacao_planilha = await ctx.callTool("atualizar_planilha", {
          operacao: "atualizar_completo",
          dados: dadosAtualizacao,
          modo: "atualizar",
        });
        console.log(
          `[${execucaoId}] ✓ Planilha atualizada: ${resultados.atualizacao_planilha.mensagem}`
        );
      } catch (error: any) {
        const erro = `Erro ao atualizar planilha: ${error.message}`;
        resultados.erros.push(erro);
        console.error(`[${execucaoId}] ✗ ${erro}`);
      }

      // 5. ATUALIZAÇÃO CONCLUÍDA
      console.log(`[${execucaoId}] ✓ Planilha atualizada com sucesso`);
      console.log(`[${execucaoId}] ℹ O dashboard Streamlit consumirá os dados automaticamente`);

      resultados.fim = new Date().toISOString();
      console.log(`\n[${execucaoId}] ===== EXECUÇÃO CONCLUÍDA =====`);
      console.log(`[${execucaoId}] Início: ${resultados.inicio}`);
      console.log(`[${execucaoId}] Fim: ${resultados.fim}`);
      console.log(`[${execucaoId}] Erros: ${resultados.erros.length}`);

      if (resultados.erros.length > 0) {
        console.log(`[${execucaoId}] Detalhes dos erros:`);
        resultados.erros.forEach((erro, i) => {
          console.log(`  ${i + 1}. ${erro}`);
        });
      }

      // Salvar resultado completo
      await ctx.host.kv.put(`execucao:${execucaoId}`, resultados);

      // Schedules não devem retornar valores
      console.log(
        `[${execucaoId}] Resultado: ${resultados.erros.length === 0 ? "SUCESSO" : "FALHA"}`
      );
    } catch (error: any) {
      console.error(`[${execucaoId}] ✗ ERRO FATAL: ${error.message}`);
      resultados.fim = new Date().toISOString();
      resultados.erros.push(`Erro fatal: ${error.message}`);

      await ctx.host.kv.put(`execucao:${execucaoId}`, resultados);

      throw error;
    }
  },
});

// Funções auxiliares
async function obterConfiguracoes(ctx: any) {
  // TODO: Ler da aba CONFIGURACOES da planilha
  // Por enquanto, retorna configurações padrão
  return {
    // Grupos separados para não cruzar origens que não combinam com o destino
    grupos_rotas: [
      {
        nome: "Europa",
        origens: (process.env.ORIGENS || "GRU,CGH,VCP").split(",").map((c) => c.trim()),
        destinos: (process.env.DESTINOS || "CDG,LIS,BCN,FCO,MXP,MAD,LON,KEF")
          .split(",")
          .map((c) => c.trim()),
      },
      {
        nome: "América do Sul",
        origens: (process.env.ORIGENS_AMERICA_SUL || "GRU,CGH,VCP").split(",").map((c) => c.trim()),
        destinos: (process.env.DESTINOS_AMERICA_SUL || "MVD,EZE").split(",").map((c) => c.trim()),
      },
      {
        nome: "África do Sul",
        origens: (process.env.ORIGENS_AFRICA || "CNF").split(",").map((c) => c.trim()),
        destinos: (process.env.DESTINOS_AFRICA || "JNB,CPT").split(",").map((c) => c.trim()),
      },
      {
        nome: "Canadá",
        origens: (process.env.ORIGENS_CANADA || "GRU,CGH,VCP,CNF").split(",").map((c) => c.trim()),
        destinos: (process.env.DESTINOS_CANADA || "YUL,YQB").split(",").map((c) => c.trim()),
      },
      {
        nome: "Orlando",
        origens: (process.env.ORIGENS_ORLANDO || "GRU,CGH,VCP,CNF").split(",").map((c) => c.trim()),
        destinos: (process.env.DESTINOS_ORLANDO || "MCO").split(",").map((c) => c.trim()),
      },
    ],
    data_ida_inicio: process.env.DATA_IDA_INICIO || getDataFutura(30),
    data_ida_fim: process.env.DATA_IDA_FIM || getDataFutura(180),
    data_volta_inicio: process.env.DATA_VOLTA_INICIO || getDataFutura(37),
    data_volta_fim: process.env.DATA_VOLTA_FIM || getDataFutura(187),
    passageiros: parseInt(process.env.PASSAGEIROS || "1"),
    preco_maximo: process.env.PRECO_MAXIMO
      ? parseFloat(process.env.PRECO_MAXIMO)
      : undefined,
    desconto_minimo: parseFloat(process.env.DESCONTO_MINIMO || "15"),
    voo_direto_preferencial: process.env.VOO_DIRETO === "true",
    max_conexoes: process.env.MAX_CONEXOES
      ? parseInt(process.env.MAX_CONEXOES)
      : undefined,
    aceitar_mudanca_aeroporto: process.env.ACEITAR_MUDANCA_AEROPORTO === "true",

    // Milhas
    programas_milhas: process.env.PROGRAMAS_MILHAS?.split(","),
    custo_maximo_milheiro: process.env.CUSTO_MAXIMO_MILHEIRO
      ? parseFloat(process.env.CUSTO_MAXIMO_MILHEIRO)
      : undefined,
    desconto_minimo_milhas: parseFloat(process.env.DESCONTO_MINIMO_MILHAS || "10"),

    // E-mail
    email_destinatarios: process.env.EMAIL_DESTINATARIOS?.split(",") || [],
    dashboard_url: process.env.DASHBOARD_URL,
  };
}

function getDataFutura(dias: number): string {
  const data = new Date();
  data.setDate(data.getDate() + dias);
  return data.toISOString().split("T")[0];
}

function calcularResumo(resultados: any) {
  const oportunidadesVoos = resultados.busca_voos?.oportunidades || [];
  const oportunidadesMilhas = resultados.busca_milhas?.oportunidades || [];
  const ativas = resultados.validacao?.ativas || [];
  const expiradas = resultados.validacao?.expiradas || [];

  return {
    oportunidades_ativas: ativas.length + oportunidadesVoos.length,
    novas_semana: oportunidadesVoos.length + oportunidadesMilhas.length,
    expiradas_semana: expiradas.length,
    maior_desconto:
      oportunidadesVoos.length > 0
        ? Math.max(...oportunidadesVoos.map((v: any) => v.desconto_percentual))
        : undefined,
    maior_economia:
      oportunidadesVoos.length > 0
        ? Math.max(...oportunidadesVoos.map((v: any) => v.economia_estimada))
        : undefined,
    melhor_milheiro:
      oportunidadesMilhas.length > 0
        ? Math.min(...oportunidadesMilhas.map((m: any) => m.custo_por_milheiro))
        : undefined,
  };
}
