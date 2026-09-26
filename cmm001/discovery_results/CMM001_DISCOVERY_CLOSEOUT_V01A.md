# CMM-001 — DISCOVERY TECHNICAL CLOSEOUT V0.1A

**FORMAL VERDICT: INSUFFICIENT_SAMPLE**
**MATURITY: M3_DISCOVERY_ATTEMPT**

Technical status: parent science reproduced from immutable event ledger; serialization bug repaired without network access or scientific changes.

## Source integrity
- Parent full-corpus source gate: PASS.
- Options candidate-window O_raw coverage: 97.4138%.
- Deribit request/parse errors: 0.
- Deribit has_more truncation days: 0.
- Binance Spot exact-hour availability: 100%.
- 2025: LOCKED / NOT FETCHED.
- 2026: LOCKED / NOT FETCHED.

## Frozen block results — BASE NET10
- A_DISCOVERY: N=15 | mean=-15.9743 bps | median=-47.3048 bps | PF=0.9382 | positive=46.67%
- B_REPLICATION_2023: N=16 | mean=-12.4893 bps | median=4.9784 bps | PF=0.8851 | positive=56.25%
- C_REPLICATION_2024: N=4 | mean=-177.3134 bps | median=-243.2101 bps | PF=0.0977 | positive=25.00%

## Pooled
- N=35
- mean NET10=-32.8199 bps
- median NET10=-47.3048 bps
- PF NET10=0.8205
- positive events=48.57%
- mean STRESS20=-42.8199 bps
- largest single positive BASE-net share=36.28%

## Bootstrap
- 10,000 reps; seed 20260925
- P(mean <= 0)=0.6630
- p05=-166.6140 bps
- median=-36.0414 bps
- p95=111.0033 bps

## Frozen sample-adequacy gate
- pooled N >=30: PASS
- A_DISCOVERY N >=8: PASS
- B_REPLICATION_2023 N >=8: PASS
- C_REPLICATION_2024 N >=8: FAIL

Because sample adequacy fails if ANY block has N<8, the frozen authority requires INSUFFICIENT_SAMPLE before any Tier-4 adjudication. This repair does not override that precedence.

## Scientific warning preserved
- Independent 2023 block material-contradiction diagnostic: TRUE.
- This warning is not a Tier-4 verdict while the frozen corpus sample-adequacy gate is unmet.
- No threshold/cost/horizon/component/year/direction rescue is authorized.

## Evidence integrity
- Event ledger SHA256: 8c79b4287d5a0bc7ab263b856b56bded638d75e2ea14c25434156a4eb20909d8
- Source report SHA256: 86232bbac83d5fa4db6cf3997b59b9a2e3c74ab56f59821e8d857251204364bd
- All original block and bootstrap reproduction anchors: PASS.

## Safety
No live trading, micro-live, capital, orders, exchange mutation, alerts/webhooks, Render deployment or main merge is authorized.
