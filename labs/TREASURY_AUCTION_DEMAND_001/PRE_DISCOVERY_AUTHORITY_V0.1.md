# TREASURY-AUCTION-DEMAND-001 — PRE-DISCOVERY AUTHORITY V0.1

Date: 2026-09-16

## Status

`DISCOVERY_PROTOCOL_FROZEN / OUTCOMES_NOT_OPENED / AWAITING_SEPARATE_OUTCOME_AUTHORIZATION`

Source authority: `TAD-COUPON-SOURCE-001`.
Canonical Source Gate: GitHub run `35128643997`, classification `SOURCE_DATA_PASS`.
Canonical source-row SHA-256: `ab2695123b04c6e320bda23e5496b1dcfadabec8c6784211a10407ac87499892`.

No BTC market values have been opened under this lab. This document freezes the future one-shot Discovery before any such access.

## MVE

`TAD-BTC-D1-001`

Economic mechanism: stronger realized demand for U.S. nominal coupon Treasury auctions should ease duration/funding stress and support risk assets; weaker auction demand should tighten financial conditions and pressure BTC. The auction demand measure is the prospectively fixed change in bid-to-cover versus the previous auction of the same original tenor.

## Discovery period and protected holdout

Discovery auction dates:
`2021-01-01` through `2023-12-31` only.

Outcome holdout:
- all BTC outcomes tied to 2024 auction events are LOCKED;
- 2025 LOCKED;
- 2026 FORBIDDEN.

A Discovery pass does not itself authorize 2024 OOS. A later separate OOS authority would be required.

## Signal — frozen

For every retained nominal coupon auction, using only the canonical source construction:

`delta_bid_to_cover = current bid_to_cover_ratio - previous bid_to_cover_ratio for the same original_security_term`

Direction:
- `delta_bid_to_cover > 0` => LONG BTC;
- `delta_bid_to_cover < 0` => SHORT BTC;
- `delta_bid_to_cover == 0` => no trade.

No magnitude threshold, z-score, percentile, yield-tail filter, bidder-share filter, tenor selection, macro regime or volatility filter is permitted.

## Same-date conflict policy — frozen

If more than one eligible Treasury auction occurs on the same auction date:
- if all non-zero signals have the same direction, collapse them to exactly one BTC trade for that date;
- if non-zero signals conflict, take no BTC trade for that date;
- zero-delta auctions do not vote.

This prevents multiple weighting of the same 24h BTC outcome.

## Timing — frozen

The auction event is dated by official Treasury `auction_date`.

To avoid dependence on an exact intraday result-release timestamp, entry is deliberately delayed to:

`auction_date + 1 calendar day at 00:00:00 UTC`

Exit:

`entry + 1 calendar day at 00:00:00 UTC`

Thus the hold is exactly one UTC day.

BTC venue/source:
- Binance Spot `BTCUSDT`;
- official Binance Data Vision monthly `1d` klines only;
- entry price = daily Open at entry timestamp;
- exit price = daily Open at exit timestamp.

Discovery implementation may download only the minimum Binance monthly archives required for 2021-2023 event entries/exits. It must not request 2024, 2025 or 2026 BTC archives.

## PnL / costs — frozen

Gross return:
- LONG: `(exit_open / entry_open - 1)`;
- SHORT: `(entry_open / exit_open - 1)`.

Primary round-trip cost: `10 bps` per trade.
Stress cost: `20 bps` per trade.

Primary evaluation is NET10.
No leverage, compounding, stop loss, take profit or position sizing optimization.

## One-shot Discovery inference — frozen

Primary statistics:
- N resolved trades;
- LONG/SHORT counts;
- mean gross bps;
- median gross bps;
- mean NET10 bps;
- mean NET20 bps;
- NET10 profit factor;
- NET10 win rate;
- calendar-year NET10 mean for 2021, 2022, 2023;
- moving-block bootstrap of mean NET10 with 5,000 repetitions, seed `230911`, block length 5 trades.

## Promotion gates — ALL required

1. resolved trade count `N >= 180`;
2. LONG trades `>= 60` and SHORT trades `>= 60`;
3. mean NET10 `> 0 bps/trade`;
4. NET10 profit factor `> 1.05`;
5. bootstrap 95% lower bound for mean NET10 `> 0`;
6. at least `2 of 3` calendar years 2021-2023 have non-negative mean NET10;
7. no single positive calendar year contributes more than `80%` of total positive gross PnL;
8. exact canonical Treasury source binding passes;
9. 2024/2025/2026 BTC outcome access remains false;
10. no live trading / exchange mutation.

If all gates pass: `DISCOVERY_PASS_CANDIDATE / 2024_OOS_LOCKED`.
If any economic/statistical gate fails after valid outcome execution: `DISCOVERY_FAIL_NO_PROMOTION` and this exact MVE closes. No inversion, threshold, tenor subset, timing, hold, cost, filter or subperiod rescue is permitted.

## Authorization boundary

This freeze does NOT itself authorize BTC outcome acquisition. The next valid action is one explicitly authorized one-shot Discovery execution of this exact contract, or no action.
