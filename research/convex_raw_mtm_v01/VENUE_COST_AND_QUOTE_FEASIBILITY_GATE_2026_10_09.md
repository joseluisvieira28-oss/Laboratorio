# VENUE COST & HISTORICAL QUOTE SOURCE GATE — 2026-10-09
**Scope**: read-only documentation/source feasibility; this is NOT an executed venue-specific microstructure replay.

## Source identities, costs and portability
1. Parent V5 historical Binance USD-M 1h engine hard-freezes commission **10bps PER SIDE**, BASE adverse slip **2bps PER SIDE**, STRESS **5bps PER SIDE**. Hence original BASE modeled roundtrip fee+slip **24bps** and STRESS **30bps**, not 10/16bps. Historical funding is exact *Binance* funding, not MEXC; all original ETH/SOL/BNB fills are Binance 1h next-open/stop BAR-MODEL assumptions.
2. MEXC official publication **May 28 2026**, applied to Futures API from **June 1 2026 at 08:00 UTC**: maker **0.06%** each side, taker **0.08% each side** = **16bps full taker-taker roundtrip fees BEFORE spread/slippage/funding**, excluding Innovation Zone pairs, account/region service access may vary. Note API pricing takes precedence over consumer app promotional advertised fees. Official link: https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742
3. Binance official public history catalog: https://github.com/binance/binance-public-data/blob/master/README.md and https://data.binance.vision . Data include OHLCV, trades, aggTrades, funding source records from official API. **None of these OHLCV/actual trade prints inherently give point-in-time bid + ask + depth, especially NOT for MEXC venue.** A signed historical order book source must be separately proven at trade decision UTC with age, spread, size, min contract, and meaningful capacity.
4. Comparison *arithmetic* with current MEXC taker fees: original Parent BASE (20bps commission + 4bps assumed slip) = 24bps; MEXC current official API taker-taker fees 16bps, **plus unknown roundtrip marketable spread/impact/slip/funding**. Treating the difference as 8bps "found edge" is invalid. Source venue differs, fee tier may change, destination eligible by locale and account. No authenticated exchange endpoints queried here.
5. No point-in-time MEXC Futures BBO/depth archive proven for the full 2021–2025 original signal windows. Status **MEXC_EXECUTION_FEASIBILITY_SOURCE_NOT_ESTABLISHED**. Do not synthesize quote spread from 1h high-low, Binance trade prints, or present-day market snapshots.

## Required gate for future executable feasibility claim (not outcome-time future wait)
- Historical public/legally accessible archived MEXC futures best bid & ask + depth for ALL intended entry/stop timestamps and sufficient normal/liquidation stress hours; hashes and completeness.
- Same timestamp clocks and primary venue symbol identity, independent trade size, min lot, margin and stop order mechanics.
- Consistent final matched order price and fees incl exchange API schedule, funding history and fees not charged twice.
- For missing source: fail-closed feasibility, historical scientific local PASS may remain, live execution profit unverified.

No trading, exchange mutations, private account reads, fee-tier assumption reduction to rescue failed experiments.
