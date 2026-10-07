# MEXC-LAUNCHPOOL-MX-DEMAND-001 — ACTIVATION PILOT V0.2.2 CLOSEOUT
Date: 2026-10-07
Branch: mexc-launchpool-mx-demand-v0.2-activation-pilot-2026-10-07

## Verdict

**PILOT_NO_SIGNAL**

Role: exploratory activation-time pilot only. Promotion credit: ZERO.

This verdict does not adjudicate the separate announcement-time parent hypothesis.

## Frozen design

- 14 source-bounded official MEXC Launchpool events with explicit MX staking
- T0 = exact Launchpool staking activation time
- MXUSDT versus BTCUSDT
- 15-minute MEXC spot candles
- entry = first exact 15m open at T0
- primary exit = exact +24h 15m open
- primary response = log(MX_exit/MX_entry) - log(BTC_exit/BTC_entry)
- no event deletion or horizon change after outcomes

## Data remediation

Initial V3 public REST coverage resolved only 2/14 events.

A pre-committed technical remediation then used the official MEXC historical market-data archive for missing 2025 rows:
- exact same MXUSDT and BTCUSDT instruments;
- exact same 15m timestamps;
- no scientific-rule change.

Official archive symbol IDs:
- BTC_USDT: 2fb942154ef44a4ab2ef98c8afb6a4a7
- MX_USDT: 7fb2a8ab8a5e4eb699ac34ee340489f8

Final authoritative run:
- GitHub Actions run: 37619015724
- artifact ID: 11480654596
- artifact digest: bad54d7329b9a5daba7ad18edd877207f70cb1aafdf41b4bafa910788190b632

## Results

- frozen events: 14
- analyzable: 13
- positive: 6
- positive fraction: 46.1538%
- mean relative log return 24h: -0.27264%
- median relative log return 24h: -0.21127%
- exact one-sided sign p: 0.70947
- bootstrap 90% CI for mean: [-0.84036%, +0.27326%]
- leave-one-out minimum mean: -0.41968%

By year:
- 2025: N=11, mean -0.31335%, median -0.21127%, positive fraction 45.45%
- 2026: N=2, mean/median -0.04875%, positive fraction 50%

Event relative 24h results:
- APT: -2.0574%
- IP: -0.3326%
- TERM: -2.7931%
- K: +0.6080%
- MNT: missing exact candle
- EPT: -1.5439%
- SHM: +0.8308%
- ICEBERG: -0.2113%
- BOMB: +1.4919%
- EURR: +1.2537%
- USDR: -0.8939%
- EIN: +0.2010%
- EMBLEM: -0.5045%
- NEX: +0.4070%

## Frozen gate adjudication

PILOT_SIGNAL_PRESENT required ALL:
- N >=10: PASS (13)
- median >0: FAIL
- positive fraction >50%: FAIL
- one-sided sign p<0.10: FAIL
- leave-one-out minimum mean >0: FAIL

Therefore: PILOT_NO_SIGNAL.

## Missing MNT robustness

The single missing MNT observation cannot change the verdict under the frozen gate.

Even if MNT were positive:
- positive count would be 7/14 = exactly 50%;
- the frozen gate requires >50%.

Therefore no technical recovery of MNT can convert this pilot to SIGNAL_PRESENT.

## Interpretation

There is no evidence in this frozen pilot that the **start of MX staking itself** creates positive 24h MX-relative-to-BTC performance.

This does NOT test or reject the separate hypothesis that the **announcement publication timestamp** creates an earlier information/demand effect. That parent study remains separately frozen and must be adjudicated independently.

## Governance

No authenticated API, account read, order, exchange mutation, wallet action, spending, main merge or post-outcome tuning occurred.
