# ETF-SHORTFLOW-001 — ONE-SHOT DISCOVERY AUTHORIZATION V0.1

STATUS: AUTHORIZED FOR EXACTLY ONE 2024 DISCOVERY EXECUTION

LAB: `ETF-SHORTFLOW-001`
MVE: `ESF-IBIT-SHORTVOL-5D-001`
BRANCH: `etf-shortflow-v0.1`

## Parent frozen authority

- Frozen protocol: `labs/ETF_SHORTFLOW_001/PRE_DISCOVERY_PROTOCOL_V0.1.md`
- Frozen protocol SHA256: `5adde8f691ac762752547437d225a7ce90ac11ce1c9e34b96ea8d93f5adecb5c`
- Source/Data Gate run: `34868986676`
- Source/Data Gate artifact: `10358052444`
- Source/Data Gate artifact ZIP SHA256: `8cd52d589e8fa782a3b59a5f49453e99fae76e0f2a8cf7371234b48e023fc0ba`
- Source/Data Gate classification: `SOURCE_DATA_PASS`
- Accepted FINRA files: 245/245
- Accepted IBIT rows: 245/245
- FINRA parsed-row CSV SHA256 at parent gate: `8ad8797f43347038c4f39f3f99d8bd95c6576e412055c6f4fb329ab31a960f13`
- 2025 accessed at parent gate: false
- 2026 accessed at parent gate: false
- BTC market data accessed at parent gate: false

## User authorization

Explicit user authorization for the one-shot Discovery was received in chat on 2026-09-14 after the successful Source/Data Gate.

## Immutable execution scope

Execute the frozen MVE exactly as written in `PRE_DISCOVERY_PROTOCOL_V0.1.md`:

- source security: IBIT only;
- FINRA 2024 source window only;
- signal: current FINRA short-volume share minus mean of the 20 prior valid IBIT observations;
- direction: higher short-flow surprise predicts lower subsequent BTC return;
- outcome instrument: Binance Spot BTCUSDT;
- entry: 00:00 UTC at the first safe day after the FINRA trade date;
- exit: exactly 5 calendar days later at 00:00 UTC;
- primary regression: r5 on signal with HAC/Newey-West lag 5; one-sided beta < 0;
- companion sign strategy: LONG when signal<0, SHORT when signal>0;
- costs: BASE10 and STRESS20 bps round trip;
- all frozen promotion gates remain unchanged.

## Firewalls

- 2025 source/outcome access is FORBIDDEN.
- 2026 source/outcome access is FORBIDDEN.
- no alternate ETF;
- no alternate horizon;
- no threshold rescue;
- no change to baseline length;
- no cost rescue;
- no price/volatility/sentiment/funding/OI/CFTC filters;
- no post-outcome tuning;
- no live trading;
- no exchange mutation;
- no merge to main;
- no deployment.

The Discovery runner MUST fail closed before BTC source access if the frozen protocol SHA256 does not match exactly or if the regenerated FINRA Source/Data Gate does not classify `SOURCE_DATA_PASS`.

Any valid Discovery result is final for this exact MVE. Any materially changed mechanism requires a new MVE ID and new prospective authority.
