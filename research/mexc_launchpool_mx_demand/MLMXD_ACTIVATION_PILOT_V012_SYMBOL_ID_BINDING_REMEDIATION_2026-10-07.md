# MLMXD ACTIVATION PILOT V0.1.2 — CURRENT SYMBOL-ID BINDING REMEDIATION
Date: 2026-10-07
Status: TECHNICAL TRANSPORT REMEDIATION

Parent pilot and event list remain unchanged.

Observed defect:
- MEXC current public symbols endpoint groups spot symbols by quote asset under data.symbols.USDT;
- rows identify the base token through vn (for example MX or BTC), rather than exposing the legacy literal MX_USDT/BTC_USDT string used by the prior probe;
- therefore the prior symbol-ID extractor returned None for both required markets.

Permitted correction:
- select rows only from data.symbols.USDT;
- bind MX by vn == "MX" and BTC by vn == "BTC";
- use each row's public id for the already-discovered official history-file path;
- inspect only the exact same MXUSDT/BTCUSDT 15m history needed for the pre-frozen 14-event pilot.

Forbidden:
- no event changes;
- no T0/horizon/direction changes;
- no alternate venue;
- no interpolation;
- no gate changes.
