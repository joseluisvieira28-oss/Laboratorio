# ETF-SHORTFLOW-001 — ACTIVATION V0.1

STATUS: ACTIVE — SOURCE/DATA GATE ONLY

## Why this is a new mechanism

This lab is NOT a rerun of ETF-CME-INSTFLOW-001.

The existing institutional-flow lab tests weekly CFTC/CME non-commercial positioning. Its historical Discovery verdict remains immutable and its separately authorized 2025 OOS V2 result remains a Tier 2 promoted fragile candidate.

ETF-SHORTFLOW-001 instead tests daily publicly reported FINRA off-exchange short-sale volume in a U.S. spot Bitcoin ETF as a possible informed-flow transmission signal into BTC.

Anti-duplication checks before activation:
- GitHub default-branch code search: no FINRA/IBIT short-sale-flow lab found;
- Google Drive search: no FINRA/IBIT short-sale-flow lab found;
- File Library search: no canonical FINRA/IBIT short-sale-flow execution found;
- existing ETF-CME-INSTFLOW-001 reviewed and classified PARTIAL_OVERLAP_BY_THEME / NEW_MECHANISM.

## First MVE

Lab ID: `ETF-SHORTFLOW-001`

MVE ID: `ESF-IBIT-SHORTVOL-5D-001`

Primary source candidate: FINRA Consolidated NMS Daily Short Sale Volume files.

Primary symbol: `IBIT` only.

Discovery source window: 2024-01-11 through 2024-12-31 only.

2025: LOCKED.

2026: LOCKED.

## Governance

- research-only;
- fail-closed;
- no live trading;
- no exchange mutation;
- no merge to main;
- no deployment;
- no post-outcome tuning;
- no ticker rescue;
- no horizon rescue;
- no threshold rescue;
- no cost rescue;
- no sentiment overlay in MVE0;
- no CFTC, funding, OI, ETF net-flow or options variables in MVE0;
- source/provenance before market outcomes.

## Current authorization

Only the outcome-blind FINRA Source/Data Gate is authorized.

No BTC price, forward return, signal-return relation, PnL, 2025 or 2026 data may be opened by this activation.
