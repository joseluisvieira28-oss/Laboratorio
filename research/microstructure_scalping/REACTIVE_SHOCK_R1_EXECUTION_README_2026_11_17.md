# REACTIVE-SHOCK-SCALP-005 — R1 execução da replicação congelada
Data de execução: 17-11-2026 (tentativa). Branch isolada: `research/reactive-shock-r1-frozen-2026-11-17`, baseada na branch `microstructure-scalping-lab-v0.1`.

**Não é nova estratégia, nem retuning.** Usa literalmente `REACTIVE_SHOCK_SCALP_005_REPLICATION_R1_FREEZE_V0_1.md` (congelado 26-09-2026) e o manifesto R1 de 14 eventos sem sobreposição com os 8 MVE. Importa `eval_variant` do motor original, que contém a correção para short. Somente `FLOWPRICE_W2`, observação 2s, saída 60s após a entrada, com BBO histórico Bybit, custos MEXC 16 bps apenas como proxy + stress extra de 10 bps. Os 2025/2026 protegidos ficam fechados.

**Gates congelados**: n>=12, CPI>=6, NFP>=6, pooled mean e median stress10>0, CPI/NFP means stress10>0, pelo menos 8 eventos stress10>0, e bootstrap 5000 95% lower>0. Um fail mata esta replicação; não mudar horizontes, custos ou eventos depois dos resultados.

**Limitações inegociáveis:** BBO histórico não equivale a fill; timestamps históricos não são recibos de receção ponto-no-tempo; o custo MEXC é proxy diferente da fonte Bybit; não há teste de carteira, impact, funding ou latência real; nem um eventual SURVIVES permite trading real. Nunca criar, enviar ou simular ordens a endpoints privados. Se fonte faltar, `SOURCE_BLOCKED`, não PnL zero. R1 é amostra histórica Discovery, não OOS verdadeiro.

Este PR é draft, sem merge à main, e o workflow tem permissão somente `contents: read`. O relatório de cada evento é salvo como artefacto JSON temporário e os hashes de arquivos são registados, mas não são enviados arquivos de mercado de grandes dimensões.