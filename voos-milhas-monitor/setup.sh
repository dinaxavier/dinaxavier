#!/bin/bash

# ============================================
# SETUP RÁPIDO - MONITOR DE VOOS E MILHAS
# ============================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  SETUP - MONITOR DE VOOS E MILHAS               ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar Node.js
echo "📦 Verificando Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js não encontrado${NC}"
    echo "  Instale em: https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}✓ Node.js $(node --version)${NC}"

# 2. Verificar Python
echo "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 não encontrado${NC}"
    echo "  Instale em: https://www.python.org/"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version)${NC}"

# 3. Criar .env se não existir
echo ""
echo "⚙️  Configurando variáveis de ambiente..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Arquivo .env criado${NC}"
    echo -e "${YELLOW}⚠ Configure sua KIWI_API_KEY no arquivo .env${NC}"
else
    echo -e "${YELLOW}⚠ .env já existe (mantendo configuração atual)${NC}"
fi

# 4. Criar diretório de dados
echo ""
echo "📁 Criando diretório de dados..."
mkdir -p data
echo -e "${GREEN}✓ Diretório ./data criado${NC}"

# 5. Instalar dependências Node.js
echo ""
echo "📦 Instalando dependências Node.js..."
npm install
echo -e "${GREEN}✓ Dependências Node.js instaladas${NC}"

# 6. Configurar dashboard Python
echo ""
echo "🐍 Configurando dashboard Streamlit..."
cd dashboard

if [ ! -d "venv" ]; then
    echo "  Criando ambiente virtual..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Ambiente virtual criado${NC}"
fi

echo "  Ativando ambiente virtual..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

echo "  Instalando dependências Python..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓ Dependências Python instaladas${NC}"

cd ..

# 7. Validar agente
echo ""
echo "✅ Validando agente..."
npx @grok/agent-sdk validate --dir . || echo -e "${YELLOW}⚠ Validação com warnings (normal)${NC}"

# 8. Resultado final
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  SETUP CONCLUÍDO!                                ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Configure sua KIWI_API_KEY:"
echo "   ${GREEN}nano .env${NC}"
echo "   Obtenha em: https://partners.kiwi.com/"
echo ""
echo "2. Teste a integração:"
echo "   ${GREEN}node testar-csv.js${NC}"
echo ""
echo "3. Inicie o dashboard:"
echo "   ${GREEN}cd dashboard${NC}"
echo "   ${GREEN}source venv/bin/activate${NC}"
echo "   ${GREEN}export CSV_DATA_DIR=../data${NC}"
echo "   ${GREEN}streamlit run app.py${NC}"
echo ""
echo "4. Teste o agente no playground:"
echo "   ${GREEN}npx @grok/agent-sdk serve --dir . --mode single --dev${NC}"
echo "   Acesse: http://localhost:3000/playground"
echo ""
echo "📚 Documentação:"
echo "   • README.md - Visão geral"
echo "   • SETUP_CSV.md - Detalhes do sistema CSV"
echo "   • SETUP_APIS.md - Configuração de APIs"
echo "   • dashboard/README.md - Customização do dashboard"
echo ""
