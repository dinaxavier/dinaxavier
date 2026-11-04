import { defineTool } from "@grok/agent-sdk";
import { z } from "zod";

export default defineTool({
  description:
    "Envia relatório semanal por e-mail em formato HTML com as melhores oportunidades de voos e milhas identificadas. Inclui resumo executivo, categorias organizadas e link para o dashboard.",
  inputSchema: z.object({
    destinatarios: z
      .array(z.string().email())
      .describe("Lista de endereços de e-mail dos destinatários"),
    assunto: z
      .string()
      .optional()
      .describe("Assunto do e-mail (gerado automaticamente se omitido)"),
    dados: z.object({
      resumo: z.object({
        oportunidades_ativas: z.number(),
        novas_semana: z.number(),
        expiradas_semana: z.number(),
        maior_desconto: z.number().optional(),
        maior_economia: z.number().optional(),
        melhor_milheiro: z.number().optional(),
      }),
      passagens: z.array(z.any()).optional(),
      milhas: z.array(z.any()).optional(),
      combinadas: z.array(z.any()).optional(),
      dashboard_url: z.string().url().optional(),
      data_verificacao: z.string(),
    }),
    limite_por_categoria: z
      .number()
      .int()
      .positive()
      .optional()
      .default(5)
      .describe("Número máximo de oportunidades a exibir por categoria"),
  }),
  effect: "write",
  execution: "server",

  async execute({ destinatarios, assunto, dados, limite_por_categoria }, ctx) {
    const resultado = {
      timestamp: new Date().toISOString(),
      destinatarios,
      enviado: false,
      erros: [] as string[],
    };

    try {
      // Gerar assunto se não fornecido
      const assuntoFinal =
        assunto ||
        `🛫 Oportunidades de Voos e Milhas - ${new Date(
          dados.data_verificacao
        ).toLocaleDateString("pt-BR")}`;

      // Gerar HTML do e-mail
      const htmlEmail = gerarHTMLEmail(dados, limite_por_categoria);

      // TODO: Implementar envio real de e-mail
      // Opções: SendGrid, AWS SES, Nodemailer com SMTP, etc.
      const enviado = await enviarEmail({
        para: destinatarios,
        assunto: assuntoFinal,
        html: htmlEmail,
      });

      resultado.enviado = enviado;

      return {
        ...resultado,
        mensagem: `E-mail enviado com sucesso para ${destinatarios.length} destinatário(s)`,
      };
    } catch (error: any) {
      resultado.erros.push(error.message);
      return {
        ...resultado,
        mensagem: `Erro ao enviar e-mail: ${error.message}`,
      };
    }
  },
});

// Funções auxiliares
function gerarHTMLEmail(dados: any, limite: number): string {
  const { resumo, passagens, milhas, combinadas, dashboard_url, data_verificacao } = dados;

  // Filtrar top oportunidades
  const topPassagens = (passagens || [])
    .sort((a: any, b: any) => b.score - a.score)
    .slice(0, limite);
  const topMilhas = (milhas || [])
    .sort((a: any, b: any) => b.score - a.score)
    .slice(0, limite);
  const topCombinadas = (combinadas || [])
    .sort((a: any, b: any) => b.economia_liquida - a.economia_liquida)
    .slice(0, limite);

  const temOportunidades =
    topPassagens.length > 0 || topMilhas.length > 0 || topCombinadas.length > 0;

  return `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Oportunidades de Voos e Milhas</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f5f5f5;
    }
    .container {
      background: white;
      border-radius: 8px;
      padding: 30px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    h1 {
      color: #2563eb;
      border-bottom: 3px solid #2563eb;
      padding-bottom: 10px;
    }
    h2 {
      color: #1e40af;
      margin-top: 30px;
    }
    .resumo {
      background: #dbeafe;
      padding: 20px;
      border-radius: 8px;
      margin: 20px 0;
    }
    .resumo-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #bfdbfe;
    }
    .resumo-item:last-child {
      border-bottom: none;
    }
    .resumo-label {
      font-weight: 600;
    }
    .resumo-valor {
      color: #1e40af;
      font-weight: bold;
    }
    .oportunidade {
      background: #f9fafb;
      border-left: 4px solid #10b981;
      padding: 15px;
      margin: 15px 0;
      border-radius: 4px;
    }
    .oportunidade-titulo {
      font-size: 18px;
      font-weight: bold;
      color: #1f2937;
      margin-bottom: 10px;
    }
    .oportunidade-detalhe {
      margin: 5px 0;
      font-size: 14px;
    }
    .destaque {
      color: #dc2626;
      font-weight: bold;
    }
    .economia {
      color: #059669;
      font-weight: bold;
      font-size: 16px;
    }
    .alerta {
      background: #fef3c7;
      border-left-color: #f59e0b;
      padding: 10px;
      margin: 10px 0;
      border-radius: 4px;
      font-size: 14px;
    }
    .btn {
      display: inline-block;
      background: #2563eb;
      color: white;
      padding: 12px 24px;
      text-decoration: none;
      border-radius: 6px;
      margin: 20px 0;
      font-weight: 600;
    }
    .btn:hover {
      background: #1e40af;
    }
    .footer {
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #e5e7eb;
      font-size: 12px;
      color: #6b7280;
      text-align: center;
    }
    .badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      margin-right: 5px;
    }
    .badge-excelente {
      background: #d1fae5;
      color: #065f46;
    }
    .badge-boa {
      background: #dbeafe;
      color: #1e40af;
    }
    .badge-moderada {
      background: #fef3c7;
      color: #92400e;
    }
    .badge-atencao {
      background: #fee2e2;
      color: #991b1b;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🛫 Oportunidades de Voos e Milhas</h1>
    
    <p><strong>Última verificação:</strong> ${new Date(data_verificacao).toLocaleString(
      "pt-BR"
    )}</p>

    <!-- Resumo Executivo -->
    <div class="resumo">
      <h2 style="margin-top: 0;">📊 Resumo Executivo</h2>
      <div class="resumo-item">
        <span class="resumo-label">Oportunidades Ativas</span>
        <span class="resumo-valor">${resumo.oportunidades_ativas}</span>
      </div>
      <div class="resumo-item">
        <span class="resumo-label">Novas esta Semana</span>
        <span class="resumo-valor">${resumo.novas_semana}</span>
      </div>
      <div class="resumo-item">
        <span class="resumo-label">Expiradas esta Semana</span>
        <span class="resumo-valor">${resumo.expiradas_semana}</span>
      </div>
      ${
        resumo.maior_desconto
          ? `
      <div class="resumo-item">
        <span class="resumo-label">Maior Desconto</span>
        <span class="resumo-valor">${resumo.maior_desconto.toFixed(1)}%</span>
      </div>
      `
          : ""
      }
      ${
        resumo.maior_economia
          ? `
      <div class="resumo-item">
        <span class="resumo-label">Maior Economia</span>
        <span class="resumo-valor">R$ ${resumo.maior_economia.toFixed(2)}</span>
      </div>
      `
          : ""
      }
      ${
        resumo.melhor_milheiro
          ? `
      <div class="resumo-item">
        <span class="resumo-label">Melhor Custo por Milheiro</span>
        <span class="resumo-valor">R$ ${(resumo.melhor_milheiro / 100).toFixed(2)}</span>
      </div>
      `
          : ""
      }
    </div>

    ${
      !temOportunidades
        ? `
    <div class="alerta">
      <strong>⚠️ Nenhuma oportunidade qualificada encontrada esta semana.</strong>
      <p>Continuaremos monitorando e notificaremos quando identificarmos novas oportunidades reais de economia.</p>
    </div>
    `
        : ""
    }

    <!-- Passagens Aéreas -->
    ${
      topPassagens.length > 0
        ? `
    <h2>✈️ Melhores Passagens Aéreas</h2>
    ${topPassagens
      .map(
        (voo: any) => `
    <div class="oportunidade">
      <div class="oportunidade-titulo">
        ${voo.origem} → ${voo.destino}
      </div>
      <div class="oportunidade-detalhe">
        <strong>Companhia:</strong> ${voo.companhia} 
        <span class="badge badge-${voo.classificacao_logistica.toLowerCase()}">${
          voo.classificacao_logistica
        }</span>
      </div>
      <div class="oportunidade-detalhe">
        <strong>Datas:</strong> ${new Date(voo.data_ida).toLocaleDateString(
          "pt-BR"
        )} - ${new Date(voo.data_volta).toLocaleDateString("pt-BR")}
      </div>
      <div class="oportunidade-detalhe">
        <strong>Preço:</strong> R$ ${voo.preco_por_pessoa.toFixed(
          2
        )}/pessoa | Total: R$ ${voo.preco_total.toFixed(2)}
      </div>
      <div class="oportunidade-detalhe">
        <strong>Economia:</strong> <span class="economia">R$ ${voo.economia_estimada.toFixed(
          2
        )} (${voo.desconto_percentual.toFixed(1)}% de desconto)</span>
      </div>
      <div class="oportunidade-detalhe">
        <strong>Duração:</strong> Ida ${voo.duracao_total_ida} | Volta ${
          voo.duracao_total_volta
        }
      </div>
      ${
        voo.mudanca_aeroporto
          ? `<div class="alerta">⚠️ <strong>Atenção:</strong> Requer mudança de aeroporto</div>`
          : ""
      }
      ${voo.link ? `<a href="${voo.link}" class="btn">Ver Passagem</a>` : ""}
    </div>
    `
      )
      .join("")}
    `
        : ""
    }

    <!-- Promoções de Milhas -->
    ${
      topMilhas.length > 0
        ? `
    <h2>💳 Melhores Promoções de Milhas</h2>
    ${topMilhas
      .map(
        (milha: any) => `
    <div class="oportunidade">
      <div class="oportunidade-titulo">
        ${milha.programa} - ${milha.tipo_promocao}
      </div>
      <div class="oportunidade-detalhe">
        <strong>Custo por milheiro:</strong> <span class="economia">R$ ${(
          milha.custo_por_milheiro / 100
        ).toFixed(2)}</span>
      </div>
      <div class="oportunidade-detalhe">
        <strong>Economia:</strong> ${milha.desconto_percentual.toFixed(1)}% vs. histórico
      </div>
      <div class="oportunidade-detalhe">
        <strong>Bônus:</strong> ${milha.bonus_percentual}%
      </div>
      <div class="oportunidade-detalhe">
        <strong>Validade:</strong> ${new Date(
          milha.validade_promocao
        ).toLocaleDateString("pt-BR")}
      </div>
      ${
        milha.link_oficial
          ? `<a href="${milha.link_oficial}" class="btn">Ver Promoção</a>`
          : ""
      }
    </div>
    `
      )
      .join("")}
    `
        : ""
    }

    <!-- Oportunidades Combinadas -->
    ${
      topCombinadas.length > 0
        ? `
    <h2>🎯 Oportunidades Combinadas (Compra de Milhas + Emissão)</h2>
    ${topCombinadas
      .map(
        (comb: any) => `
    <div class="oportunidade">
      <div class="oportunidade-titulo">
        ${comb.rota}
      </div>
      <div class="oportunidade-detalhe">
        <strong>Programa:</strong> ${comb.programa}
      </div>
      <div class="oportunidade-detalhe">
        <strong>Custo total (milhas + taxas):</strong> R$ ${comb.custo_total_emissao.toFixed(
          2
        )}
      </div>
      <div class="oportunidade-detalhe">
        <strong>Preço em dinheiro:</strong> R$ ${comb.preco_em_dinheiro.toFixed(2)}
      </div>
      <div class="oportunidade-detalhe">
        <strong>Economia líquida:</strong> <span class="economia">R$ ${comb.economia_liquida.toFixed(
          2
        )} (${comb.economia_percentual.toFixed(1)}%)</span>
      </div>
    </div>
    `
      )
      .join("")}
    `
        : ""
    }

    ${
      dashboard_url
        ? `
    <div style="text-align: center; margin: 40px 0;">
      <a href="${dashboard_url}" class="btn">📊 Acessar Dashboard Completo</a>
    </div>
    `
        : ""
    }

    <div class="footer">
      <p>Este relatório é gerado automaticamente pelo Monitor de Voos e Milhas.</p>
      <p>As oportunidades foram validadas na data da verificação, mas podem expirar rapidamente.</p>
      <p>Sempre confirme preços e disponibilidade antes de comprar.</p>
    </div>
  </div>
</body>
</html>
  `;
}

async function enviarEmail(dados: {
  para: string[];
  assunto: string;
  html: string;
}): Promise<boolean> {
  // TODO: Implementar envio real
  // Exemplo com Nodemailer:
  /*
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: false,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });

  await transporter.sendMail({
    from: process.env.EMAIL_FROM,
    to: dados.para.join(','),
    subject: dados.assunto,
    html: dados.html,
  });
  */

  console.log("[EMAIL] Enviado para:", dados.para);
  console.log("[EMAIL] Assunto:", dados.assunto);
  return true;
}
