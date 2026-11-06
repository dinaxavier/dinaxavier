# 📁 Diretório de Dados

Este diretório contém os arquivos CSV gerados pela rotina (matriz + baseline + alerta).

## 📋 Arquivos

- **observacoes.csv** - Histórico append-only de preços por célula (rota × datas)
- **voos_ativos.csv** - Alertas ativos (células ≥ desconto mínimo vs baseline)
- **alertas.csv** - Espelho enxuto dos alertas ativos
- **milhas_ativas.csv** - Promoções de compra de milhas
- **historico.csv** - Histórico legado
- **logs.csv** - Logs de execução do agente
- **estatisticas.json** - Resumo da última rodada

## 🔄 Atualização

Estes arquivos são atualizados:

### Automaticamente
- **Toda segunda-feira às 06:00 BRT** via GitHub Actions
- Workflow: `.github/workflows/atualizar-dados.yml`

### Manualmente
```bash
cd /workspace/voos-milhas-monitor
node testar-csv.js
git add data/ && git commit -m "data: update" && git push
```

## 🚫 .gitignore

Por padrão, os CSVs estão em `.gitignore` para evitar commits desnecessários.

Para incluí-los no Git (necessário para deploy):

```bash
# Remover da .gitignore
sed -i '/data\//d' .gitignore

# Commitar dados
git add data/
git commit -m "data: adicionar dados iniciais"
git push
```

## 💡 Dicas

### Backup
```bash
# Backup local
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restaurar
tar -xzf backup-20261104.tar.gz
```

### Limpar histórico antigo
```bash
# Manter apenas últimos 3 meses
# Adicionar ao agente ou script cron
```

### Verificar tamanho
```bash
du -sh data/
ls -lh data/
```
