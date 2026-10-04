# MEXC GLOBAL-ASSET TRANSFER V0.5 — CLOSEOUT

Date: 2026-10-04
Branch: `mexc-globalasset-transfer-v0.5-prereg-2026-10-04`
Run: `37235872887`

## Frozen evidence

Source gate:
- run `37235636339`
- source artifact SHA256 `94f8a3865c6f6619a9cebf1ca8c546557cb538579c01fc1f82e26d7416b0b78a`

V0.5 family artifact:
- artifact ID `11315452120`
- SHA256 `1fd39b9a6224d3210e74ba8ee12f9486d35ff8dd1a5f9ece7fc986353a47c5f3`

Family size:
- 35 source-pass assets
- all 35 receipts completed successfully

Rule:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS
- external = mean(Binance + Bitget)
- no per-asset tuning

Multiplicity:
- Holm-Bonferroni FWER 0.05 across all 35 assets.

## Verdict

Scientific PASS:
- 31 / 35 assets

Fee-floor survivor after 12 bps:
- 0 / 35

Robust fee survivor after 16 bps:
- 0 / 35

Overall:
`SCIENTIFIC_TRANSFER_SURVIVORS_FOUND__STANDARD_API_FEE_BLOCKED`

Top gross mean:
1. VRTSTOCK_USDT: +5.724073 bps, N=818, 73.7164% wins, p=1.188627e-43
2. MRVLSTOCK_USDT: +5.675484 bps, N=577, 70.0173% wins, p=1.390494e-22
3. COINBASE_USDT: +5.640436 bps, N=1101, 68.7557% wins, p=1.575462e-36
4. PDDSTOCK_USDT: +5.293423 bps, N=322, 60.5590% wins, p=8.967088e-5
5. CRWVSTOCK_USDT: +5.234450 bps, N=1110, 61.9820% wins, p=6.641274e-16

Even the best gross mean remains below the frozen 12 bps maker-maker API round-trip floor.

## Interpretation

The 5/3/1m lead-lag mechanism is broadly replicated across MEXC global-asset contracts, but its economic magnitude is structurally too small for the currently documented standard MEXC Futures API tariff.

Continuing to mine more assets under the same rule is not a legitimate route to API profitability unless the execution tariff or execution route changes.

No retrospective rescue, parameter change, private endpoints, account reads, orders, wallets, exchange mutation or live trading were used.
