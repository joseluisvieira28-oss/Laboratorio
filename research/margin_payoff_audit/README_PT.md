# Auditoria +40% líquido / perda planeada ~−10% sobre margem

Data: 2026-10-08. Veredito: **TARGET_NOT_ESTABLISHED_COST_EXECUTION_AND_INDEPENDENT_SAMPLE_GAPS**.

Não foi demonstrada, nas famílias auditadas, uma estratégia que entregue +40% líquido por trade vencedor sobre a margem com perdas planeadas perto de −10%, após custos e restrições de execução verificáveis. Isto não declara NO_EDGE para todas as famílias: os vereditos científicos originais permanecem intactos. Há sobrevivência parcial de BTC-CONVEX e Donchian, falhas terminais de outras formulações e lacunas específicas na tradução para margem.

## Escopo e rastreabilidade

Auditoria descritiva de evidência já publicada, sem novo backtest ou hipótese. Quant Trailing v5 (Payoff Invertido) é o Parent recuperado de BTC-CONVEX-TREND-CAPTURE-001; contar ambos como estratégias independentes duplicaria evidência. Sticky H1 e H2 são filhos separados, não correções retroativas do Parent.

`source_manifest.json` fixa commit, Git blob e SHA-256 de 74 documentos/ledgers de quatro branches. As cópias em `evidence/` preservam os bytes publicados. `descriptive_metrics.json` contém contagens recalculadas dos dois ledgers seed comprimidos. Os commits e links canónicos de cada documento podem ser reconstruídos como `https://github.com/joseluisvieira28-oss/Laboratorio/blob/<commit>/<path>` usando o manifest. Nenhum artefacto original foi alterado.

Esta é uma seleção focada de famílias relevantes, não um censo de todas as branches. As cópias incluem documentos históricos superseded: devem ser lidos em sequência de autoridade, nunca como decisões atuais isoladas. Não foram baixados ZIPs de resultados de Actions: os digests de runs abaixo são declarações dos closeouts publicados, não hashes de ZIPs novamente verificados nesta auditoria. As contagens seed são verificadas diretamente contra os bytes do ledger.

## Frequência observada das grandes vitórias

Denominador das frequências: operações fechadas, incluindo todas as perdas. São percentagens de retorno reportadas pelo export com comissão, **sem funding/slippage completos**. No ledger 1h, a reconciliação direta demonstra que o denominador do retorno é value × 1.001 (valor de entrada mais fee de entrada de 0.1%), não notional puro. As colunas 2× multiplicam a percentagem reportada, são aproximações descritivas e não simulam uma conta alavancada. Trades abertos são excluídos.

| Seed BTC | Fechados | Vitórias / perdas | ≥40% a 1× | ≥40% sobre margem a 2×, apenas comissão | ≥40% a 1× por ano observado |
|---|---:|---:|---:|---:|---:|
| 5m | 187 | 38 / 149 | 7/187 = 3.74% | 16/187 = 8.56% | 1.03 |
| 15m | 159 | 29 / 130 | 6/159 = 3.77% | 12/159 = 7.55% | 0.88 |
| 1h | 100 | 26 / 74 | 5/100 = 5.00% | 11/100 = 11.00% | 0.75 |
| 4h | 61 | 17 / 44 | 1/61 = 1.64% | 3/61 = 4.92% | 0.15 |

No seed 1h, as cinco vitórias ≥40% são apenas 19.23% das 26 vitórias. A 2×, 11/26 = 42.31% das vitórias cruzariam o objetivo antes dos custos omitidos. Portanto nem a versão retrospectiva mais favorável sustenta que cada vencedor produza +40%. O retorno médio dos vencedores 1h é +21.56% e a perda média −4.19%, ambos na unidade reportada pelo export.

As cinco grandes vitórias 1h concentram-se em 2020 (1), 2021 (1) e 2024 (3); nenhuma em 2022, 2023, 2025 ou no pequeno bloco já publicado de 2026 fechado. A taxa anual é contagem dividida pela duração entre primeira entrada e última saída; não é previsão futura nem amostra anual independente. Dados 2026 aqui são somente linhas seed anteriormente abertas/publicadas, não acesso a novo holdout. A contagem independente, causal e com todos os custos para o objetivo margem permanece **UNKNOWN**, não zero.

## Margem, custos e compatibilidade da perda

Defina margem inicial M, notional inicial N e L=N/M. O retorno correto é PnL líquido/M, incluindo custos em dinheiro. Para a mesma posição e sem liquidação, custos fixos ou mudanças de sizing, pode-se traduzir um retorno líquido sobre N como L × retorno líquido sobre N. Lucro sobre equity da conta e retorno sobre margem não são intercambiáveis; a alocação original de ~95% da equity não é alavancagem.

Com perda típica seed reportada de 4.19% (já com comissão), multiplicar por 2 implica aproximadamente −8.38% sobre margem **antes dos custos ausentes**. O teto puramente algébrico 10/4.19 ≈ 2.387× usaria todo o orçamento de perda típica na unidade reportada; exigiria ≥16.76% nessa unidade para +40%. A conversão exata para N/M exige o denominador notional, acrescendo a diferença de fee inicial de 0.1% identificada acima. No seed 1h somente 12/100 trades cruzam esse limiar aproximado. Este teto não é recomendação, seleção de leverage nem garantia: funding, gaps, spread e slippage podem aumentar a perda. Não há sweep de parâmetros ou leverage escolhido por desempenho.

Para comparar posições reais: PnL líquido = quantity × (exit_fill−entry_fill) − fees + funding_cashflows − outros custos. Slippage incorporado em fill não se subtrai de novo. A margem deve ser definida antes da entrada e qualquer top-up identificado separadamente. Para spot sem leverage, capital comprometido substitui M; funding perp não se aplica, mas não se pode reclassificar um histórico perp como teste spot verificado.

Custos do primeiro basket BTC-CONVEX: 10 bps por lado, BASE 2 bps adversos por lado, STRESS 5 bps por lado e funding oficial histórico. O próprio freeze diz que slippage é **assunção fixa**, não slippage historicamente realizado. Os fees são herança do Parent, não tarifa pessoal verificada. Funding aplica-se apenas a posições carregadas antes do timestamp; entrada exatamente no timestamp não recebe essa cobrança segundo o contrato congelado. Não substituir esta ordem temporal.

A documentação oficial atual expõe [exchange information e funding history](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data), incluindo filtros por símbolo e markPrice associado ao funding. Isso não comprova filtros históricos, tarifa pessoal ou capacidade de execução de uma conta. Não foi chamado endpoint de conta.

**Min notional / min quantity / step size / tick size:** faltam recibos históricos por símbolo e data no conjunto auditado. Não assumir que 100 USDT de margem ou a alocação proporcional execute todas as posições; arredondamento pode alterar o risco/stop, e posições pequenas podem ser inelegíveis. Margin tiers, manutenção, mark-based liquidation, gap risk e regras de stop também faltam para uma tradução alavancada verificável. Estas lacunas bloqueiam a elegibilidade de execução e o objetivo líquido; não anulam automaticamente o closeout de mecanismo.

## Causalidade, overlap, duração e drawdowns

No seed 1h há oito reentradas no mesmo timestamp da saída anterior. O replay causal retirou foreknowledge de OHLC final e reentrada no mesmo candle: 93 trades, 23 vitórias, 70 perdas, PF 1.311, DD de equity fechada −40.75%. O PnL caiu 8,697.34 USDT frente ao comparador na mesma janela. Replay retrospectivo sem funding/slippage continua diagnóstico, não validação independente.

O Parent usa seleção de trail não latched: abaixo da ativação close-based +5%, pode voltar ao stop inicial. O recibo de 2026-09-29 que chamou a queda do stop de violação causal foi explicitamente **superseded / false positive** pelo recibo posterior preservado. Não importar a semântica Sticky H1 para o Parent.

Não há sobreposição de intervalos abertos dentro de cada seed, mas há 173 pares sobrepostos entre 5m e 15m, com 23 timestamps de saída idênticos. Entre 1h e 5m há 110 pares; entre 1h e 15m, 108. Pares não são clusters nem N_eff. Os exports menores omitem timezone, por isso comparações cruzadas são condicionais a relógio comum. A correlação mensal 5m/15m ~0.87 é do closeout histórico. Não somar os quatro N como replicações independentes.

Mediana de duração 1h: vencedores 778 horas (~32.4 dias), perdedores 47 horas; máximo 2,640 horas (~110 dias). Funding e capital imobilizado têm assimetria temporal material. Maior sequência de perdas: 5m 16, 15m 14, 1h 10, 4h 10. Se hipoteticamente toda a equity fosse margem e cada perda fosse 10%, dez perdas compostas reduziriam a equity em 65.13%; margem menor por trade muda essa conta. Não confundir perda pequena por trade com drawdown pequeno.

DD seed recalculado com 95% de alocação e retornos arredondados: −68.97%, −77.68%, −40.70%, −39.49% para 5m/15m/1h/4h. São reconstruções de equity fechada, não drawdowns intratrade ou de uma conta alavancada. Os baskets independentes têm DD MTM muito maior que o orçamento por trade.

## Freezes e closeouts preservados

| Família / estágio | Amostra e custos | Resultado publicado e implicação |
|---|---|---|
| BTC-CONVEX / Quant Trailing seed | 100 fechados 1h; fee-only; outcomes já observados | Retrospectivo. Remover top 3 vencedores deixa −20,360.33 USDT; não serve para escolher nova regra. |
| BTC causal replay | 93 trades; comissão; funding/slippage ausentes | Diagnóstico sobrevive, edge independente não demonstrado. Run 35911267608. |
| Parent ETH/SOL/BNB 2021–2025 | 100/163/102 trades; fees, funding, BASE/STRESS | SURVIVES, PF BASE 1.212/1.141/1.266; DD MTM −54.28%/−58.97%/−58.20%. Run 35918769969, digest 236b053ad50704149c5702803722c8022bee99d9dba0565e6b25138992571032. Frequência ≥40% sobre margem indisponível nos resumos. 365 trades não são 365 observações independentes. |
| Parent expansão XRP/DOGE/ADA/LINK/AVAX | 136/166/159/161/173 trades; mesmo custo | CROSS_SECTION_EXPANSION_FAIL; 0/5 positivos, mean BASE −75.70%, STRESS −77.78%; DD MTM de −75.58% a −88.18%. Run 35921780080. Não eliminar perdedores. |
| H2 rising regime terceiro basket | LTC/BCH/TRX/DOT/UNI; custos congelados | H2_FAIL; 1/5 positivo; mediana DD MTM −72.17%. TRX não pode ser escolhido depois do resultado. Run 35956632021. N detalhado não consta do resumo copiado. |
| P00 breakout/retest 3R | 344/344; BASE 0.20%, STRESS 0.30% RT | CLOSED_NO_EDGE; 88 vitórias/256 perdas, PF .737, expectancy −.196R; CI dia-block inteiramente negativa; 47 overlaps skipped, 212 dias. Não reabrir 2025/2026. |
| Donchian 1D 3R Discovery | 98 resolvidos/101 selecionados; 140 overlaps skipped, 73 dias | INSUFFICIENT_SAMPLE sob gate de 100; não apagar esta decisão com estágio posterior. |
| Donchian 1D 2025 OOS | 40/40; 16 vitórias/24 perdas; 30 dias distintos; custos 0.20%/0.30% | OOS_CONFIRMATION_SURVIVES_SHADOW_ELIGIBLE; 12 targets (30%) a 3R; mean .351R; CI [−.427,+1.101]R é diagnóstico no freeze, não novo gate. 23/40 trades no Q3. Não prova +40% sobre margem. |
| EMA pullback 1D 2R | 71 resolvidos/75; 29 overlaps skipped | INSUFFICIENT_SAMPLE; 29 vitórias/42 perdas; mean .154R. Regra 2R não satisfaz automaticamente um objetivo 4:1 líquido. |

Nos sistemas com target 3R, alavancar ou mudar sizing multiplica ganho e perda e conserva o ratio para a mesma operação antes de custos adicionais. Se −1R corresponder a −10% sobre margem, +3R corresponde aproximadamente a +30%, não +40%. P00 já falhou cientificamente; Donchian sobreviveu ao seu próprio gate, mas não ao estimando novo solicitado. Não retunar target para 4R neste histórico. Oportunidades e percentagens em R não dão frequências de +40% sobre margem sem ledgers de risco, custos e margem por evento. DD e duração OOS Donchian não estão nos resumos copiados: UNKNOWN; não inferir do total R.

O forward BTC-CONVEX mantém autoridade separada V0.1/V0.2 e checkpoints 10/25/50 com exigências por símbolo. O último recibo técnico copiado não é um veredito económico forward atual. Esta auditoria não executa snapshots, não abre resultados novos e não afirma checkpoint atual atingido.

## Decisão e trabalho admissível

**Nenhum candidato qualificado para o objetivo +40/−10 após todos os custos na evidência auditada.** Não há prova de que nenhuma estratégia possível o consiga; há ausência de demonstração para estas famílias e um problema explícito de frequência, dependência e risco. Preservar SURVIVES, FAIL, NO_EDGE e INSUFFICIENT_SAMPLE conforme os freezes próprios.

Próximo bloqueio concreto: obter os ledgers/eventos já publicados dos runs económicos, sem recalcular ou expandir outcomes, e ligar margem inicial, net PnL, custos, duração, overlaps e restrições históricas de tamanho por trade. O alvo só pode ser creditado quando essa cadeia passar; faltas continuam UNKNOWN/BLOCKED, nunca zero inventado. Para qualquer nova regra ou target, exigir novo ID, freeze antes de outcomes e um inventário de exposição que prove dados genuinamente intocados; o histórico seed e baskets abertos não são intocados. Nenhuma hipótese nova foi ativada aqui.

## Reprodução e limites operacionais

Na raiz desta branch: `python research/margin_payoff_audit/audit.py` e `python -m unittest discover -s research/margin_payoff_audit -p test_audit.py -v`. Só biblioteca padrão, leitura das cópias locais e escrita de `descriptive_metrics.json`; sem rede, credentials ou integração de runtime. `snapshot.py` copia blobs Git já presentes, mantendo commits fixados pelo manifest existente; não é necessário para repetir as métricas.

Branch isolada baseada em main `f263c6c6f3a57f26666a7aee28e782f2cbd08418`. Somente `research/margin_payoff_audit/` muda. Sem ordens, endpoints authenticated de exchange, login, saldo, gastos, Render mutation, merge, live trading ou alteração dos freezes originais.
