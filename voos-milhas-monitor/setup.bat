@echo off
REM ============================================
REM SETUP RÁPIDO - MONITOR DE VOOS E MILHAS
REM ============================================

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║  SETUP - MONITOR DE VOOS E MILHAS               ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM 1. Verificar Node.js
echo 📦 Verificando Node.js...
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Node.js não encontrado
    echo   Instale em: https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node.js %NODE_VERSION%

REM 2. Verificar Python
echo 🐍 Verificando Python...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Python não encontrado
    echo   Instale em: https://www.python.org/
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ %PYTHON_VERSION%

REM 3. Criar .env se não existir
echo.
echo ⚙️  Configurando variáveis de ambiente...
if not exist .env (
    copy .env.example .env
    echo ✓ Arquivo .env criado
    echo ⚠ Configure sua KIWI_API_KEY no arquivo .env
) else (
    echo ⚠ .env já existe (mantendo configuração atual^)
)

REM 4. Criar diretório de dados
echo.
echo 📁 Criando diretório de dados...
if not exist data mkdir data
echo ✓ Diretório .\data criado

REM 5. Instalar dependências Node.js
echo.
echo 📦 Instalando dependências Node.js...
call npm install
echo ✓ Dependências Node.js instaladas

REM 6. Configurar dashboard Python
echo.
echo 🐍 Configurando dashboard Streamlit...
cd dashboard

if not exist venv (
    echo   Criando ambiente virtual...
    python -m venv venv
    echo ✓ Ambiente virtual criado
)

echo   Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo   Instalando dependências Python...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo ✓ Dependências Python instaladas

cd ..

REM 7. Validar agente
echo.
echo ✅ Validando agente...
call npx @grok/agent-sdk validate --dir .

REM 8. Resultado final
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║  SETUP CONCLUÍDO!                                ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo 📋 PRÓXIMOS PASSOS:
echo.
echo 1. Configure sua KIWI_API_KEY:
echo    notepad .env
echo    Obtenha em: https://partners.kiwi.com/
echo.
echo 2. Teste a integração:
echo    node testar-csv.js
echo.
echo 3. Inicie o dashboard:
echo    cd dashboard
echo    venv\Scripts\activate
echo    set CSV_DATA_DIR=..\data
echo    streamlit run app.py
echo.
echo 4. Teste o agente no playground:
echo    npx @grok/agent-sdk serve --dir . --mode single --dev
echo    Acesse: http://localhost:3000/playground
echo.
echo 📚 Documentação:
echo    • README.md - Visão geral
echo    • SETUP_CSV.md - Detalhes do sistema CSV
echo    • SETUP_APIS.md - Configuração de APIs
echo    • dashboard\README.md - Customização do dashboard
echo.

pause
