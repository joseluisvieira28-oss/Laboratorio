# MEXC CRCL REGULAR-SESSION PACK — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE CRCL OUTCOMES

Target: MEXC `CRCLSTOCK_USDT`.
External public legs: Binance `CRCLUSDT`, Bitget `CRCLUSDT`.

Source gate run `37230232528` returned `CRCL_REGSESSION_PUBLIC_CORE_SOURCE_PASS`.
The source-verification day `2026-09-30` is excluded.

Frozen sample: weekdays `2026-09-09 ... 2026-10-02`, excluding 2026-09-30.
Signal window: `14:31 ... 18:44 UTC`.
Closed 1-minute candles, observable at candle start +60s. Exact timestamps only; no fill/interpolation.

External return = mean(Binance, Bitget 1m returns).
MEXC return = CRCLSTOCK_USDT 1m return.
Lag gap = external - MEXC.
Direction = FOLLOW_EXTERNAL_CONSENSUS.

Total alpha 0.05 is split before outcomes:
- 0.025 exact transfer test: shock>=5, gap>=3, horizon=1m, 1m cooldown;
- 0.025 exploratory grid: shocks 5/10/20/40, gaps 3/5/10/20, horizons 1/2/5/15, Holm across 64 cells.

Transfer PASS requires N>=50, >=12 signal sessions, mean/median>0, win>50%, all thirds>0, one-sided binomial p<0.025.

Exploratory eligibility requires N>=20, mean/median>0, win>50%, all thirds>0; Holm FWER=0.025.

Costs 0/2/5/10/12/14/16/18/20 bps are reported separately and are not scientific gates.

No rescue after outcomes. No retrospective OOS, private endpoints, account reads, wallets, orders, exchange mutation or live trading.
