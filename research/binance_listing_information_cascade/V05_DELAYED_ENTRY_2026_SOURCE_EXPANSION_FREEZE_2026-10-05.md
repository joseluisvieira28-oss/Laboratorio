# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.5 DELAYED-ENTRY 2026 SOURCE EXPANSION FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2026 MARKET OUTCOME ACCESS

Parent: V04_DELAYED_ENTRY_2026_HOLDOUT_PRE_OUTCOME_FREEZE_2026-10-05.md

V0.4 source gate found only 7/20 valid observations using Bitget -> KuCoin. No 2026 market outcomes were opened.
V0.5 changes SOURCE ARCHITECTURE ONLY, before outcomes.

## Frozen venue hierarchy V0.5
1. Bitget spot
2. KuCoin spot
3. MEXC spot public market data

MEXC is used only when both Bitget and KuCoin lack frozen source coverage.
No later venue shopping inside V0.5.

## Everything else unchanged
- same frozen 2026 census interval and candidate set;
- same structural exclusions;
- same >=24h pre-T0 requirement;
- same delayed LONG entry at OPEN of M+1m;
- same H5/H15/H60 definitions;
- same volume shock;
- same n/performance/LOO/concentration gates;
- same governance and no-trading restrictions.

If source coverage reaches n>=12, an activation freeze listing the exact observation->venue mapping must be committed before any 2026 returns are calculated.
If n<12, V0.5 is SOURCE_BLOCKED and no outcomes are opened.
