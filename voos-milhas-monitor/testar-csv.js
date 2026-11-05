#!/usr/bin/env node

/**
 * Script para testar CSV storage e integração completa
 * Execute: node testar-csv.js
 */

import 'dotenv/config';
import * as fs from 'fs';
import * as path from 'path';

async function testarKiwiAPI() {
  console.log('\n✈️  === TESTE KIWI API ===\n');

  try {
    const { KiwiClient } = await import('./bot/lib/kiwi-client.js');
    const client = new KiwiClient();

    console.log('1. Testando conexão...');
    const conectado = await client.testarConexao();

    if (!conectado) {
      console.error('❌ Falha na conexão');
      return false;
    }

    const hoje = new Date();
    const daquiA30Dias = new Date(hoje);
    daquiA30Dias.setDate(hoje.getDate() + 30);
    const daquiA37Dias = new Date(hoje);
    daquiA37Dias.setDate(hoje.getDate() + 37);

    const formatarData = (data) => {
      return data.toISOString().split('T')[0];
    };

    const separar = (valor, padrao) =>
      (valor || padrao).split(',').map((item) => item.trim()).filter(Boolean);

    const grupos = [
      {
        nome: 'Europa',
        origens: separar(process.env.ORIGENS, 'GRU,CGH,VCP'),
        destinos: separar(process.env.DESTINOS, 'CDG,LIS,BCN,FCO,MXP,MAD,LON,KEF'),
      },
      {
        nome: 'América do Sul',
        origens: separar(process.env.ORIGENS_AMERICA_SUL, 'GRU,CGH,VCP'),
        destinos: separar(process.env.DESTINOS_AMERICA_SUL, 'MVD,EZE'),
      },
      {
        nome: 'África do Sul',
        origens: separar(process.env.ORIGENS_AFRICA, 'CNF'),
        destinos: separar(process.env.DESTINOS_AFRICA, 'JNB,CPT'),
      },
      {
        nome: 'Canadá',
        origens: separar(process.env.ORIGENS_CANADA, 'GRU,MCO'),
        destinos: separar(process.env.DESTINOS_CANADA, 'YUL,YQB'),
      },
    ];

    const voos = [];
    for (const grupo of grupos) {
      console.log(
        `\n2. Buscando ${grupo.nome}: ${grupo.origens.join(',')} → ${grupo.destinos.join(',')}`
      );
      const encontrados = await client.buscarVoos({
        origens: grupo.origens,
        destinos: grupo.destinos,
        dataIdaInicio: formatarData(daquiA30Dias),
        dataIdaFim: formatarData(daquiA30Dias),
        dataVoltaInicio: formatarData(daquiA37Dias),
        dataVoltaFim: formatarData(daquiA37Dias),
        passageiros: 1,
        maxConexoes: 2,
        limite: 20,
      });
      voos.push(...encontrados);
    }

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
    return voos;
  } catch (error) {
    console.error('\n❌ Erro na Kiwi API:', error.message);
    console.error('\nVerifique:');
    console.error('- KIWI_API_KEY está configurado no .env\n');
    return [];
  }
}

async function testarCSVStorage(voos) {
  console.log('\n📁 === TESTE CSV STORAGE ===\n');

  try {
    const { CSVStorage } = await import('./bot/lib/csv-storage.js');
    const storage = new CSVStorage();

    console.log('1. Testando criação de diretório...');
    console.log(`   Diretório: ${storage.getCaminhoDados()}`);

    // Preparar dados para salvar
    console.log('\n2. Salvando voos em CSV...');
    const voosParaSalvar = voos.map((voo) => ({
      id: `TESTE_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      origem: voo.origem,
      cidade_origem: voo.cidade_origem,
      destino: voo.destino,
      cidade_destino: voo.cidade_destino,
      companhia: voo.companhia,
      data_ida: voo.data_ida,
      data_volta: voo.data_volta,
      preco_por_pessoa: voo.preco_por_pessoa,
      preco_total: voo.preco_total,
      preco_referencia: 3000,
      desconto_percentual: ((3000 - voo.preco_por_pessoa) / 3000) * 100,
      economia_estimada: 3000 - voo.preco_por_pessoa,
      tipo_voo_ida: voo.tipo_voo_ida,
      tipo_voo_volta: voo.tipo_voo_volta,
      total_conexoes: voo.total_conexoes,
      duracao_total_ida: voo.duracao_total_ida,
      duracao_total_volta: voo.duracao_total_volta,
      mudanca_aeroporto: voo.mudanca_aeroporto,
      classificacao_logistica: voo.voo_direto ? 'Excelente' : 'Boa',
      score: 85,
      bagagem_incluida: voo.bagagem_incluida,
      link: voo.deep_link,
    }));

    await storage.salvarVoos(voosParaSalvar);

    console.log('\n3. Salvando estatísticas...');
    await storage.salvarEstatisticas({
      total_oportunidades: voosParaSalvar.length,
      novas_semana: voosParaSalvar.length,
      maior_desconto: Math.max(...voosParaSalvar.map(v => v.desconto_percentual)),
      melhor_preco: Math.min(...voosParaSalvar.map(v => v.preco_por_pessoa)),
      melhor_custo_milheiro: 280,
    });

    console.log('\n4. Registrando log...');
    await storage.registrarLog({
      execucao_id: `TESTE_${Date.now()}`,
      inicio: new Date().toISOString(),
      ofertas_verificadas: voosParaSalvar.length,
      ofertas_confirmadas: voosParaSalvar.length,
      novas_oportunidades: voosParaSalvar.length,
      status: 'OK',
    });

    console.log('\n5. Verificando arquivos criados...');
    const dataDir = storage.getCaminhoDados();
    const arquivos = fs.readdirSync(dataDir);
    
    console.log('   Arquivos criados:');
    arquivos.forEach((arquivo) => {
      const tamanho = fs.statSync(path.join(dataDir, arquivo)).size;
      console.log(`   ✓ ${arquivo} (${tamanho} bytes)`);
    });

    console.log('\n✅ CSV Storage: OK\n');
    console.log(`📂 Dados salvos em: ${dataDir}\n`);
    return true;
  } catch (error) {
    console.error('\n❌ Erro no CSV Storage:', error.message);
    console.error(error.stack);
    return false;
  }
}

async function main() {
  console.log('╔══════════════════════════════════════════════════╗');
  console.log('║  TESTE CSV + KIWI API - MONITOR DE VOOS         ║');
  console.log('╚══════════════════════════════════════════════════╝');

  // Verificar configuração
  console.log('\n🔍 Verificando configuração...\n');
  const kiwiConfigured = !!process.env.KIWI_API_KEY;
  
  console.log(`  ${kiwiConfigured ? '✓' : '✗'} KIWI_API_KEY`);

  if (!kiwiConfigured) {
    console.log('\n⚠️  Configure KIWI_API_KEY no .env\n');
    console.log('Veja SETUP_APIS.md para instruções\n');
    process.exit(1);
  }

  console.log('\n✓ Configuração OK\n');

  // Executar testes
  const voos = await testarKiwiAPI();
  
  if (voos.length > 0) {
    await testarCSVStorage(voos);
  } else {
    console.log('\n⚠️  Nenhum voo encontrado para testar CSV\n');
  }

  // Resultado final
  console.log('\n╔══════════════════════════════════════════════════╗');
  console.log('║  PRÓXIMOS PASSOS                                 ║');
  console.log('╚══════════════════════════════════════════════════╝\n');
  console.log('1. Testar dashboard Streamlit:');
  console.log('   cd dashboard');
  console.log('   streamlit run app.py\n');
  console.log('2. Testar agente no playground:');
  console.log('   npx @grok/agent-sdk serve --dir . --mode single --dev\n');
  console.log('3. Dashboard estará em: http://localhost:8501\n');
}

main().catch((error) => {
  console.error('\n💥 Erro fatal:', error);
  process.exit(1);
});
