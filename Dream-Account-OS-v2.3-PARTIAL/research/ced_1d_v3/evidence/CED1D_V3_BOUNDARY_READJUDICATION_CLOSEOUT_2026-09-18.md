# CED-1D-V1 — V3 BOUNDARY-WEEK SURVIVOR RE-ADJUDICATION CLOSEOUT — 2026-09-18

**Historical verdict preserved / re-adjudicated under Promotion Policy V3.**

## Execution identity

- one-shot V3 implementation freeze commit: `102ee494ea2b46c0d29b48f5cfcae6e6cc28f1ca`
- implementation Git blob: `c5cc6a7b78d6ed93bc864d46ef326e3475242aed`
- frozen historical mapped closeout ZIP SHA256: `d590b2fe3b86baa9b9b0c1e092cf53c6cb0067ebcafb9fd7a21002dd2df50841`
- historical closeout output SHA256: `8b30a95606a0949a912fa8d1475e63c9431263c7568bf0b2d3df4f8373c47416`
- reproduced RAW Discovery matched original closeout input pins **7/7 byte-exact**.
- derived daily fingerprint: `b92741d682a704a237cc1ab1a4d1fb0beb13798b11993ddde9ef54bcd4f3ab20`
- historical mapped closeout tests: **69/69 PASS**
- V3 boundary wrapper pre-outcome tests: **9/9 PASS**
- 2025 accessed: **false**
- 2026+ accessed: **false**

## Boundary blocker adjudication

The historical inference blocker is resolved under the prospectively frozen signal-completion-week rule.

For all three frozen survivors:
- `bootstrap_status = PASS`
- boundary executed trades excluded = **0**
- two split-edge `DATA_UNAVAILABLE` signal rows remain visible in audit per target and do not enter inference.
- no event deletion, new cell, direction change, lookback change, horizon change, threshold change or cost rescue occurred.

## Target results — frozen Discovery 2021–2024

| ID | Cell | N inference | BASE 10 bps | PF BASE | p one-sided | 95% bootstrap CI | Scout | V0.2 routing |
|---|---|---:|---:|---:|---:|---|---:|---|
| CED1D-0031 | AVAX 20D CONT, H1D | 1439 | +20.9116 bps | 1.1002 | 0.1447 | [-13.5505, +57.6990] | 59 | SCOUT_SURVIVOR |
| CED1D-0241 | SOL 20D CONT, H1D | 1439 | +26.7908 bps | 1.1320 | 0.0699 | [-4.7558, +59.7042] | 56 | SCOUT_SURVIVOR |
| CED1D-0251 | SOL 60D CONT, H1D | 1399 | +13.4689 bps | 1.0660 | 0.2333 | [-17.3192, +45.3076] | 59 | SCOUT_SURVIVOR |

Additional frozen diagnostics:
- AVAX 20D: STRESS14 +16.9116 bps; SEVERE20 +10.9116; positive months 60.42%; minimum calendar-year BASE mean -6.6496 bps; neighbour support 1/2.
- SOL 20D: STRESS14 +22.7908 bps; SEVERE20 +16.7908; positive months 54.17%; minimum calendar-year BASE mean +3.4559 bps; neighbour support 1/2.
- SOL 60D: STRESS14 +9.4689 bps; SEVERE20 +3.4689; positive months 50.00%; minimum calendar-year BASE mean -34.8726 bps; neighbour support 2/3.

Funding remains `NOT_TESTABLE` in this Discovery closeout, exactly as required by the frozen V0.2 contract.

## V3 status after Discovery re-adjudication

No target is Tier 4 / NO_EDGE.

All three remain scientifically alive and are classified **Tier 3 — WATCHLIST / awaiting independent 2025 Confirmation** under Promotion Policy V3. No Tier 2 is assigned from Discovery alone because the required independent replication has not yet been opened and funded economics/execution remain unresolved.

All three frozen survivors proceed to the separately frozen 2025 Confirmation protocol. No new survivor is admitted.

## Next gate

Before any 2025 price outcome:
1. freeze the exact 2025 Confirmation population = these three IDs only;
2. freeze base/stress nonfunding Confirmation costs under the V0.2 contract;
3. freeze official Binance USD-M funding provenance and settlement accounting;
4. freeze one-shot 2025 source/access firewall;
5. only then open 2025 once.

No 2026+, live trading, exchange mutation, orders, wallets, alerts/webhooks or merge to main are authorized.