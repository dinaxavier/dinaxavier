# 🌐 Deploy Gratuito - Dashboard Sempre Online

Este guia mostra **5 formas gratuitas** de deixar seu dashboard Streamlit disponível 24/7 na internet.

## 📊 Comparação Rápida

| Plataforma | Grátis? | Setup | Limitações | Recomendação |
|------------|---------|-------|------------|--------------|
| **Streamlit Cloud** | ✅ Sim | ⭐⭐⭐ Fácil | Apps públicos | **🏆 Melhor!** |
| **Render** | ✅ Sim | ⭐⭐ Médio | Sleep após inatividade | Boa |
| **Hugging Face** | ✅ Sim | ⭐⭐⭐ Fácil | Apps públicos | Ótima |
| **Railway** | ⚠️ $5 crédito | ⭐⭐ Médio | 500h/mês grátis | Boa |
| **Google Cloud Run** | ✅ Free tier | ⭐ Difícil | Complexo | Avançado |

---

## 🏆 Opção 1: Streamlit Community Cloud (RECOMENDADO!)

**Melhor opção:** Gratuito, simples, oficial!

### Características
- ✅ **100% gratuito** para apps públicos
- ✅ **Deploy automático** do GitHub
- ✅ **Sempre online** (não dorme)
- ✅ **SSL grátis** (HTTPS)
- ✅ **Atualização automática** ao fazer push

### Limitações
- ⚠️ App deve ser **público** (qualquer um pode acessar)
- ⚠️ Recursos limitados (1 GB RAM por app)
- ⚠️ Máximo 3 apps gratuitos

### Passo a Passo

#### 1. Preparar Repositório

```bash
cd /workspace/voos-milhas-monitor

# Criar arquivo de requisitos do Streamlit
cat > dashboard/requirements.txt << EOF
streamlit==1.31.0
pandas==2.2.0
EOF

# Criar arquivo de configuração do Streamlit
mkdir -p dashboard/.streamlit
cat > dashboard/.streamlit/config.toml << EOF
[server]
headless = true
port = 8501
enableCORS = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#1a1a2e"
font = "sans serif"
EOF

# Commitar
git add dashboard/
git commit -m "chore: preparar para deploy no Streamlit Cloud"
git push
```

#### 2. Deploy no Streamlit Cloud

1. Acesse: https://share.streamlit.io/
2. Clique em **"New app"**
3. Conecte sua conta GitHub
4. Selecione:
   - **Repository**: `dinaxavier/dinaxavier`
   - **Branch**: `main`
   - **Main file path**: `voos-milhas-monitor/dashboard/app.py`
5. Clique **"Deploy"**

#### 3. Configurar Secrets (Importante!)

Como o agente roda **localmente** e gera os CSVs, você tem duas opções:

**Opção A: Upload Manual dos CSVs (Simples)**

```bash
# Após cada execução do agente, commitar os CSVs
cd /workspace/voos-milhas-monitor
git add data/*.csv data/*.json
git commit -m "data: atualizar dados $(date)"
git push

# Dashboard atualiza automaticamente!
```

**Opção B: GitHub Actions (Automático)**

Criar `.github/workflows/atualizar-dados.yml`:

```yaml
name: Atualizar Dados Semanalmente

on:
  schedule:
    - cron: '0 9 * * 1'  # Segunda 09:00 UTC (06:00 BRT)
  workflow_dispatch:  # Permitir execução manual

jobs:
  buscar-voos:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Instalar dependências
        run: |
          cd voos-milhas-monitor
          npm install
      
      - name: Executar busca de voos
        env:
          KIWI_API_KEY: ${{ secrets.KIWI_API_KEY }}
        run: |
          cd voos-milhas-monitor
          node testar-csv.js
      
      - name: Commitar dados atualizados
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add voos-milhas-monitor/data/
          git diff --quiet && git diff --staged --quiet || git commit -m "data: atualizar $(date +%Y-%m-%d)"
      
      - name: Push changes
        uses: ad-m/github-push-action@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

Configurar secret no GitHub:
1. Vá em **Settings → Secrets → Actions**
2. Clique **"New repository secret"**
3. Nome: `KIWI_API_KEY`
4. Valor: sua chave da API
5. Salvar

#### 4. Configurar CSV_DATA_DIR

No Streamlit Cloud, clique em **"⋮ → Settings → Secrets"**:

```toml
CSV_DATA_DIR = "data"
```

#### 5. Pronto! 🎉

Seu dashboard estará em:
```
https://share.streamlit.io/dinaxavier/dinaxavier/main/voos-milhas-monitor/dashboard/app.py
```

Ou um domínio customizado como:
```
https://voos-milhas-dinaxavier.streamlit.app
```

---

## 🚀 Opção 2: Render.com

Alternativa ao Streamlit Cloud com algumas vantagens.

### Características
- ✅ Gratuito permanente
- ✅ Apps **privados** permitidos
- ⚠️ **Dorme após 15 min** de inatividade
- ⚠️ Acorda em ~30 segundos no primeiro acesso

### Passo a Passo

#### 1. Criar `render.yaml`

```yaml
services:
  - type: web
    name: voos-milhas-monitor
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r dashboard/requirements.txt
    startCommand: streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0
    envVars:
      - key: CSV_DATA_DIR
        value: data
      - key: PYTHON_VERSION
        value: 3.11.0
```

#### 2. Deploy

1. Acesse: https://render.com/
2. Conecte GitHub
3. **New → Web Service**
4. Selecione repositório `dinaxavier`
5. Configure:
   - **Name**: `voos-milhas-monitor`
   - **Root Directory**: `voos-milhas-monitor`
   - **Build**: `pip install -r dashboard/requirements.txt`
   - **Start**: `streamlit run dashboard/app.py --server.port=$PORT`
6. Deploy!

URL pública: `https://voos-milhas-monitor.onrender.com`

**Dica:** Para evitar sleep, use serviços como:
- **UptimeRobot** (ping a cada 5 min)
- **Cron-job.org** (requisições agendadas)

---

## 🤗 Opção 3: Hugging Face Spaces

Plataforma de ML com suporte Streamlit gratuito!

### Características
- ✅ 100% gratuito
- ✅ Sempre online
- ✅ Recursos generosos (16 GB RAM, 8 CPUs)
- ✅ Comunidade ativa

### Passo a Passo

#### 1. Criar Space

1. Acesse: https://huggingface.co/spaces
2. Clique **"Create new Space"**
3. Preencha:
   - **Space name**: `voos-milhas-monitor`
   - **License**: MIT
   - **Space SDK**: **Streamlit**
4. Criar!

#### 2. Configurar Arquivos

Hugging Face precisa de estrutura específica:

```bash
# Clonar o space
git clone https://huggingface.co/spaces/SEU_USUARIO/voos-milhas-monitor
cd voos-milhas-monitor

# Copiar arquivos do dashboard
cp ../workspace/voos-milhas-monitor/dashboard/app.py .
cp ../workspace/voos-milhas-monitor/dashboard/requirements.txt .

# Criar README.md
cat > README.md << EOF
---
title: Radar de Voos & Milhas
emoji: ✈️
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.31.0
app_file: app.py
pinned: false
---

# Radar de Voos & Milhas

Dashboard de monitoramento de oportunidades de viagem.
EOF

# Copiar dados (ou configurar atualização automática)
mkdir -p data
cp ../workspace/voos-milhas-monitor/data/* data/

# Commitar e push
git add .
git commit -m "Initial commit"
git push
```

#### 3. Pronto!

URL pública: `https://huggingface.co/spaces/SEU_USUARIO/voos-milhas-monitor`

---

## 🚂 Opção 4: Railway

Plataforma moderna com free tier generoso.

### Características
- ⚠️ $5 de crédito inicial (gratuito)
- ✅ 500 horas/mês grátis (~20 dias)
- ✅ Não dorme
- ✅ SSL grátis

### Passo a Passo

#### 1. Criar `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 2. Criar `nixpacks.toml`

```toml
[phases.setup]
nixPkgs = ['python39']

[phases.install]
cmds = ['pip install -r dashboard/requirements.txt']

[start]
cmd = 'streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0'
```

#### 3. Deploy

1. Acesse: https://railway.app/
2. **New Project → Deploy from GitHub repo**
3. Selecione `dinaxavier/dinaxavier`
4. Configure variáveis:
   - `CSV_DATA_DIR`: `voos-milhas-monitor/data`
5. Deploy!

URL: `https://voos-milhas-monitor.up.railway.app`

---

## ☁️ Opção 5: Google Cloud Run (Avançado)

Para quem quer controle total.

### Características
- ✅ Free tier: 2 milhões requisições/mês
- ✅ Sempre online (configurável)
- ⚠️ Requer Docker e gcloud CLI
- ⚠️ Setup complexo

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar app e dados
COPY dashboard/app.py .
COPY data/ ./data/

# Variáveis
ENV CSV_DATA_DIR=/app/data
ENV PORT=8080

# Expor porta
EXPOSE 8080

# Comando
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### Deploy

```bash
# Instalar gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Criar projeto
gcloud projects create voos-milhas-monitor

# Build e deploy
gcloud builds submit --tag gcr.io/voos-milhas-monitor/dashboard
gcloud run deploy dashboard \
  --image gcr.io/voos-milhas-monitor/dashboard \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CSV_DATA_DIR=/app/data
```

URL: `https://dashboard-xxxxx-uc.a.run.app`

---

## 🔒 Tornar Dashboard Privado (com senha)

### Opção A: Streamlit Secrets (simples)

```python
# dashboard/app.py (adicionar no início)
import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Senha", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Senha", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Senha incorreta")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Resto do app...
```

No Streamlit Cloud, adicionar em Secrets:
```toml
password = "sua-senha-aqui"
```

### Opção B: Cloudflare Access (grátis, profissional)

1. Adicionar site ao Cloudflare
2. Configurar **Access** com autenticação
3. Permitir apenas seu e-mail
4. Grátis até 50 usuários!

---

## 📊 Resumo: Qual Escolher?

### Para Iniciantes
✅ **Streamlit Cloud** - Mais fácil e rápido

### Para Apps Privados
✅ **Render** + UptimeRobot (evitar sleep)

### Para Projetos ML
✅ **Hugging Face Spaces** - Comunidade e recursos

### Para Protótipos
✅ **Railway** - $5 grátis é suficiente

### Para Produção
✅ **Google Cloud Run** - Escalável e confiável

---

## 🔄 Automatizar Atualização de Dados

Para qualquer opção acima, use **GitHub Actions** para atualizar dados semanalmente:

```yaml
# .github/workflows/atualizar-dados.yml
name: Atualizar Dados

on:
  schedule:
    - cron: '0 9 * * 1'  # Segunda 09:00 UTC
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18
      
      - name: Instalar deps
        run: |
          cd voos-milhas-monitor
          npm install
      
      - name: Buscar voos
        env:
          KIWI_API_KEY: ${{ secrets.KIWI_API_KEY }}
        run: |
          cd voos-milhas-monitor
          node testar-csv.js
      
      - name: Commit e push
        run: |
          git config user.name "Bot"
          git config user.email "bot@github.com"
          git add voos-milhas-monitor/data/
          git commit -m "data: update $(date)" || exit 0
          git push
```

Adicionar `KIWI_API_KEY` nos **Secrets do GitHub**.

---

## 💡 Dicas Finais

### Performance
```python
# dashboard/app.py
@st.cache_data(ttl=3600)  # Cache 1 hora
def carregar_dados():
    # ...
```

### Monitoramento
- **UptimeRobot**: https://uptimerobot.com/ (gratuito)
- **Statuspage**: Avisar usuários se cair

### Domínio Próprio
- Registrar em **Registro.br** (~R$ 40/ano)
- Apontar para URL do Streamlit/Render
- Configurar SSL no Cloudflare (grátis)

### Backup
```bash
# Cron diário para backup dos CSVs
0 3 * * * cd /workspace/voos-milhas-monitor && tar -czf backup-$(date +\%Y\%m\%d).tar.gz data/
```

---

## 🎉 Próximos Passos

1. **Escolher plataforma** (recomendo Streamlit Cloud)
2. **Configurar GitHub Actions** para atualização automática
3. **Adicionar senha** (opcional)
4. **Compartilhar URL** com amigos/família!

## 📚 Recursos

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Render Docs](https://render.com/docs)
- [Hugging Face Docs](https://huggingface.co/docs/hub/spaces)
- [Railway Docs](https://docs.railway.app/)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

---

**Custo Total:** R$ 0,00/mês 💰  
**Tempo de Setup:** 10-30 minutos ⏱️  
**Resultado:** Dashboard profissional online 24/7! 🎉
