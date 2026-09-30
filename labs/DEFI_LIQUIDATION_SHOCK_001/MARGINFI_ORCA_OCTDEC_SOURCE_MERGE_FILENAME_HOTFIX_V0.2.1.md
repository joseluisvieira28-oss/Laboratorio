# DLS — MARGINFI ORCA OCT-DEC SOURCE MERGE RECEIPT FILENAME HOTFIX V0.2.1

Date: 2026-09-30
Branch: dls-marginfi-orca-impact-v02
Status: FROZEN OPERATIONAL HOTFIX / SOURCE-ONLY / BEFORE MARKET OUTCOMES

Canonical source shard run:
36781844349

Observed state:
- 16 / 16 source shards completed PASS;
- 2,688 / 2,688 adjudication rows were produced;
- no shard failure;
- merge step classified BLOCKED only because the merge reader looked for:
  MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_RECEIPT_V0.2.json

The canonical Oct-Dec population artifact actually contains:
  MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_RECEIPT_V0.2.json

This is a filename-binding bug only.

Authorized correction:
replace the expected receipt filename with the exact canonical Oct-Dec population receipt filename.

No other code, source rule, population, decoder, threshold, market rule, gate, or semantic may change.

The 16 immutable source shard artifacts from run 36781844349 must be reused unchanged.
No shard rerun is required for this hotfix.

No Oct-Dec OHLC, returns or PnL have been opened.

Firewall:
prices=false
ohlc=false
returns=false
pnl=false
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
