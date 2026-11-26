# LIQMAP-DIAMANTE-001 — Pre-registration 2026-11-26
NO TRADING. Crypto Lab original PROXY, NOT Neuron proprietary calculations, not actual observed liquidation orders.

## Source / historic window frozen now
Bybit public unauthenticated BTCUSDT and ETHUSDT linear perpetual 1h candles (v5/market/kline interval=60) and open interest (v5/market/open-interest intervalTime=1h, max 200/page), UTC 2026-11-01 00:00 through 2026-11-25 00:00 exclusive (576 hours per market). Require 576 unique contiguous aligned hourly timestamps, positive OHLC and OI. No synthetic substitution, interpolation, gaps, future incomplete bars or backfill after seeing outcomes; record URLs + response SHA256 and publication times. HTTP/source errors => SOURCE_BLOCKED.

## Model — assumed liquidation pools only
At each closed candle t: take positive delta OI (reported for both sides), seed hypothetical long/short positions 50/50 at assumed leverage 10x/25x/50x with weights 0.5/0.3/0.2; estimated liquidation close*(1-1/L) or close*(1+1/L). Half-lives 72/36/12 hours; discard after 120h; clear earlier levels swept within the just-closed candle high/low. Seed mass proportional to deltaOI*close and never treat it as verified position/liquidation dollars. Aggregate into log-price bins width 0.0025; consider bands at log distance 0.005..0.05 from current close. Choose bin of greatest sum decayed mass * exp(-abs(log price gap)/0.03). If none, NO_SIGNAL. Direction to selected band, counter barrier exactly symmetric log distance.

## Falsification / controls
Use evaluations every six hours from index=120, then 126,..., using ONLY closed history up to t, and next 6 bars (t+1..t+6) for outcomes. Outcomes TARGET_FIRST/OPPOSITE_FIRST/NEITHER/AMBIGUOUS (same bar both touched). Rates calculated solely over first two, Wilson 95% per coin; report all no-hit/ambiguous counts. Compare exact same barriers against 6h price momentum direction baseline; 50% direction chance is weaker null. Avoid overlapping 6h trials. Simulated futures-style long/short entries at next open and exit at barrier/6h close, both-hit pessimistic loss, hypothetical 10/35/80bps PER side plus 5bps slippage PER side; funding, future mark price and execution not modeled. Block bootstrap 4 event blocks x 2000 seed 6001 for paired excess PnL, separately by symbol. History is retrospective.

## Strict economic decision
For even prospective CANDIDATE: >=50 resolved events separately BTC and ETH, Wilson lower >50% for each, >+5pp directional advantage vs MOM6, positive pseudo-PnL after 80bps/leg, replication in another independent period/venue, no false discoveries. Otherwise NO-GO or INCONCLUSIVE. Not enough history does not imply negative edge. Never LIVE GO based on this study. Hypotheses frozen; no parameter tuning, selecting best tier/window after result, or relabeling proxy as vendor map.

## Safety
No personal accounts, private APIs, subscriptions, paid datasets, trading, trades, orders, money, leverage, deployment or merge. Draft PR only.
