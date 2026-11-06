# Rotina manual — Radar de Voos e Milhas (matriz + baseline + alerta)

Não há agendamento. A busca só roda quando alguém pede para atualizar os dados.

A rotina amostra uma fatia da **matriz de datas** (rota × ida × estadia), cotiza cada célula no Google Flights, grava a observação no histórico e emite **alerta** só quando o preço fica ≥ 25% abaixo do **baseline** (mediana das observações da rota nos últimos 90 dias). Sem baseline próprio ainda, usa a média/típico da página como bootstrap.

Não usa Kiwi, Travelpayouts nem afiliados. Não envia e-mail. Grava em `data/observacoes.csv`, `data/voos_ativos.csv` e `data/alertas.csv`.

## Prompt para a automação

```
Leia voos-milhas-monitor/config-rotina.json e voos-milhas-monitor/prompt-rotina-semanal.md.

1. Rode: python3 voos-milhas-monitor/scripts/listar_rotas.py
   Cada linha impressa é uma célula da matriz: origem, destino, data_ida, data_volta e link já com essas datas.
2. Para cada célula impressa, abra o link público do Google Flights no navegador.
3. Toda rota precisa sair de um aeroporto do Brasil (GRU, CGH, VCP, CNF ou SLZ — São Luís/MA) para o destino. Descarte itinerário que comece em outro país.
4. A célula já define ida, volta e estadia. Anote o menor preço em BRL por pessoa para exatamente essas datas (ida e volta). Se a página mostrar média ou preço típico da rota, anote em preco_medio (bootstrap do baseline). Se não mostrar, omita preco_medio — não invente. Anote também companhia, duração, conexões da ida, conexões da volta e se há mudança de aeroporto.
5. Mudança de aeroporto é quando a conexão chega em um aeroporto e o voo seguinte sai de outro. Exemplos: CDG e ORY, LHR e LGW, EWR e JFK. Voo direto não tem mudança. Se a página não mostrar os aeroportos da conexão, grave mudanca_aeroporto como null. Não chute.
6. Não invente preço, data, companhia, número de conexões nem desconto. O preço gravado é o menor valor de ida e volta visível no link da célula. Se a página não abrir ou não mostrar preço, omita essa célula.
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
   Use nas datas exatamente data_ida e data_volta da célula listada. preco_medio é opcional.
8. Rode: python3 voos-milhas-monitor/scripts/gravar_voos.py
   O script:
   - acrescenta cada cotação válida em data/observacoes.csv (histórico append-only);
   - calcula o baseline por rota (mediana dos últimos 90 dias; se ainda não houver 3 observações, usa preco_medio da página);
   - grava em data/voos_ativos.csv e data/alertas.csv só células com desconto ≥ desconto_minimo_percentual do config.
9. Commit e push de:
   - voos-milhas-monitor/data/voos_ativos.csv
   - voos-milhas-monitor/data/observacoes.csv
   - voos-milhas-monitor/data/alertas.csv
   - voos-milhas-monitor/data/estatisticas.json
   - voos-milhas-monitor/out/cotacoes.json
   - voos-milhas-monitor/out/matriz_estado.json
10. Resposta final curta em português: quantas células foram cotadas, quantas ficaram sem preço, quantas viraram alerta, quantas têm mudança de aeroporto, e se os CSVs foram atualizados.
```

## Quando rodar

Não crie automação semanal. Rode este prompt só quando a pessoa pedir para atualizar os dados.

Modelo: Composer 2.5, esforço baixo. A tarefa é ler o preço e a logística de cada célula listada.

## O que a rotina faz de diferente agora

- **Matriz**: cobre os próximos `meses_a_frente` (padrão 6); amostra rota × ida (a cada `passo_ida_dias`) × estadias com estratégia **espalhada** (várias datas por rota por rodada, não uma rota de cada vez).
- **Baseline**: histórico próprio em `data/observacoes.csv`; alerta compara com a mediana da rota, não só com o “melhor da página”.
- **Alerta**: só entra em `voos_ativos` / `alertas` se estiver ≥ X% abaixo da referência.

## O que a rotina não faz

- Não dispara sozinha nem em dia fixo.
- Não inventa média. Sem baseline suficiente e sem média na página, a observação é gravada mas não vira alerta.
- Não apaga uma passagem antiga quando a página daquela célula falha.
- Não abre cadastro de afiliado.
