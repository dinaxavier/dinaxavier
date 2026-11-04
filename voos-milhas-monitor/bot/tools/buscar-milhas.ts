import { defineTool } from "@grok/agent-sdk";
import { z } from "zod";

export default defineTool({
  description:
    "Busca promoções ativas de compra de milhas e pontos em programas de fidelidade. Calcula o custo efetivo por milheiro e compara com referências históricas para identificar oportunidades reais.",
  inputSchema: z.object({
    programas: z
      .array(z.string())
      .optional()
      .describe(
        "Programas específicos para monitorar (ex: ['Smiles', 'Latam Pass', 'Livelo']). Se omitido, monitora todos."
      ),
    custo_maximo_milheiro: z
      .number()
      .positive()
      .optional()
      .describe("Custo máximo aceitável por milheiro (em centavos)"),
    desconto_minimo: z
      .number()
      .min(0)
      .max(100)
      .default(10)
      .describe(
        "Desconto mínimo percentual em relação ao histórico para considerar oportunidade (%)"
      ),
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
      // Programas principais de fidelidade no Brasil
      const programasPadrao = [
        "Smiles",
        "Latam Pass",
        "Livelo",
        "TudoAzul",
        "Esfera",
        "Club Premier (Aeroméxico)",
        "LifeMiles",
        "Membership Rewards (Amex)",
      ];

      const programasMonitorar = params.programas || programasPadrao;

      // 1. Buscar referências históricas
      for (const programa of programasMonitorar) {
        resultado.referencias_historicas[programa] = await buscarCustoHistoricoMilheiro(
          programa,
          ctx
        );
      }

      // 2. Buscar promoções ativas
      const promocoesEncontradas = await buscarPromocoesAtivas(programasMonitorar);
      resultado.total_encontradas = promocoesEncontradas.length;

      // 3. Analisar cada promoção
      for (const promocao of promocoesEncontradas) {
        const custoReferencia = resultado.referencias_historicas[promocao.programa];

        if (!custoReferencia) {
          resultado.erros.push(
            `Sem referência histórica para ${promocao.programa}`
          );
          continue;
        }

        // Calcular custo efetivo por milheiro
        const custoMilheiro = calcularCustoMilheiro(promocao);

        // Calcular economia
        const economia = custoReferencia - custoMilheiro;
        const descontoPercentual = (economia / custoReferencia) * 100;

        // Verificar se atende critérios
        if (descontoPercentual < params.desconto_minimo) {
          continue;
        }

        if (params.custo_maximo_milheiro && custoMilheiro > params.custo_maximo_milheiro) {
          continue;
        }

        // Calcular score (baseado no desconto)
        const score = Math.min((descontoPercentual / 40) * 100, 100);

        const oportunidade = {
          id: gerarIdOportunidade(promocao),
          timestamp: resultado.timestamp,
          programa: promocao.programa,
          tipo_promocao: promocao.tipo,
          descricao: promocao.descricao,

          // Dados da promoção
          quantidade_base: promocao.quantidade_base,
          bonus_percentual: promocao.bonus_percentual,
          quantidade_total: promocao.quantidade_total,
          preco_total: promocao.preco_total,

          // Análise
          custo_por_milheiro: custoMilheiro,
          referencia_historica: custoReferencia,
          economia_por_milheiro: economia,
          desconto_percentual: descontoPercentual,

          // Condições
          elegibilidade: promocao.elegibilidade || "Geral",
          validade_promocao: promocao.validade_promocao,
          validade_milhas: promocao.validade_milhas,
          condicoes_especiais: promocao.condicoes || [],

          // Avaliação
          score,

          // Extras
          link_oficial: promocao.link,
          observacoes: promocao.observacoes || null,
        };

        resultado.oportunidades.push(oportunidade);
      }

      // 4. Ordenar por score
      resultado.oportunidades.sort((a, b) => b.score - a.score);

      // 5. Registrar no log
      await registrarNoLog(ctx, "BUSCA_MILHAS", {
        parametros: params,
        encontradas: resultado.total_encontradas,
        oportunidades: resultado.oportunidades.length,
      });

      return {
        sucesso: true,
        ...resultado,
        mensagem: `Busca de milhas concluída: ${resultado.oportunidades.length} oportunidades encontradas de ${resultado.total_encontradas} promoções analisadas`,
      };
    } catch (error: any) {
      resultado.erros.push(error.message);
      return {
        sucesso: false,
        ...resultado,
        mensagem: `Erro na busca de milhas: ${error.message}`,
      };
    }
  },
});

// Funções auxiliares
async function buscarCustoHistoricoMilheiro(
  programa: string,
  ctx: any
): Promise<number> {
  // TODO: Buscar de histórico na planilha
  // Por enquanto, retorna custos médios conhecidos (em centavos)
  const custosMedios: Record<string, number> = {
    Smiles: 3.5,
    "Latam Pass": 4.0,
    Livelo: 2.8,
    TudoAzul: 3.8,
    Esfera: 3.2,
    "Club Premier (Aeroméxico)": 2.5,
    LifeMiles: 1.8,
    "Membership Rewards (Amex)": 3.0,
  };

  return custosMedios[programa] || 3.5;
}

async function buscarPromocoesAtivas(programas: string[]): Promise<any[]> {
  // TODO: Implementar scraping/API de sites de milhas
  // Fontes: sites oficiais, Melhores Destinos, Pontos pra Voar, etc.
  return [];
}

function calcularCustoMilheiro(promocao: any): number {
  // Custo efetivo considerando o bônus
  const quantidadeTotal = promocao.quantidade_base * (1 + promocao.bonus_percentual / 100);
  const custoMilheiro = (promocao.preco_total / quantidadeTotal) * 1000;

  return Math.round(custoMilheiro * 100) / 100; // Arredonda para 2 casas decimais
}

function gerarIdOportunidade(promocao: any): string {
  const timestamp = Date.now();
  const hash = `${promocao.programa}${promocao.tipo}${timestamp}`.slice(0, 16);
  return `MILHAS_${hash}`;
}

async function registrarNoLog(ctx: any, tipo: string, dados: any) {
  console.log(`[${tipo}]`, JSON.stringify(dados, null, 2));
}
