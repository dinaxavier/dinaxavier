# 🚀 Deploy no Streamlit Cloud - Guia Completo

Deploy **gratuito e fácil** do dashboard em 10 minutos!

## 📋 Pré-requisitos

- ✅ Conta no GitHub (você já tem!)
- ✅ Código commitado (já está!)
- ✅ Conta Streamlit Cloud (criar em 2 minutos)

## 🎯 Passo a Passo

### 1️⃣ Criar Conta no Streamlit Cloud

1. Acesse: https://share.streamlit.io/
2. Clique em **"Sign up"**
3. Escolha **"Continue with GitHub"**
4. Autorize o Streamlit Cloud
5. ✅ Pronto!

### 2️⃣ Fazer Deploy

1. No Streamlit Cloud, clique em **"New app"**

2. Preencha as informações:
   ```
   Repository: dinaxavier/dinaxavier
   Branch: main
   Main file path: voos-milhas-monitor/dashboard/app.py
   App URL (opcional): voos-milhas-monitor
   ```

3. Clique em **"Advanced settings"** (opcional)

4. Em **"Secrets"**, adicione:
   ```toml
   # Deixar vazio por enquanto
   # Dados virão do GitHub
   ```

5. Clique em **"Deploy!"**

6. Aguarde 2-3 minutos...

7. ✅ **Dashboard no ar!**

### 3️⃣ Sua URL Pública

Após o deploy, seu dashboard estará em:

```
https://voos-milhas-monitor-dinaxavier.streamlit.app
```

Ou:
```
https://share.streamlit.io/dinaxavier/dinaxavier/main/voos-milhas-monitor/dashboard/app.py
```

## 🔄 Configurar Atualização Automática de Dados

### Opção A: GitHub Actions (Recomendado)

Já configurado! Só precisa adicionar a chave da API:

1. Vá em seu repositório GitHub
2. **Settings → Secrets and variables → Actions**
3. Clique **"New repository secret"**
4. Preencha:
   ```
   Name: KIWI_API_KEY
   Value: sua-chave-aqui
   ```
5. Salvar

Pronto! O workflow `.github/workflows/atualizar-dados.yml` irá:
- Executar toda **segunda-feira às 06:00 BRT**
- Buscar novos voos
- Atualizar CSVs no GitHub
- Dashboard atualiza automaticamente! 🎉

### Testar Manualmente

1. Vá em **Actions** no GitHub
2. Selecione **"Atualizar Dados Semanalmente"**
3. Clique **"Run workflow"**
4. Aguarde 2-3 minutos
5. ✅ Dados atualizados!

### Opção B: Commitar Manualmente (Simples)

Após executar o agente localmente:

```bash
cd /workspace/voos-milhas-monitor

# Executar busca
node testar-csv.js

# Commitar dados
git add data/
git commit -m "data: atualizar $(date +%Y-%m-%d)"
git push

# Dashboard atualiza automaticamente em ~1 minuto!
```

## 🔐 Adicionar Senha (Opcional)

### 1. Atualizar `dashboard/app.py`

Adicione no **início do arquivo**, logo após os imports:

```python
def check_password():
    """Retorna True se a senha estiver correta."""
    def password_entered():
        if st.session_state["password"] == st.secrets.get("password", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "🔒 Senha",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Digite a senha"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "🔒 Senha",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Digite a senha"
        )
        st.error("😕 Senha incorreta")
        return False
    else:
        return True

# Bloquear acesso sem senha
if not check_password():
    st.stop()
```

### 2. Configurar Senha no Streamlit Cloud

1. No dashboard do Streamlit Cloud, clique em **"⋮ → Settings"**
2. Na aba **"Secrets"**, adicione:
   ```toml
   password = "sua-senha-super-secreta"
   ```
3. Salvar
4. ✅ Dashboard protegido!

Agora só quem tiver a senha poderá acessar! 🔒

## 📱 Compartilhar com Amigos/Família

### Link Direto

Compartilhe a URL pública:
```
https://voos-milhas-monitor-dinaxavier.streamlit.app
```

### QR Code

Gere um QR code para facilitar:

1. Acesse: https://www.qr-code-generator.com/
2. Cole sua URL
3. Baixe o QR code
4. Compartilhe por WhatsApp!

### Adicionar à Home (Mobile)

**iPhone:**
1. Abra a URL no Safari
2. Toque no ícone de compartilhar
3. **"Adicionar à Tela de Início"**
4. ✅ App instalado!

**Android:**
1. Abra a URL no Chrome
2. Menu **"⋮ → Adicionar à tela inicial"**
3. ✅ App instalado!

## 🎨 Personalizar Visual

### Logo Customizado

1. Crie um logo 200x200px
2. Salve como `dashboard/logo.png`
3. Atualize `app.py`:
   ```python
   st.image('logo.png', width=60)
   st.markdown("# Radar de Voos & Milhas")
   ```
4. Commit e push!

### Cores do Tema

Edite `dashboard/.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF4B4B"      # Vermelho
backgroundColor = "#0E1117"    # Fundo escuro
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
```

## 📊 Monitorar Tráfego

### Google Analytics (Opcional)

1. Crie uma propriedade no Google Analytics
2. Copie o ID de medição (G-XXXXXXXXXX)
3. No Streamlit Cloud, **Settings → Secrets**:
   ```toml
   GA_TRACKING_ID = "G-XXXXXXXXXX"
   ```
4. Adicione no `app.py`:
   ```python
   import streamlit.components.v1 as components
   
   ga_id = st.secrets.get("GA_TRACKING_ID", "")
   if ga_id:
       components.html(f"""
           <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
           <script>
             window.dataLayer = window.dataLayer || [];
             function gtag(){{dataLayer.push(arguments);}}
             gtag('js', new Date());
             gtag('config', '{ga_id}');
           </script>
       """)
   ```

## 🚨 Troubleshooting

### Dashboard não inicia

**Erro:** `ModuleNotFoundError: No module named 'pandas'`

**Solução:**
```bash
# Verificar requirements.txt
cat dashboard/requirements.txt

# Deve conter:
streamlit==1.31.0
pandas==2.2.0
```

### Erro ao carregar dados

**Erro:** `FileNotFoundError: data/voos_ativos.csv`

**Solução:**
1. Commitar dados de exemplo:
   ```bash
   git add voos-milhas-monitor/data/
   git commit -m "data: adicionar dados iniciais"
   git push
   ```

2. Ou executar GitHub Actions manualmente

### App reiniciando constantemente

**Causa:** Erro no código

**Solução:**
1. Ver logs no Streamlit Cloud (botão **"Manage app"**)
2. Corrigir erro
3. Commit e push
4. Deploy automático

### Dados não atualizam

**Verificar:**
1. GitHub Actions está rodando? (**Actions** tab)
2. `KIWI_API_KEY` configurada nos Secrets?
3. Workflow executou sem erros?

**Forçar atualização:**
```bash
# Localmente
node testar-csv.js
git add data/ && git commit -m "data: update" && git push
```

## 💡 Dicas Pro

### 1. Domínio Customizado

Streamlit Cloud suporta domínios próprios!

1. Compre domínio (ex: `voosmilhas.com.br`)
2. No Streamlit Cloud: **Settings → Custom Domain**
3. Adicione o domínio
4. Configure DNS (CNAME)
5. ✅ `https://voosmilhas.com.br`

### 2. Evitar Sleep no Render (alternativa)

Se usar Render.com em vez de Streamlit Cloud:

**UptimeRobot** (gratuito):
1. https://uptimerobot.com/
2. Adicione monitor HTTP(s)
3. URL: sua URL do Render
4. Intervalo: 5 minutos
5. ✅ App sempre acordado!

### 3. Notificações

Adicione notificações quando dados atualizarem:

**Telegram:**
```python
# dashboard/app.py
def enviar_telegram(mensagem):
    bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID")
    
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id,
            "text": mensagem
        })
```

### 4. Backup Automático

GitHub já é seu backup! Mas para redundância:

```yaml
# .github/workflows/backup.yml
name: Backup Semanal
on:
  schedule:
    - cron: '0 0 * * 0'  # Domingo meia-noite

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Criar backup
        run: |
          tar -czf backup-$(date +%Y%m%d).tar.gz voos-milhas-monitor/data/
      
      - name: Upload para releases
        uses: softprops/action-gh-release@v1
        with:
          files: backup-*.tar.gz
          tag_name: backup-$(date +%Y%m%d)
```

## 🎉 Pronto!

Você agora tem:

- ✅ Dashboard online 24/7
- ✅ URL pública para compartilhar
- ✅ Atualização automática semanal
- ✅ SSL/HTTPS grátis
- ✅ Zero custo mensal
- ✅ Deploy em 10 minutos

## 📚 Recursos

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Streamlit Components](https://streamlit.io/components)

## 🆘 Suporte

Problemas? Opções:

1. **Logs do Streamlit Cloud** (botão "Manage app")
2. **GitHub Actions logs** (aba Actions)
3. **Documentação** em `DEPLOY_GRATIS.md`
4. **Fórum Streamlit**: https://discuss.streamlit.io/

---

**Tempo total:** ~10 minutos ⏱️  
**Custo:** R$ 0,00/mês 💰  
**URL pública:** ✅  
**Atualizações automáticas:** ✅  
**SSL/HTTPS:** ✅
