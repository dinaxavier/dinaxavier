# Rotina semanal — Radar de Voos e Milhas

Disparo: toda segunda-feira, 07:00 (America/Sao_Paulo). No agendador em UTC isso é 10:00. Cloud Agent — o computador pode estar desligado.

Não usa Kiwi, Travelpayouts nem qualquer programa de afiliados. Não envia e-mail. O dashboard lê o CSV que esta rotina atualiza.

## Prompt para a automação

```
Leia voos-milhas-monitor/config-rotina.json e voos-milhas-monitor/prompt-rotina-semanal.md.

1. Rode: python3 voos-milhas-monitor/scripts/listar_rotas.py
2. Para cada rota impressa, abra o link público do Google Flights no navegador.
3. Toda rota precisa sair de um aeroporto do Brasil (GRU, CGH, VCP ou CNF) para o destino. Descarte itinerário que comece em outro país.
4. Anote só o que estiver visível na página: menor preço em BRL por pessoa, companhia, datas de ida e volta dentro da janela do config, duração, link, conexões da ida, conexões da volta e se há mudança de aeroporto.
5. Mudança de aeroporto é quando a conexão chega em um aeroporto e o voo seguinte sai de outro, na mesma cidade ou não. Exemplos: CDG e ORY, LHR e LGW, EWR e JFK. Voo direto não tem mudança. Se a página não mostrar os aeroportos da conexão, grave mudanca_aeroporto como null. Não chute.
6. Não invente preço, data, companhia, número de conexões nem desconto. Se a página não abrir ou não mostrar preço, omita essa rota.
7. Grave o que foi visto em voos-milhas-monitor/out/cotacoes.json, neste formato:
   {
     "gerado_em": "AAAA-MM-DDTHH:MM:SS-03:00",
     "itens": [
       {
         "origem": "GRU",
         "destino": "LIS",
         "preco": 2500,
         "companhia": "TAP",
         "data_ida": "2027-01-15",
         "data_volta": "2027-01-25",
         "conexoes_ida": 1,
         "conexoes_volta": 1,
         "mudanca_aeroporto": false,
         "aeroportos_conexao": "LIS",
         "duracao_ida": "14h10",
         "duracao_volta": "13h40",
         "link": "https://...",
         "fonte": "Google Flights"
       }
     ]
   }
8. Rode: python3 voos-milhas-monitor/scripts/gravar_voos.py
   O script substitui a linha daquela origem e destino e mantém as rotas que não tiveram cotação nesta rodada.
9. Commit e push de:
   - voos-milhas-monitor/data/voos_ativos.csv
   - voos-milhas-monitor/data/estatisticas.json
   - voos-milhas-monitor/out/cotacoes.json
10. Resposta final curta em português: quantas rotas foram cotadas, quantas ficaram sem preço, quantas têm mudança de aeroporto, e se o CSV foi atualizado.
```

## Como ligar no Cursor

No editor de Automations:

| Campo | Valor |
|---|---|
| Repositório | dinaxavier/dinaxavier |
| Cloud Agent | Ativado |
| Agendamento | Segunda-feira, 07:00, fuso America/Sao_Paulo |
| Prompt | O bloco acima |

Não há segredo de API. Não há e-mail.

## O que a rotina não faz

- Não estima desconto contra um histórico que ela não viu.
- Não apaga uma passagem antiga quando a página daquela rota falha.
- Não abre cadastro de afiliado.
