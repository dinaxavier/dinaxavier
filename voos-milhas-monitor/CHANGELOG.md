# 📋 Changelog - Monitor de Voos e Milhas

## [3.4.0] - 2026-11-06

### Aba Compra de milhas

- Mantém os balões no topo de Passagens.
- Nova aba **Compra de milhas** com a lista completa, filtros por programa e avaliação.

## [3.3.0] - 2026-11-06

### Avaliação de promoções de milhas

- Classifica cada oferta: **Excelente** / **Regular** / **Ruim** (compra isolada).
- Campo **Custo efetivo do milheiro após bônus de transferência**.
- Turbo Livelo ~R$ 29,40 → Ruim na compra isolada; efetivo ilustrativo com transferência ref. 100%.
- Regras em `config-milhas.json` (`avaliacao.excelente_ate` / `regular_ate`).

## [3.2.0] - 2026-11-06

### Dashboard em página única + milhas automáticas

- Remove milhas, combinadas, histórico e config da navegação — fica só o radar de passagens.
- Balões de promoção no topo, alimentados automaticamente.
- `scripts/buscar_promocoes_milhas.py` varre feeds (Passageiro de Primeira / Melhores Destinos) filtrando os programas de `config-milhas.json`.
- Botão **Atualizar dados** e a 1ª carga (CSV velho) disparam a coleta.

## [3.1.0] - 2026-11-06

### Dashboard: aviso de milhas no topo

- Remove a página "Promoções de Milhas".
- Promoções ativas em `data/milhas_ativas.csv` aparecem como balão no topo.
- Lista de programas em `config-milhas.json` (Smiles, Azul, LATAM Pass, Livelo, Esfera, Iberia/BA Avios, TAP, Flying Blue, AAdvantage, United, Copa, Aerolíneas Plus).

## [3.0.0] - 2026-11-06

### Matriz: 6 meses + São Luís + amostra espalhada

- Janela relativa `meses_a_frente: 6` (varre ~27 idas semanais).
- Estratégia `espalhada`: até 3 datas por rota por rodada (não esgota uma rota só).
- Origem **SLZ (São Luís/MA)** incluída nos grupos de busca.
- `max_celulas_por_rodada` sobe para 180 (~177 células / rodada com a config atual).

### Rotina: matriz de datas + baseline + alerta

- `scripts/matriz.py` gera células `rota × ida × estadia` e amostra com rotação (`max_celulas_por_rodada`).
- `scripts/baseline.py` mantém `data/observacoes.csv` (append-only) e calcula mediana por rota.
- `scripts/gravar_voos.py` grava observação sempre; só promove alerta (≥ 25% abaixo do baseline, ou média da página no bootstrap).
- `scripts/listar_rotas.py` lista a amostra da rodada com links datados.
- `prompt-rotina-semanal.md` e `config-rotina.json` alinhados ao novo fluxo.
- Novos artefatos: `data/observacoes.csv`, `data/alertas.csv`, `out/matriz_estado.json`.

## [2.0.0] - 2026-11-04

### 🎉 MUDANÇAS IMPORTANTES

#### ✅ Migração de Google Sheets para CSV

**ANTES:**
```
Agente → Google Sheets API → Dashboard lê Sheets API
```

**AGORA:**
```
Agente → Arquivos CSV → Dashboard lê CSV direto
```

**Vantagens:**
- ✅ **Sem autenticação OAuth** (eliminou Google Service Account)
- ✅ **Mais simples** de configurar e manter
- ✅ **Mais rápido** (sem API calls)
- ✅ **Portável** (funciona offline)
- ✅ **Transparente** (arquivos legíveis facilmente)

### 📁 Novos Arquivos

#### Armazenamento CSV
- `bot/lib/csv-storage.ts` - Cliente para salvar/ler CSVs
- `data/` - Diretório onde os CSVs são salvos:
  - `voos_ativos.csv`
  - `milhas_ativas.csv`
  - `historico.csv`
  - `logs.csv`
  - `estatisticas.json`

#### Dashboard Streamlit
- `dashboard/app.py` - Dashboard interativo
- `dashboard/requirements.txt` - Dependências Python
- `dashboard/README.md` - Documentação do dashboard

#### Scripts e Configuração
- `testar-csv.js` - Script de teste de integração
- `setup.sh` - Setup automático (Linux/Mac)
- `setup.bat` - Setup automático (Windows)
- `.env.example` - Exemplo de configuração
- `.gitignore` - Ignora dados sensíveis

#### Documentação
- `SETUP_CSV.md` - Guia completo do sistema CSV
- `CHANGELOG.md` - Este arquivo

### 🔄 Arquivos Modificados

#### `bot/tools/atualizar-planilha.ts`
- ❌ Removido: Integração com Google Sheets
- ✅ Adicionado: Integração com CSV Storage
- Funções adaptadas:
  - `atualizarVoos()` → salva em CSV
  - `atualizarMilhas()` → salva em CSV
  - `moverParaHistorico()` → append em CSV
  - `registrarLog()` → append em CSV

#### `README.md`
- Atualizado para refletir arquitetura CSV
- Removidas instruções do Google Sheets
- Adicionadas instruções do CSV + Streamlit

#### `package.json`
- Mantido (sem mudanças nas dependências)

### 📊 Dashboard Streamlit

#### Funcionalidades
- ✨ **Header visual** com gradiente
- 📊 **5 métricas principais**:
  - Total de oportunidades
  - Novas na semana
  - Maior desconto
  - Melhor custo por milheiro
  - Data da última atualização
- 🎴 **Cards de destaque** (top 3 voos)
- 📋 **Tabela filtrada** de oportunidades
- 🔍 **Filtros avançados**:
  - Origem
  - Destino
  - Tipo de voo
  - Preço máximo
- 🔄 **Atualização automática** (cache 5 min)
- 📱 **Responsivo** (desktop/tablet/mobile)

#### Abas
1. **✈️ Passagens Aéreas**
2. **💳 Promoções de Milhas**
3. **🎯 Oportunidades Combinadas** (em breve)

### 🚀 Como Usar

#### Setup Rápido

**Linux/Mac:**
```bash
./setup.sh
```

**Windows:**
```bat
setup.bat
```

#### Manual

1. **Configurar variáveis:**
```bash
cp .env.example .env
nano .env  # Adicionar KIWI_API_KEY
```

2. **Instalar dependências:**
```bash
npm install
cd dashboard && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

3. **Testar integração:**
```bash
node testar-csv.js
```

4. **Iniciar dashboard:**
```bash
cd dashboard
export CSV_DATA_DIR=../data
streamlit run app.py
```

5. **Testar agente:**
```bash
npx @grok/agent-sdk serve --dir . --mode single --dev
```

### 🗑️ Removido

#### Dependências Desnecessárias
- ❌ `googleapis` (Google Sheets API)
- ❌ `google-auth-library`
- ❌ Service Account credentials

#### Código Legado
- ❌ `bot/lib/sheets-client.ts` (mantido por compatibilidade, mas não mais usado)
- ❌ Referências a `GOOGLE_SHEETS_ID`
- ❌ Referências a `credentials.json`

#### Ferramentas
- ❌ `bot/tools/enviar-email.ts` (mantido opcional, mas não mais no schedule)
- ❌ Configurações SMTP do .env (opcional)

### 📝 Variáveis de Ambiente

#### Obrigatórias
```bash
KIWI_API_KEY=sua-chave-aqui
```

#### Opcionais
```bash
CSV_DATA_DIR=./data  # Padrão: ./data
ORIGENS=GRU,CGH,VCP
DESTINOS=CDG,LIS,BCN,FCO,MAD
# ... (ver .env.example)
```

### 🔧 Configuração

#### Agente (Node.js)
```typescript
import { CSVStorage } from './bot/lib/csv-storage.js';

const storage = new CSVStorage();
await storage.salvarVoos(voos);
await storage.salvarMilhas(milhas);
await storage.salvarEstatisticas(stats);
```

#### Dashboard (Python)
```python
import pandas as pd
import os

DATA_DIR = os.environ.get('CSV_DATA_DIR', './data')
voos_df = pd.read_csv(os.path.join(DATA_DIR, 'voos_ativos.csv'))
```

### 🐛 Correções

- ✅ Removida complexidade de autenticação OAuth
- ✅ Eliminados rate limits da Google Sheets API
- ✅ Sem dependência de conexão internet (após buscar voos)
- ✅ Dados persistem localmente

### 📚 Documentação

Documentação completa disponível em:
- `README.md` - Visão geral e instruções básicas
- `SETUP_CSV.md` - Sistema CSV detalhado
- `SETUP_APIS.md` - Configuração de APIs externas
- `dashboard/README.md` - Customização do dashboard

### 🎯 Próximos Passos

- [ ] Adicionar gráficos de evolução de preços
- [ ] Implementar notificações via Telegram
- [ ] Adicionar mapa interativo de destinos
- [ ] Criar alertas customizados por usuário
- [ ] Implementar comparação com emissão de milhas
- [ ] Deploy automatizado no Streamlit Cloud

### 🔄 Migração

Se você está usando a versão anterior com Google Sheets:

1. **Backup**: Exporte seus dados do Sheets
2. **Atualizar**: `git pull` para pegar as mudanças
3. **Setup**: Execute `./setup.sh` ou `setup.bat`
4. **Configurar**: Edite `.env` com sua `KIWI_API_KEY`
5. **Testar**: Execute `node testar-csv.js`
6. **Dashboard**: Inicie o Streamlit

Seus dados antigos do Google Sheets não serão migrados automaticamente. Para importar:

```bash
# Exportar do Sheets → CSV manualmente
# Mover para data/voos_ativos.csv
# O agente substituirá na próxima execução
```

### 🤝 Contribuindo

Sugestões e melhorias são bem-vindas! Veja a seção "Próximos Passos" acima.

### 📄 Licença

Uso privado/pessoal.

---

**Versão Anterior:** 1.0.0 (Google Sheets + E-mail)  
**Versão Atual:** 2.0.0 (CSV + Streamlit)  
**Data:** 04 de Novembro de 2026
