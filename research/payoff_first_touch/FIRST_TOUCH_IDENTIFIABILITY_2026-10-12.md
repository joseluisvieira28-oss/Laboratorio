# PAYOFF 4:1 — Primeiro toque / causalidade — 2026-10-12

**Classificação:** `FIRST_TOUCH_OUTCOMES_UNIDENTIFIABLE_FROM_PUBLISHED_EXIT_COUNTS_AND_MFE_MAE_SUMMARIES`. Diagnóstico pós-outcome, **zero promoção científica**. Parent: PR #166, commit `98454c4516b69fae54526ed37600895f0b6063a9`. Sem alteração de parâmetros, execução ou outcomes.

## Fonte e resultado verificável

Fontes fixadas e preservadas na PR #166: `research/margin_payoff_audit/README_PT.md`, `descriptive_metrics.json`, `ONE_HOUR_SEED_AUDIT_V0.1.md`, `CAUSAL_1H_REPLAY_CLOSEOUT_V0.1.md`, `SOURCE_RECOVERED_V0.1.pine`.

- BTC 1h seed retrospectivo: **100 encerradas (26 wins/74 losses)**; **5/100** saídas com retorno reportado ≥40% fee-only; **11/100** saídas ≥20% usadas pela PR #166 como **aproximação aritmética 2×**; **12/100** ≥16,76% para o teto descritivo de leverage baseado na perda típica. Nenhuma destas frequências é first-touch ou resultado económico integral.
- Média dos vencedores seed **+21,56%**, média dos perdedores **−4,19%**, **10 perdas seguidas**, DD de equity fechada **~−40,7%**, mediana de vencedor aberto **778h**. Capital, liquidação e drawdown intratrade alavancados **não verificados**.
- Fonte Pine recuperada: stop inicial **4% do preço**, trailing **12%**, ativação via close ≥**5%** **não-latched**, fee da configuração histórica **0,1% por lado**, alocação **95% da equity**, não uma margem fixa 2×. Não se pode transpor tarifa observada MEXC 0,08% para resultados de outro venue.
- O audit seed regista excursion favorável **MFE em 74 losers**: 41 chegaram +2%, 24 a +4%, 18 a +5%, 6 a +10%, 1 a +15% e máximo +15,69%. MFE/MAE não registam por si só a **ordem temporal** dos toques de barreiras novas.
- Replay causal já publicado: **93 trades, 23 wins/70 losses, PF 1,311, DD fechada −40,75%**; ainda **sem funding/slippage** e em outcomes conhecidos. Não é validação prospectiva.
- Basket ETH/SOL/BNB do Parent preserva `SURVIVES` ao seu próprio gate económico (DD MTM severo); expansão 5 moedas `FAIL`; H2 `FAIL`; P00 `CLOSED_NO_EDGE`; Donchian 2025 OOS `SURVIVES` ao gate **3R**, não ao estimando de +40%/−10%. Não reclassificar.

## O preço do +40% líquido e −10% líquido com 2×

Exemplo **sintético**, não observação nem reinterpretação do ledger: margem inicial M, notional 2M, preço de saída `1+x` vezes o preço de entrada, fee taker ilustrativa MEXC **0,08% na entrada e saída calculada ao nocional de saída**, sem funding nem slippage e mesma quantidade:

`netPnL/M = 2 * (0.9992*x - 0.0016)`.

- +40% líquido sobre M precisa de **preço +20,17614%**.
- −10% líquido sobre M corresponde a **preço −4,84388%** (não a −5% com fees).
- Stop do Parent a −4% do preço daria aprox. **−8,3136% de M** sob este exemplo de fees, antes de outros custos. Não é novo stop proposto.

A contagem original 11/100 por **retorno de saída** não é limite superior para alvos intratrade: um trade que saiu abaixo de +20% pode ter tocado esse alvo antes. Inversamente um MFE grande não prova stop-first seguro, fill no alvo ou ganho líquido. Ambos os enviesamentos são possíveis.

## Gate de primeiro toque e regras de ciência

1. **Autoridade primeiro**: custos, sizing, razão notional/margem, direção, stops e targets fixados *antes* de outcomes; critério de seleção apenas com features conhecidas à entrada. Não retrofitar limites a 100 trades vistos.
2. **Path data**: candles com timestamp e proveniência em todo o intervalo desde entrada até horizonte predefinido; preço last versus mark identificado; entrada e timestamp causal; nenhum preenchimento artificial de gaps.
3. **Ambiguidade**: se stop e target aparecem no mesmo candle sem ordem intrabar comprovada, emitir `AMBIGUOUS_SAME_BAR` (não target-first). Gaps e stops não garantem preço de fill. Mesmo candles 1m podem ser insuficientes.
4. **Risco e execução**: funding time-weighted, fees por notional real, slippage, maintenance tiers, liquidação mark-price, min notional e lot/tick, overlap/insolvência antes de concluir resultados.
5. **Independência**: qualquer regra realmente nova necessita outro ID, freeze antes de dados genuinamente intocados, e verificação de cobertura; histórico PR #166 fica diagnóstico. Sem acesso a novos outcomes até uma autorização científica específica válida.

`first_touch.py` recebe **casos JSON já preparados e autorizados**, usa OHLC completos e contíguos, e devolve apenas `TARGET_FIRST_NO_FILL_GUARANTEE`, `STOP_FIRST_NO_FILL_GUARANTEE`, `AMBIGUOUS_SAME_BAR`, gaps, missing/invalid ou neither. Não estima PnL, sequências ausentes, liquidation ou order fills. **Nenhum dataset novo nem output de mercado foi fornecido**.

**Reprodução local sintética:** `python -m unittest discover -s research/payoff_first_touch -p 'test_first_touch.py' -v`. Sete unit tests sintéticos PASS em ambiente local antes da publicação; sem afirmar CI/runs ou replay real.

**Estado:** SOURCE-CAUSALITY GATE BLOCKED FOR +40%/−10% TARGET. Isto **não** é NO_EDGE do Parent nem um trade live GO. Scope research-only, branch isolada, sem ordens, contas, wallets, gastos, Render, activation, alteração a freeze ou merge para main.
