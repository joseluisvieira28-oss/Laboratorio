# Funding Crowding — auditoria e veredito
Data: 2026-10-22. **DUPLICADO IDENTIFICADO / NO_PROMOTION.** Há correspondência direta em PERP-CROWDING-UNWIND e incremental em DCV-001. Não se cria um novo backtest com novo nome.

## Hipótese direta, freeze e amostras
Financiamento nos extremos de 5/95% + crescimento OI no percentil80: unwind contrarian em24h. Quantis trailing540 eventos, mínimo270, shifted1; sem alteração após outcomes; uma posição ativa. BTC2021–24; ETH/SOL/BNB2022–24. Fonte Binance pública: funding calc_time, métricas OI, klines1h.
Protocolo BTC blob cbfdb0de63a7d525321e4fab1c0a478d3cf739c5; head7225957df2d64fa8240922a1a7c9e26d4aae8cad. Relatórios de 2026-09-19, auditados2026-10-22.
| ativo | N | média net10 | CI95% média | média net20 |
|---|---:|---:|---:|---:|
| BTC |177|+0.4776%|[-0.0771%,+1.0516%]|+0.3776%|
| ETH |129|+0.3530%|[-0.2071%,+0.9529%]|+0.2530%|
| SOL |141|+0.7588%|[-0.2098%,+1.7609%]|+0.6588%|
| BNB |119|+0.5885%|[-0.1755%,+1.3445%]|+0.4885%|
Todos falharam o critério congelado de limite inferior bootstrap >0. Todos negativos em2024. Família exata encerrada em44f79718b878da12c79f5f7c66511025ba8b913f. São resultados herdados, não reproduzidos de raw nesta auditoria.

## Auditoria crítica de custo e timestamps
O runner inspecionado usa funding do próprio calc_time e OI <=calc_time, mas assume entrada no open da MESMA hora (t.floor('h')). Não demonstra que as publicações já estavam disponíveis antes desse open. Risco de antecipação/simultaneidade operacional; não reclassificar como causalmente executável.
O custo10/20bps round trip omite cashflows de funding explicitamente. Num trade de perp de24h isso não é custo total. Faltam spreads/capacidade/fills, latência, regras históricas de fee/margem e risco de liquidação. Não se deve tratar média net10 como lucro realizável.
Qualquer correção de latência ou inclusão de funding após ver resultados é uma nova investigação, não validação OOS do estudo antigo. Não a executar silenciosamente.
Controlos originais: quantis causais, overlap, custos stress, anos e replicações idênticas entre ativos. Mesmos anos/mesma venue não são confirmação temporal independente; ativo novo não remove regimes comuns. Ausência de placebos causais e known_at de publicação limita inferência.

## DCV-001 e famílias adjacentes
DCV-001 pergunta informação incremental funding×OI×RV7 no retorno seguinte, com termos inferiores completos, z90 passado e bootstrap de blocos7. N997; beta -0.0006263757; CI95[-0.0020661132,+0.0014461722]; sinal anual negativo só em2022. DISCOVERY_FAIL_NO_PROMOTION em278e27a2f851c3682a606471103592e2ae30a4fb, relatório2026-09-23.
Não calcula P&L, logo não demonstra custo total ou edge. Discovery falhou:2024 replication e2025/26 continuam fechados para esse mecanismo.
Funding carry/squeeze é mecanismo adjacente, não crowd-unwind: V03 Binance2025 N21, média bruta12.3821bps, net20=-7.6179bps, CI95[-9.9312,-4.9358]bps; NO_EDGE_LOWCOST_V03, bf0e9659fc06d9d3ddebbc1a70cc40778298c314. Não usar como rejeição universal de crowding.

## Veredito e próximo gate
Manter encerradas as regras exatas; nenhum OOS de resgate, inversão, novos ativos ou mudança de horizonte. O fenómeno geral continua não universalmente refutado; não há edge independente executável demonstrado.
Próximo estudo só com known_at real e entrada posterior, funding integral, capital/margem/quotes, controlos e amostra prospectiva definida ANTES de outcomes. Sem chamadas privadas ou trading.

Fontes:
- [BTC closeout](https://github.com/joseluisvieira28-oss/Laboratorio/blob/7225957df2d64fa8240922a1a7c9e26d4aae8cad/labs/PERP_CROWDING_UNWIND_001/DISCOVERY_CLOSEOUT_V0.1.md)
- [runner auditado](https://github.com/joseluisvieira28-oss/Laboratorio/blob/7225957df2d64fa8240922a1a7c9e26d4aae8cad/labs/PERP_CROWDING_UNWIND_001/discovery_v01.py)
- [crossasset final](https://github.com/joseluisvieira28-oss/Laboratorio/blob/44f79718b878da12c79f5f7c66511025ba8b913f/labs/PERP_CROWDING_UNWIND_XASSET_001/FINAL_CLOSEOUT_V0.1.md)
- [DCV](https://github.com/joseluisvieira28-oss/Laboratorio/blob/278e27a2f851c3682a606471103592e2ae30a4fb/research/dcv001/DCV001_DISCOVERY_CLOSEOUT_V0.1.json)
