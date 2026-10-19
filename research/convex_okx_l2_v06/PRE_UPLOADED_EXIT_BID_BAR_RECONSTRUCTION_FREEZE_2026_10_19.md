# CONVEX V06 — ORIGINAL STOP-INTRABAR EXIT L2 BID SOURCE FREEZE

Date 2026-10-19 UTC, frozen **before inspecting the two user-uploaded exit dates around historical stop windows**. Research-only, in-sample 2023. Two original official OKX portal tar.gz uploads reside in the private chat sandbox, never to public GitHub:

- `SOL-USDT-SWAP-L2orderbook-400lv-2023-06-05.tar.gz` (exit day, original SOL1h V5 entry 2023-05-29 16:05 UTC)
- `BNB-USDT-SWAP-L2orderbook-400lv-2023-11-21.tar.gz` (exit day, original BNB4h V5 entry 2023-11-01 16:05 UTC)

Frozen by immutable original trading CSV run 38432883246, exit-day locator GitHub Actions 39210167738:
- SOL original LONG `close_t` 2023-06-05 16:05:00 UTC, `STOP_INTRABAR`; original stop-cross 5-minute **bar** starts **16:00:00 UTC**.
- BNB original LONG `close_t` 2023-11-21 17:45:00 UTC, `STOP_INTRABAR`; original stop-cross 5-minute **bar** starts **17:40:00 UTC**.
Source original model code `research/btc_convex_timeframe_matrix_20261013/matrix.py`: for `STOP_INTRABAR` uses 5min bar low <= preexisting stop, assumes synthetic fill at raw stop * (1 - 2bps BASE adverse slippage); ledger time `close_t=t+5min` is **bar end, not broker stop trigger time**.

## Frozen source and tests
1. Confirm original user-source filenames, exactly one .data regular member, UTC date/instrument, initial snapshot, chronological updates, valid sides and no crossed bids vs asks, 400-level order book at sampled timestamps. No fabrication of sequence ID; if absent explicitly SOURCE_CONTINUITY_UNVERIFIED; SHA256 of local file is not OKX publisher signature.
2. Book reconstruction processes all records from day's first snapshot strictly until **before** original bar close. Sampling grid fixed for each original 5minute stop bar: six **causal** time points, `bar_start + {0,60,120,180,240}s` and `bar_end-1ms`. Each uses last source update with timestamp <= sampling time and age <=2000ms, except no quote -> reject. No futures after sample used. Archive can be traversed once per venue; no reordering.
3. At each sampled quote, evaluate **BID** sell-side for original paper base-asset qty with 4 ratios {0.25,0.5,0.75,1.0}. The only contract multipliers allowed are the launch-announcement historical **provisional** SOL=1 SOL/contract, BNB=0.01 BNB/contract. MUST label `CONTRACT_METADATA_UNVERIFIED_AT_2023_DATE`; lot step/rounding not verified; raw sweeps are **conditional unrounded static** and never actual submitted order size. Record full requested base qty, best BID, bid qty, available total, levels traversed, sell VWAP, adverse walk bps vs best bid. Source cross-venue market vs Binance original entry triggers not inherently transferable.
4. Original actual model `stop` value must be recovered independently only from *unchanged* original 2023-25 trade CSV (selected open_t and qty) and original model BASE `exit_price`: infer raw stop threshold exactly for STOP_INTRABAR via `exit_price/(1-0.0002)`; original paper intrabar price is **not a broker-side trigger and exchange trigger type is unspecified**. Actual OKX book bid <= Binance stop in target bar is a cross-venue **price comparison only**; never claim a real stop should have executed then.
5. For **all chronological L2 events in the original 5m bar**, measure earliest observed time the **best BID** crosses below paper Binance raw stop threshold and report timestamp/distance, if valid reconstruction continuous enough. If none, `NO_OKX_BID_CROSS_IN_THIS_BAR`, not skip or invent fill. This is **not** earliest stop during whole original holding interval, which is NOT analyzed. Record range of 5m bar best bid and widest observed spread, count of updates. If an exchange-native stop may trigger on mark/index/last instead of BID, these events are *not* evidence of actual stop trigger.
6. Report original source modeled trade entry/exit prices solely as reference; do **not** reconstruct full exit trade PnL, after-fee economics, post-event re-entry, funding, margin or portfolio performance. Chronological sampled BID path and hypothetical static SELL VWAP are valid as **only source evidence**. No cherry-picked favorable sample time or new parameter thresholds after observing.
7. Custody user-uploaded raw source .tar.gz never redistributed or committed to GitHub; only derived receipt file with SHA, timestamps, summary book metrics, original-model threshold for documented comparison. Public CI uses **synthetic-only archives** in Windows/Linux. True source processed privately in conversation sandbox. Cross-platform CI PASS does not certify real book continuity or profitability.

## Gates
- Chronological quote reconstruction: require initial complete snapshot and T0 freshness <=2s, within UTC date, expected instrument, valid book >= 1 bid/ask and 400 levels for samples; no post-event lookahead.
- No true raw publisher checksum (SHA of user download only); sequence IDs absent means SOURCE_GAPS_NOT_EXCLUDED.
- TRUE executable exit: UNKNOWN without native stop ACK, actual trigger source, exact real order size/lot and latency, and historical OKX fee/funding; OOS 2026 remains locked.
- Full end-to-end strategy outcome: NOT tested with just these two trade examples.
- Stop protection must not be weakened to backfit 2023 outcome.

**LIVE GO NONE. NO MERGE main, NO REAL ORDERS, NO PRIVATE API, NO EXPENSES, NO WALLET / FUTURES ACCOUNT, NO PROTECTED 2026 OOS.**
