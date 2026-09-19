# OPTIONS-EXPIRY-GAMMA-001 — SIGNED FLOW CORPUS SOURCE CLOSEOUT V0.5

Date: 2026-09-19
Source gate: OEG-TARDIS-SIGNED-FLOW-CORPUS-005
Canonical run: 35428784200
Canonical head SHA: 8a16a7f59f6b4f1b18e60e048056fdbf6a6f15e0
Canonical aggregate artifact: OEG_SIGNED_FLOW_CORPUS_SOURCE_V0_5
Artifact ID: 10580281819
Artifact ZIP SHA256: 668ddfbb00b6ac6d5c552f8cd349509288fd434a3db529119eb156e9f3cc4a4d

## FINAL CLASSIFICATION

SIGNED_GAMMA_FLOW_CORPUS_SOURCE_PASS

## OUTCOME-BLIND RESULT

- total deterministic free first-of-month dates: 48
- passing dates: 48
- 2021: 12/12
- 2022: 12/12
- 2023: 12/12
- 2024: 12/12
- technical error dates: 0
- API key used: false
- subscription purchase: false

The source contract is Tardis Deribit first-day-of-month free OPTIONS trades + options_chain. The source gate proved adequate taker-side trade data plus contemporaneous OI/gamma coverage and dynamic OI evidence across the complete 2021-2024 monthly free corpus.

## SCIENTIFIC LIMIT

This PASS does not infer dealer inventory or dealer gamma sign. Tardis trade side is the liquidity-taker/aggressor side. A later hypothesis may therefore study signed gamma demand/flow without treating the opposite side as a known dealer book.

No BTC outcomes, returns, PnL, option values, retained gamma values or retained OI values were opened under this gate.

## RELEASE

A separately frozen Discovery may use the 48 passing dates. Any outcome definition, DTE filter, gamma-flow proxy, BTC source, horizon and statistical gates must be frozen before BTC outcomes are opened.

2025/2026 access: false
Live trading: false
Exchange mutation: false
Merge to main: false
