# BTC-CONVEX-TREND-CAPTURE-001 — R0 1H ENTRY SOURCE REPRODUCTION CLOSEOUT V0.1

**Date:** 2026-09-23  
**Workflow run:** 35910617874  
**Artifact:** 10773730205  
**Artifact SHA-256:** 2c51a04efcb30b8b2b0ea192f39e64424c6594460876baf916a1d369ceda791d  
**Status:** ENTRY SOURCE REPRODUCTION PASS / EXECUTION INTEGRITY NOT PASSED

## Source coverage

Official Binance USD-M BTCUSDT 1h monthly archives were used.

2019-09 through 2019-12 monthly futures archive paths returned 404, leaving six 2019 entries source-unverified.

From 2020 onward:
- 57,696 official 1h bars loaded;
- 95 observed entries source-verifiable.

## Ordinary entries

There are 87 source-verifiable ordinary entries.

Result:
- recovered Pine entry condition is TRUE on the previous closed bar for **87 / 87**;
- reported TradingView entry price is within 1 bp of the next Binance bar OPEN for **87 / 87**.

Therefore:

**ORDINARY_ENTRY_SOURCE_REPRODUCTION = PASS**

The recovered Pine code explains every verifiable ordinary 1h entry timestamp and fill architecture.

## Same-bar reentries

Eight entries occur at the exact timestamp of the preceding exit.

Results:
- recovered Pine signal using the **final values of the same historical bar** = TRUE for **8 / 8**;
- recovered Pine signal on the **previous bar** = TRUE for only **5 / 8**;
- nearest Binance historical OHLC tick:
  - LOW = 7
  - OPEN = 1
  - HIGH = 0
  - CLOSE = 0

Three same-bar reentries therefore require the current bar's final indicator values; the signal did not exist on the prior closed bar.

Those trades are:

| Trade | Entry UTC | Prior-bar signal | Fill fingerprint | Net PnL |
|---|---|---|---|---:|
| 17 | 2020-08-02 04:00 | FALSE | LOW | +384.06 USDT |
| 52 | 2022-07-11 01:00 | FALSE | LOW | -1,203.27 USDT |
| 70 | 2024-03-05 19:00 | FALSE | LOW | +5,900.91 USDT |

Descriptive combined PnL = **+5,081.70 USDT**.

This subtraction is NOT a valid counterfactual because removing trades changes future equity sizing and potentially state.

## Execution-integrity interpretation

TradingView documents that when executions after order fills are enabled:
- the script can recalculate immediately after a historical fill;
- historical current-bar price/volume variables can contain the bar's final values;
- this can create lookahead bias;
- historical fills can occur at OHLC ticks unavailable as known future prices in real trading.

The observed 1h pattern matches that warning directly:
- exit fills intrabar;
- strategy recalculates while flat;
- current bar final signal is TRUE;
- a new entry is filled at the historical LOW;
- for three trades, the same signal was not available on the previous completed bar.

Classification:

**SAME_BAR_REENTRY_LOOKAHEAD_CONTAMINATION = PROVEN FOR 3 SOURCE-VERIFIABLE 1H TRADES**

This does not imply that all 1h entries are contaminated. The 87 ordinary entries reproduce causally from the previous closed bar.

## Entry-rule simplification confirmed

The source contains:
- `sinalZ = zScore < -2`;
- `sinalBB = close < SMA20 - 2 × STDEV20`.

Across the reproduction:
- boolean mismatches between `sinalZ` and `sinalBB` = **0**.

They are the same condition under the supplied defaults.

For all 95 source-verifiable entries:
- the 2-sigma downside condition is TRUE;
- volume > SMA20(volume) is TRUE.

Confirmation branch counts:
- Z/BB + VOLUME, RSI not required: **87**
- Z/BB + VOLUME + RSI<30: **8**
- RSI-only confirmation: **0**

Therefore, in the verified 2020-2026 entry sample, RSI never creates an entry that volume would not already create.

The observed source behavior is effectively:

**close > SMA200  
AND close < SMA20 - 2σ20  
AND volume > SMA20(volume)**

with RSI acting as a redundant additional score point in these observed entries.

This is descriptive source reconstruction, not authority to delete RSI from a future rule.

## Remaining R0 blocker

Entry-source reproduction has passed.

Full strategy R0 has NOT passed because the exit layer can also be affected by recalculation after order fills.

On a historical entry fill, an additional execution can expose final current-bar `high` and `close`. The recovered exit code immediately uses:
- `high` to initialize/update `precoPico`;
- `close` to decide whether the +5% trailing regime is active.

Therefore full exit PnL must be retested under a causal execution protocol before any edge or promotion claim.

## Verdict

**ENTRY SOURCE = REPRODUCED**  
**ORDINARY ENTRY TIMING = PASS**  
**3 SAME-BAR 1H ENTRIES = HISTORICAL LOOKAHEAD CONTAMINATED**  
**FULL EXIT / PNL INTEGRITY = BLOCKED**  
**EDGE = UNPROVEN**

No promotion, live trading, exchange mutation or main merge is authorized.
