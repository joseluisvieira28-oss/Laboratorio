# Índice de fontes efetivamente lidas

As referências com SHA são imutáveis; as três referências de branch VRP/CED apontam aos documentos lidos, cujos blob SHAs se indicam abaixo.

- [Auditoria obrigatória](https://github.com/joseluisvieira28-oss/Laboratorio/blob/ebaddeb5e0ac2922ba523c011c87866f35060409/audits/CRYPTO_LAB_SCIENCE_ONLY_ALL_FRONTS_ATTACK_2026-10-08.md)
- [XALT holdout canónico](https://github.com/joseluisvieira28-oss/Laboratorio/blob/99792504992b4a40741192dec671c1a7d03800c8/research/liquidation_cascade/LICP_HIST_XALT_003_CANONICAL_HOLDOUT_RESULT_V0_1.md)
- [XALT forward freeze](https://github.com/joseluisvieira28-oss/Laboratorio/blob/99792504992b4a40741192dec671c1a7d03800c8/research/liquidation_cascade/LICP_FWD_XALT_004_PRE_OUTCOME_FREEZE_V0_1.md)
- [LICP BTC freeze](https://github.com/joseluisvieira28-oss/Laboratorio/blob/99792504992b4a40741192dec671c1a7d03800c8/research/liquidation_cascade/LICP_001_FORWARD_ECONOMIC_VERDICT_FREEZE_V0_1.md)
- [OPTIONS custo canónico](https://github.com/joseluisvieira28-oss/Laboratorio/blob/51a808bcf70e89319e23ca1753cace47ffb963e7/receipts/OPTIONS_SPOTPERP_001_V21_EXECUTION_ECONOMICS_CANONICAL_BASE_CLOSEOUT_2026-09-28.json)
- [OPTIONS fees corrigidas](https://github.com/joseluisvieira28-oss/Laboratorio/blob/51a808bcf70e89319e23ca1753cace47ffb963e7/receipts/OPTIONS_SPOTPERP_001_V21_FEE_ZERO_TOTALFEE_HOTFIX_EVIDENCE_2026-09-29.json)
- [ETF OOS](https://github.com/joseluisvieira28-oss/Laboratorio/blob/20ace9b5d3a13e7e6ea4bd62d4c42bab7cad6806/labs/ETF_CME_INSTITUTIONAL_FLOW_001/OOS_2025_V2_PROMOTION_CLOSEOUT.md)
- [ETF readiness](https://github.com/joseluisvieira28-oss/Laboratorio/blob/20ace9b5d3a13e7e6ea4bd62d4c42bab7cad6806/labs/ETF_CME_INSTITUTIONAL_FLOW_001/TIER1_READINESS_CLOSEOUT_2026-09-14.md)
- [CED reconciliation](https://github.com/joseluisvieira28-oss/Laboratorio/blob/ced1d-runtime-reconciliation-2026-09-30/crypto_edge_radar/receipts/CED1D_0031_CANONICAL_RUNTIME_RECONCILIATION_2026-09-30.md)
- [BNB source](https://github.com/joseluisvieira28-oss/Laboratorio/blob/79f41e0153eda3727f4ced6305d4e457ba3703a2/governance/BNB_LAUNCHPOOL_PROSPECTIVE_SOURCE_AUDIT_CLOSEOUT_V0.3_2026-10-05.md)
- [DH03 freeze](https://github.com/joseluisvieira28-oss/Laboratorio/blob/b3fd7991d488129b13fa0f2f919e8534c314a1fd/crypto_edge_radar/HTF_DH03_12H_STANDALONE_FORWARD_V1_FREEZE.json)
- [VRP V2 closeout](https://github.com/joseluisvieira28-oss/Laboratorio/blob/btc-options-vrp-v2-forward-2026-10-07/research/btc_options_vrp_v2/V2_RESEARCH_CLOSEOUT_2026-10-07.md)
- [VRP V2 current](https://github.com/joseluisvieira28-oss/Laboratorio/blob/btc-options-vrp-v2-forward-2026-10-07/research/btc_options_vrp_v2/CURRENT_VERDICT_2026-10-07.md)
- [Funding carry](https://github.com/joseluisvieira28-oss/Laboratorio/blob/526ee97b7177596b7ffe1cfb3a2578e4cdfcd002/labs/FUNDING_CASH_CARRY_001/DISCOVERY_CLOSEOUT_V0.1.md)
- [QBC closeout](https://github.com/joseluisvieira28-oss/Laboratorio/blob/154c041dfa77f3cf8edc84a2f0e1babba33776c8/Dream-Account-OS-v2.3-PARTIAL/research/quarterly_basis_convergence_001/FINAL_CLOSEOUT_V0.2.md)
- [L2 upper bound](https://github.com/joseluisvieira28-oss/Laboratorio/blob/0db7a7e911aea0913f0b6aca859f4ac46444b1b4/research/l2_resiliency/L2R_EXEC_PASSIVE_001_2025_UPPER_BOUND_CLOSEOUT_V0_1.md)

Blob SHAs: CED 9958f0546b3f8a68ef3e8b3189b0866255468425; VRP closeout 0a43be9f1d2fcdaa310c271b790a4c647beec199; VRP current 0d28118f32a0c3f9abac3150ec0280b40b2beaba.

## Fontes públicas de execução consultadas em 2026-10-08
- [Fees Deribit](https://support.deribit.com/hc/en-us/articles/25944746248989-Fees): tabela standard; opções 3 bps, cap 12,5%; desconto combo apenas na rota elegível; delivery.
- [Linear USDC Options](https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options): estilo europeu, settlement, quantidades, unidades, margem.
- [Linear Futures](https://support.deribit.com/hc/en-us/articles/31424954805405-Linear-Futures): settlement gerado pelas opções.
- [Combos](https://insights.deribit.com/exchange-updates/deribit-introducing-combos/): BOX e distinção entre livro conjunto e preços implícitos.
- [API combo IDs](https://docs.deribit.com/api-reference/combo-books/public-get_combo_ids)
- [API instrumentos](https://docs.deribit.com/api-reference/market-data/public-get_instruments)
O endpoint de metadata devolveu taker_commission=0.0003 nas 16 pernas selecionadas, reconciliado com a documentação; nenhum tier privado foi consultado.

## Runs históricos referenciados, não reexecutados
- [XALT holdout canónico 36234052123](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/36234052123)
- [ETF OOS 34815006815](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/34815006815)
- [ETF readiness 34842535727](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/34842535727)
- [Funding carry 35472634799](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35472634799)
Estes links são proveniência dos closeouts lidos; o estado vivo de cada run não foi novamente auditado.

## Nova freeze e execução
- [Freeze pré-quotes f2591d3](https://github.com/joseluisvieira28-oss/Laboratorio/commit/f2591d34f9d7ce2949d2f209dde65653be04bc8f)
- Freeze commit UTC: 2026-10-08T15:24:00Z.
- Coleta local: 2026-10-08T15:26:17.899370Z a 15:28:05.678354Z.
- Novo workflow executado: nenhum. Execução e replay locais com dados públicos.

