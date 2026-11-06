# Rotina manual — Radar de Voos e Milhas

Não há agendamento. A busca só roda quando alguém pede para atualizar os dados.

Não usa Kiwi, Travelpayouts nem qualquer programa de afiliados. Não envia e-mail. A rotina grava o que viu em `data/voos_ativos.csv`. Entra só ida e volta, de 7 a 15 dias, com o preço pelo menos 25% abaixo da média vista na página.

## Prompt para a automação

```
Leia voos-milhas-monitor/config-rotina.json e voos-milhas-monitor/prompt-rotina-semanal.md.

1. Rode: python3 voos-milhas-monitor/scripts/listar_rotas.py
2. Para cada rota impressa, abra o link público do Google Flights no navegador.
3. Toda rota precisa sair de um aeroporto do Brasil (GRU, CGH, VCP ou CNF) para o destino. Descarte itinerário que comece em outro país.
4. Procure só passagem de ida e volta, com estadia de 7 a 15 dias, dentro da janela de datas do config. Estadia é a diferença em dias entre a data de ida e a data de volta. Descarte só ida e o que ficar fora dessa faixa. Anote o menor preço em BRL por pessoa e a média ou o preço típico que a página mostrar para essa ida e volta. Grave a média em preco_medio. O desconto é (média − preço) / média. Só grave a rota se esse desconto for de pelo menos 25%. Se a página não mostrar a média, omita a rota. Não invente a média. Anote também companhia, datas, duração, link da página de ida e volta, conexões da ida, conexões da volta e se há mudança de aeroporto.
5. Mudança de aeroporto é quando a conexão chega em um aeroporto e o voo seguinte sai de outro, na mesma cidade ou não. Exemplos: CDG e ORY, LHR e LGW, EWR e JFK. Voo direto não tem mudança. Se a página não mostrar os aeroportos da conexão, grave mudanca_aeroporto como null. Não chute.
6. Não invente preço, data, companhia, número de conexões nem desconto. O preço gravado é o menor valor de ida e volta visível no link. Se a página disser que os preços estão normais ou altos, isso não é desconto. Se a página não abrir ou não mostrar preço, omita essa rota.
7. Grave o que foi visto em voos-milhas-monitor/out/cotacoes.json, neste formato:
   {
     "gerado_em": "AAAA-MM-DDTHH:MM:SS-03:00",
     "itens": [
       {
         "origem": "GRU",
         "destino": "LIS",
         "preco": 2500,
         "preco_medio": 4000,
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

## Quando rodar

Não crie automação semanal. Rode este prompt só quando a pessoa pedir para atualizar os dados.

Modelo: Composer 2.5, esforço baixo. A tarefa é ler o preço, as conexões e a troca de aeroporto que aparecem na página.

## O que a rotina não faz

- Não dispara sozinha nem em dia fixo.
- Não estima a média. O desconto só vale quando a página mostra o preço típico ou a média, e o preço está pelo menos 25% abaixo.
- Não apaga uma passagem antiga quando a página daquela rota falha.
- Não abre cadastro de afiliado.
