# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.3 CLEAN DISCOVERY CLOSEOUT
Date: 2026-10-05
Status: SURVIVES_INFORMATION_DISCOVERY
Authoritative result commit parent: cc1cb0ed58562043416ad22747c7a89c7be0e5f5
Freeze authority: 08b83cb2bbf10d3806425c833f648032fcaaee23
Technical remediation authority: 9de672a86797d9cf38f8e0c1f61445dfd8058a76

## Authoritative result
The technically remediated clean 2022-2023 discovery is the authoritative V0.3 result.

- n = 12/12
- median R1 = +19.0141%
- median R5 = +19.6329%
- median R15 = +20.3875%
- median R60 = +15.2781%
- R15 positive hit-rate = 100%
- median 5m volume shock = 97.6645x
- leave-one-out median R15 > 0 = PASS
- largest observation share of summed positive R15 = 19.9693% (gate <=35%) = PASS
- verdict = SURVIVES_INFORMATION_DISCOVERY

All frozen Layer-A gates pass.

## Secondary delayed-entry diagnostics (non-gating)
Entry = first full minute boundary at least 60 seconds after official Binance T0.
- median gross +5m = +2.4328%; hit-rate 75.0%
- median gross +15m = +1.6376%; hit-rate 58.33%
- median gross +60m = +0.3775%; hit-rate 58.33%
- median +15m ex-BTC = +1.7904%
- median 15m MFE = +5.5286%
- median 15m MAE = -4.3210%

These are descriptive only. No fee/slippage/latency-adjusted edge is claimed.

## Superseded evidence
Earlier V0.3 SOURCE_BLOCKED closeouts/results are retained for audit history but superseded by the locked technical remediation, which repaired deterministic transport gaps and used the pre-outcome frozen KuCoin->Bitget fallback only when a mandatory source metric could not be computed.

## Governance
2024 remains quarantined from confirmatory use.
2025-2026 remain unopened by V0.3.
No live trading, orders, account reads, private endpoints, wallets, or merge to main.
A new pre-outcome execution/cost freeze is mandatory before opening a holdout or making a tradability claim.
