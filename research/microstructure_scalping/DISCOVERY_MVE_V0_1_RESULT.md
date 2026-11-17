# MICROSTRUCTURE SCALPING LAB — DISCOVERY MVE V0.1 RESULT

Date: 2026-09-25
Workflow run: 36189370766
Status: TAKER_ONLY_NO_EDGE / RAW_SIGNAL_PRESENT

## Frozen sample
- Bybit BTCUSDT linear L2
- date: 2023-01-18
- first 250,000 messages
- anchor interval: 1,000 ms
- rows with all frozen labels: 24,419
- OOS 2025 opened: NO
- protected 2026 holdout opened: NO

## Main observation
The sign of book imbalance / microprice contains weak positive directional information as horizon increases, but the executable magnitude is far below taker transaction-cost hurdles.

Representative L1/microprice results:
- 100 ms: mean directional mid +0.0146 bps; mean executable gross -0.2216 bps
- 500 ms: +0.0514 bps; executable gross -0.1846 bps
- 1 s: +0.0874 bps; executable gross -0.1487 bps
- 5 s: +0.3173 bps; executable gross +0.0812 bps
- 15 s: +0.5882 bps; executable gross +0.3521 bps
- 30 s: +0.7237 bps; executable gross +0.4874 bps

At 30 s:
- directional-mid hit rate: 53.48%
- p95 executable gross: 4.7037 bps
- mean Bybit taker/taker net using frozen VIP0 reference: -10.5126 bps
- mean gross minus MEXC taker/taker fee hurdle: -15.5126 bps

L5/L10 results are similar in scale.

## Decision
TAKER_ONLY_NO_EDGE for the frozen sign-only MVE.

This does NOT close the whole microstructure family because:
1. extreme states were not threshold-searched in the frozen MVE;
2. maker-assisted execution was deliberately blocked pending a defensible fill/queue model;
3. executed trade flow has not yet been joined to L2.

## Scientific next step
Do NOT expand taker-only sign rules to OOS.

Open a new pre-outcome maker/source gate:
- prove historical public trade data can be matched to L2 using Bybit trade time T and/or cross sequence seq;
- construct a conservative passive-fill model;
- only after that freeze an extreme-state Discovery grid inside 2023–2024.

No 2025 OOS and no 2026 holdout until a candidate is frozen.
