#!/usr/bin/env node

/**
 * Script para testar as integrações do agente
 * Execute: node testar-integracao.js
 */

import 'dotenv/config';

async function testarGoogleSheets() {
  console.log('\n📊 === TESTE GOOGLE SHEETS ===\n');

  try {
    const { SheetsClient } = await import('./bot/lib/sheets-client.js');
    const client = new SheetsClient();

    // Testar conexão
    console.log('1. Testando conexão...');
    const conectado = await client.testarConexao();

    if (!conectado) {
      console.error('❌ Falha na conexão');
      return false;
    }

    // Testar leitura
    console.log('\n2. Testando leitura de dados...');
    const dados = await client.lerDados('VOOS_ATIVOS');
    console.log(`✓ Lidos ${dados.length} linhas`);

    // Testar inicialização (se necessário)
    if (dados.length === 0) {
      console.log('\n3. Inicializando planilha com cabeçalhos...');
      await client.inicializarPlanilha();
    }

    console.log('\n✅ Google Sheets: OK\n');
    return true;
  } catch (error) {
    console.error('\n❌ Erro no Google Sheets:', error.message);
    console.error('\nVerifique:');
    console.error('- GOOGLE_SHEETS_ID está configurado no .env');
    console.error('- credentials.json existe e está correto');
    console.error('- Planilha foi compartilhada com a service account\n');
    return false;
  }
}

async function testarKiwiAPI() {
  console.log('\n✈️  === TESTE KIWI API ===\n');

  try {
    const { KiwiClient } = await import('./bot/lib/kiwi-client.js');
    const client = new KiwiClient();

    // Testar conexão
    console.log('1. Testando conexão...');
    const conectado = await client.testarConexao();

    if (!conectado) {
      console.error('❌ Falha na conexão');
      return false;
    }

    // Testar busca simples
    console.log('\n2. Testando busca de voos (GRU → CDG)...');
    const hoje = new Date();
    const daquiA30Dias = new Date(hoje);
    daquiA30Dias.setDate(hoje.getDate() + 30);
    const daquiA37Dias = new Date(hoje);
    daquiA37Dias.setDate(hoje.getDate() + 37);

    const formatarData = (data) => {
      return data.toISOString().split('T')[0];
    };

    const voos = await client.buscarVoos({
      origens: ['GRU'],
      destinos: ['CDG'],
      dataIdaInicio: formatarData(daquiA30Dias),
      dataIdaFim: formatarData(daquiA30Dias),
      dataVoltaInicio: formatarData(daquiA37Dias),
      dataVoltaFim: formatarData(daquiA37Dias),
      passageiros: 1,
      maxConexoes: 2,
      limite: 5,
    });

    console.log(`✓ Encontrados ${voos.length} voos`);

    if (voos.length > 0) {
      const voo = voos[0];
      console.log('\nExemplo de voo encontrado:');
      console.log(`  ${voo.origem} → ${voo.destino}`);
      console.log(`  Preço: R$ ${voo.preco_total.toFixed(2)}`);
      console.log(`  Tipo: ${voo.tipo_voo_ida}`);
      console.log(`  Companhia: ${voo.companhia}`);
    }

    console.log('\n✅ Kiwi API: OK\n');
    return true;
  } catch (error) {
    console.error('\n❌ Erro na Kiwi API:', error.message);
    console.error('\nVerifique:');
    console.error('- KIWI_API_KEY está configurado no .env');
    console.error('- API key está válida (teste em: https://tequila.kiwi.com)\n');
    return false;
  }
}

async function testarFluxoCompleto() {
  console.log('\n🔄 === TESTE FLUXO COMPLETO ===\n');

  try {
    console.log('1. Buscando voos...');
    const { KiwiClient } = await import('./bot/lib/kiwi-client.js');
    const kiwiClient = new KiwiClient();

    const hoje = new Date();
    const daquiA30Dias = new Date(hoje);
    daquiA30Dias.setDate(hoje.getDate() + 30);

    const formatarData = (data) => {
      return data.toISOString().split('T')[0];
    };

    const voos = await kiwiClient.buscarVoos({
      origens: ['GRU'],
      destinos: ['LIS'],
      dataIdaInicio: formatarData(daquiA30Dias),
      dataIdaFim: formatarData(daquiA30Dias),
      passageiros: 1,
      limite: 3,
    });

    if (voos.length === 0) {
      console.log('⚠️  Nenhum voo encontrado para testar');
      return true;
    }

    console.log(`✓ Encontrados ${voos.length} voos\n`);

    // Preparar dados para salvar
    const voosParaSalvar = voos.map((voo) => ({
      id: `TESTE_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      origem: voo.origem,
      destino: voo.destino,
      companhia: voo.companhia,
      data_ida: voo.data_ida,
      data_volta: voo.data_volta,
      passageiros: 1,
      preco_por_pessoa: voo.preco_por_pessoa,
      preco_total: voo.preco_total,
      preco_referencia: 3000,
      desconto_percentual: ((3000 - voo.preco_por_pessoa) / 3000) * 100,
      economia_estimada: 3000 - voo.preco_por_pessoa,
      tipo_voo_ida: voo.tipo_voo_ida,
      conexoes_ida: voo.conexoes_ida,
      conexoes_volta: voo.conexoes_volta,
      duracao_total_ida: voo.duracao_total_ida,
      duracao_total_volta: voo.duracao_total_volta,
      mudanca_aeroporto: voo.mudanca_aeroporto,
      bagagem_incluida: voo.bagagem_incluida,
      tipo_bilhete: 'Econômica',
      classificacao_logistica: voo.voo_direto ? 'Excelente' : 'Boa',
      score: 85,
      link: voo.deep_link,
      alertas_logisticos: [],
    }));

    console.log('2. Salvando na planilha...');
    const { SheetsClient } = await import('./bot/lib/sheets-client.js');
    const sheetsClient = new SheetsClient();

    const linhas = voosParaSalvar.map((voo) => [
      voo.id,
      voo.timestamp,
      new Date().toISOString(),
      'TESTE',
      voo.origem,
      voo.destino,
      voo.companhia,
      voo.data_ida,
      voo.data_volta || '',
      voo.passageiros,
      voo.preco_por_pessoa?.toFixed(2),
      voo.preco_total?.toFixed(2),
      voo.preco_referencia?.toFixed(2),
      voo.desconto_percentual?.toFixed(1),
      voo.economia_estimada?.toFixed(2),
      voo.tipo_voo_ida,
      voo.conexoes_ida?.length || 0,
      voo.conexoes_volta?.length || 0,
      voo.duracao_total_ida,
      voo.duracao_total_volta || '',
      voo.mudanca_aeroporto ? 'Sim' : 'Não',
      voo.bagagem_incluida,
      voo.tipo_bilhete,
      voo.classificacao_logistica,
      voo.score,
      voo.link,
      '',
    ]);

    await sheetsClient.adicionarLinhas('VOOS_ATIVOS', linhas);
    console.log(`✓ ${linhas.length} voos salvos na planilha\n`);

    console.log('3. Verificando dados salvos...');
    const dadosSalvos = await sheetsClient.lerDados('VOOS_ATIVOS');
    console.log(`✓ Total de ${dadosSalvos.length} linhas na planilha\n`);

    console.log('✅ Fluxo completo: OK\n');
    console.log('📊 Abra sua planilha para ver os dados!\n');
    return true;
  } catch (error) {
    console.error('\n❌ Erro no fluxo completo:', error.message);
    console.error(error);
    return false;
  }
}

// Executar testes
async function main() {
  console.log('╔══════════════════════════════════════════════════╗');
  console.log('║  TESTE DE INTEGRAÇÕES - MONITOR DE VOOS         ║');
  console.log('╚══════════════════════════════════════════════════╝');

  // Verificar variáveis de ambiente
  console.log('\n🔍 Verificando configuração...\n');
  const checks = {
    'GOOGLE_SHEETS_ID': !!process.env.GOOGLE_SHEETS_ID,
    'GOOGLE_APPLICATION_CREDENTIALS': !!process.env.GOOGLE_APPLICATION_CREDENTIALS,
    'KIWI_API_KEY': !!process.env.KIWI_API_KEY,
  };

  for (const [key, value] of Object.entries(checks)) {
    console.log(`  ${value ? '✓' : '✗'} ${key}`);
  }

  const todasConfiguradas = Object.values(checks).every((v) => v);

  if (!todasConfiguradas) {
    console.log('\n⚠️  Configure as variáveis faltantes no .env\n');
    console.log('Veja SETUP_APIS.md para instruções\n');
    process.exit(1);
  }

  console.log('\n✓ Todas as variáveis configuradas\n');

  // Executar testes
  const resultados = {
    sheets: await testarGoogleSheets(),
    kiwi: await testarKiwiAPI(),
  };

  if (resultados.sheets && resultados.kiwi) {
    const testarFluxo = process.argv.includes('--fluxo');

    if (testarFluxo) {
      await testarFluxoCompleto();
    } else {
      console.log('💡 Para testar o fluxo completo: node testar-integracao.js --fluxo\n');
    }
  }

  // Resultado final
  console.log('╔══════════════════════════════════════════════════╗');
  console.log('║  RESULTADO DOS TESTES                            ║');
  console.log('╚══════════════════════════════════════════════════╝\n');
  console.log(`  Google Sheets: ${resultados.sheets ? '✅ OK' : '❌ FALHOU'}`);
  console.log(`  Kiwi API:      ${resultados.kiwi ? '✅ OK' : '❌ FALHOU'}\n`);

  if (resultados.sheets && resultados.kiwi) {
    console.log('🎉 Todas as integrações estão funcionando!\n');
    console.log('Próximos passos:');
    console.log('1. Teste o agente no playground:');
    console.log('   npx @grok/agent-sdk serve --dir . --mode single --dev\n');
    console.log('2. Teste o fluxo completo:');
    console.log('   node testar-integracao.js --fluxo\n');
    process.exit(0);
  } else {
    console.log('❌ Algumas integrações falharam\n');
    console.log('Veja os erros acima e corrija a configuração\n');
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('\n💥 Erro fatal:', error);
  process.exit(1);
});
