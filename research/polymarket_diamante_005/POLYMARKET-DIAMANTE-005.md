# POLYMARKET-DIAMANTE-005

26 de novembro de 2026 · Reconstrução independente · BTC Up/Down 5 minutos · 8–21 de agosto de 2026 UTC

**Decisão económica: NO-GO para avançar com capital.** A hipótese de replicação por execução passiva ou híbrida permanece inconclusiva. A DIAMANTE-004 foi reproduzida com o seu perímetro de resultados e um modelo de comissões calibrado com recibos on-chain.

## Evidência histórica

| Métrica | Catálogo original | Catálogo completado pela Gamma |
|---|---:|---:|
| Mercados em que a carteira operou e com resultado disponível | 3 553 | 3 592 |
| Execuções da carteira | 163 637 | 165 435 |
| Compras | $2 074 292,39 | $2 097 338,91 |
| Valor teórico na liquidação | $2 139 563,90 | $2 163 389,14 |
| Comissões modeladas | $48 000,48 | $48 559,53 |
| PnL líquido modelado, excluindo incentivos | +$17 271,03 | +$17 490,70 |
| Margem sobre compras | 0,8326% | 0,8339% |
| PnL líquido dos pares FIFO | +$13 877,44 | +$14 223,70 |

A carteira tem 165 435 registos próprios entre 21 336 165 eventos do universo. Chaves transação/log sem duplicados nem nulos. Todos os eventos juntaram ao catálogo de 4 032 mercados. No dia 8, 4 945 execuções, 279 mercados, +$2 163,66 líquido modelado, +$1 783,43 nos pares e +$380,23 no residual reproduzem o resumo da DIAMANTE-003. Recuperaram-se os resumos das fases anteriores e os seus insumos públicos, com código reconstruído nesta operação. A origem exata do artigo e os artefactos completos das fases 001–004 não foram localizados.

O campo maker identifica o titular da ordem no OrderFilled. Quando o campo taker contém o contrato CTF Exchange V2, o evento descreve a ordem agressora agregada. As referências à carteira como contraparte dos makers não constituem um segundo fluxo próprio. A ordenação histórica usa instante do bloco Polygon e log index dentro do bloco. Dois fills da carteira têm timestamp de bloco posterior ao fecho. A inclusão preserva a reconstrução contabilística. Esses timestamps não demonstram que era possível iniciar novas ordens depois do fecho.

A Gamma devolveu 42 resultados resolvidos em falta, com preços finais 0/1. A carteira operou em 39 desses mercados. A inclusão acrescentou $219,66 ao PnL modelado. O payout é o direito económico inferido da posição comprada e do vencedor. O estudo não reconciliou resgates, merges, transferências, outros endereços, inventário fora da amostra, incentivos efetivamente recebidos ou custos operacionais da carteira.

## Comissões

Modelo para taker: quantidade × 0,07 × preço × (1 − preço). Modelo maker: zero. Verificaram-se 56 eventos estratificados por data e papel com recibos Polygon públicos, ligados por hash e log index. Os montantes do Parquet conferiram nos 56. As 28 comissões maker foram zero. As 28 taker somaram $17,684 observados face a $17,68408187 modelados. Erro absoluto máximo de $0,00000943. Os agregados globais continuam modelados. O endpoint dRPC reportou um limite gratuito de 100 blocos por pesquisa, e as outras respostas RPC pediram credencial de arquivo ou devolveram erro 403. O intervalo total de 803 341 blocos exigiria pelo menos 8 034 consultas consecutivas sob esse limite. Há evidência pontual verificável em fee_sample.json e receipt_example.json.

A margem no perímetro original é de 83,26 pontos base sobre compras. Uma degradação agregada desse tamanho anula o resultado observado. Com 1,25× as comissões modeladas, o mesmo conjunto de fills renderia +$5 270,91. Com 1,5×, −$6 729,21. O limiar é condicional aos mesmos fills, sem supor que outra conta os obteria.

## Mecanismo e cobertura de execução

Os pares somam 80,35% do PnL original. O FIFO foi positivo em 14/14 dias. O resultado total foi negativo em três. Os pares levaram em média 21,62 s a completar, ponderados por quantidade e medidos por timestamps de bloco. Cerca de 3,11% das unidades emparelhadas situaram-se no mesmo segundo de bloco. O desvio máximo entre UP e DOWN acumulado num mercado foi 1 088,10 contratos na amostra de resultados conhecida. A perda por mercado mais alta foi $641,33. Por papel das duas pernas, maker/maker contribuiu +$2 524,62, maker/taker +$6 746,35 e taker/taker +$4 606,47. A presença material dos pares taker/taker é compatível com execução sequencial e deixa em aberto a regra de timing. O emparelhamento agrega a posição retrospetivamente e o lucro depende da aquisição anterior de dois lados. O teste não identifica a regra que decidiu comprar o primeiro lado, nem mede intenção de cobertura, gestão de inventário ou impacto causal de volatilidade e desequilíbrio.

Em 8 de agosto, o piloto inspecionou 22 799 260 observações de cotação durante as janelas dos 288 mercados, 22 022 622 com preços dos dois lados utilizáveis, e 408 860 mensagens de tape. Nenhum cruzamento foi observado nas cotações utilizáveis. Na representação complementar do fornecedor, comprar imediatamente UP e DOWN custa ask(UP) + 1 − bid(UP), ou 1 + spread, antes das comissões. A baseline simultânea deu zero candidatos e zero capital usado para $100, $250, $500, $1 000 e $5 000. O resultado aplica-se à baseline instantânea de dois takers sob essa representação. A captura L2 tem mediana de 4,55 ms e p99 de 22,51 ms face ao timestamp do evento no piloto. Esse atraso mede a recolha, sem medir a ida e volta das ordens da carteira.

O mercado oficial piloto resolveu pela TWAP de 30 s. O dataset fornece spot e TWAP de 60 s no piloto. A Gamma também reporta TWAP de 60 s em parte dos mercados recuperados. Usar TWAP de 60 s de forma uniforme ou preencher antecipadamente uma lacuna por meio do preço final contaminaria as inferências. O Chainlink de 60 s tem latência local mediana de 1,337 s, p99 de 2,178 s e extremos mapeados em pilot.json. O ficheiro de referência disponível no piloto tem 82 666 segundos de observação distintos. Os fills Polygon têm relógio por bloco, inadequado para ligar a cada execução a cotação imediatamente anterior. A ligação defensável exige identificador comum ou intervalo explícito de incerteza e o feed de referência contratual de cada mercado.

## Robustez e veredito

O bootstrap circular descritivo usa 10 000 reamostragens de blocos de dois dias e devolve uma banda de margem de +0,330% a +1,317% para o histórico contabilizado com as mesmas regras. O intervalo é interno a 14 dias já conhecidos. Não há split independente executado ou freeze pré-outcome para uma regra maker/híbrida, nem base para atribuir o resultado a momentum, reversão, seleção adversa, desequilíbrio ou divergência de probabilidade.

| Dimensão | Veredito | Âmbito |
|---|---|---|
| Rentabilidade histórica | GO | Resultado histórico reconstruído e sem incentivos na fórmula. Comissões estimadas globalmente e conferidas numa amostra estratificada. |
| Mecanismo económico | INCONCLUSIVO | Emparelhamento comprovado na decomposição. A decisão de entrada permanece sem identificação causal. Dois takers simultâneos recusados no piloto. |
| Replicabilidade independente | INCONCLUSIVO | Replay maker/híbrido com fila, latência, slippage, preenchimentos parciais e risco da segunda perna por demonstrar. |
| Robustez estatística | INCONCLUSIVO | Reamostragem histórica exploratória. Falta teste cego e ablações causais. |
| Pequeno capital | INCONCLUSIVO | Cinco capitais na baseline simultânea, todos sem entradas. Escala do mecanismo sequencial por determinar. |
| Infraestrutura especializada | INCONCLUSIVO | Captura de baixa latência e prioridade de fila relevantes, sem medição causal da sensibilidade da estratégia. |
| Viabilidade após todos os custos | NO-GO | Critério para avançar com capital. O edge executável por outra conta ainda não foi demonstrado. |

O replay completo deve avaliar uma regra que seja observável antes da primeira compra e um limite causal para completar ou abandonar a segunda. A série de 8–21 de agosto já foi consultada para reconstruir a carteira. Um teste de confirmação deverá congelar os critérios de aprovação antes de abrir uma amostra cronológica nova, e usar preços que a ordem hipotética poderia realmente obter. Com L2 agregado, o cenário pessimista deve tratar cancelamentos sem posição conhecida como volume atrás, medir consumo da fila pelo tape e carregar o residual até resolução quando a segunda perna falhar. O teste precisa de reservar caixa até desbloqueio verificável e stressar perdas, latência e slippage nos cinco capitais antes de qualquer promoção.

## Reprodução e fontes

1. Executar download.sh com Bash e curl. Os 19 objetos Parquet usados são fixados no commit público 92fb1141c220c54587ad0efbbf9963b442acd4e1. A reconstrução lista SHA-256 por ficheiro em reconstruction.json.
2. Com Python 3.12 e DuckDB 2.0.1, correr settlements.py, reconstruct.py, pilot.py e fees.py. Os dois scripts de consulta pública escrevem os recibos Gamma e Polygon. Não há acesso privado ou escrita em bolsa.
3. markets_result.csv contém a decomposição por mercado do perímetro original. reconstruction.json contém resultados diários, resumo estendido, stress e hashes. pilot.json contém as condições e resultados da baseline. A cópia GitHub contém código e recibos de síntese. O pacote de evidência contém também o CSV detalhado, o conjunto de resoluções consultadas e os recibos.

- [Dataset PMData](https://huggingface.co/datasets/mileswangs/polymarket-btc-updown-5m-orderbook-tick-data/tree/92fb1141c220c54587ad0efbbf9963b442acd4e1)
- [Regra do mercado piloto na Gamma oficial](https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-1786147200)
- [Convenção de espelho PMData](https://pmdata.dev/faq)
- [Comissões Polymarket](https://docs.polymarket.com/trading/fees)
- [ABI do CTF Exchange V2](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/interfaces/ITrading.sol)
- [Exemplo de recibo Polygon](https://polygonscan.com/tx/0xc274454d35777b718fa8104ce9a1174487b370abf0688b6b43318f52c274be45)
