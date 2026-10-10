# RW-HL-EXITFLOW-001 — SOURCE-FIRST CONTINUATION & FINAL HANDOFF 2026-10-09

Scientific classification: **PROSPECTIVE_PUBLIC_SOURCE_FEASIBLE / HISTORICAL_OI_NOT_AUTHORIZED_NO_COST / ECONOMIC_HYPOTHESIS_UNTESTED**
Trading authority NONE. No main merge, no external expenses, no wallets/accounts/trades.

## 1. Mechanism, not a magic signal
Primary published source: https://edgealchemy.robotwealth.com/p/hyperliquid-carry-looks-trendy
Kris Longmore observes a disparity between Binance vs Hyperliquid carry-factor outcomes in frictionless comparisons, especially extreme negative Hyperliquid funding where longs collecting funding can lose on price continuation. "Informed selling"/holders avoiding on-chain spot disposal is the author's proposed causal story; **not established insider identity or proof of positive net trading returns**.

What might be new: point-in-time Hyperliquid OI growth + negative funding and actual newly listed symbol status, prospectively observed and controlled for common market movements. Selling a postlaunch perp or naive negative-funding momentum are not novel by themselves; Crypto Lab freezes of postlaunch SHORT, basis convergence, and funding×OI interactions are preserved.

## 2. Source audit complete (no fee expenditure)
- [G1 public Hyperliquid data probe](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37938587198): 14 synthetic PASS, 178 live markets with aligned openInterest/mark/funding in each of 2 prospective snapshots on Oct09 13:41 and 13:42 UTC. SHA256 preserved as GitHub artifact `11620221130`. `fundingHistory` for BTC on 2024-01-01 returned 24 records; source count only. No future markouts.
- Hyperliquid `metaAndAssetCtxs` supplies current market OI/mark/funding; it DOES NOT supply 2024 OI history or first official listing T0.
- Official requester-pays historical `asset_ctxs` S3 archive not fetched; no user expenses. See https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- Dune public pages show `hyperliquid.market_data` and historical OI, e.g. https://dune.com/queries/6339221/10088072, but the web-accessible chart is **NOT yet an independently verified reproducible free/full point-in-time export**. Dune's API needs a key and its perpetual datasets may require an Enterprise tier. DO NOT treat a displayed dashboard as an acquired time-series corpus or silently scrape around access controls.
- No one authenticated as user or queried private accounts.

## 3. Immutable first prospective multi-snapshot capture — RECOVERED
First source capture run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37939142048
- 23/23 synthetic tests PASS.
- 3 authentic public-market-only snapshots, each 178 valid markets: Oct09 **13:45:40.212504**, **13:46:40.518616**, **13:47:40.697753 UTC**.
- Time-ordered original sha-chain terminal:
  `3c9d8c54d00d20be035f8add10123a75002d42b87d32006ed757e701b7fa2c31`.
- First job's HTTPS Git push was rejected `non-fast-forward` after a separate audit commit landed on the same research branch while capture ran. Observations were **not lost**: uploaded immutable artifact `11621135724` SHA256 `b161bbc3624d0a29fd8bacda5b99ed8dc97ae6e64b93302068961e02b62b135c`.
- Independent technical recovery https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37939670207 succeeded, 6/6 synthetic recovery tamper tests PASS. It downloaded ONLY the original source artifact without any extra market call; verified all 3 original SHA256 byte hashes, sequential receive timestamps, original run identity, hash-chain and no outcomes; then wrote those same bytes under:
  `research/rw_hl_exitflow/intake/2026-10-09/2026-10-09T13-45-40_212358Z_37939142048/`
- GitHub research-branch recovery commit `3bf34a3` verified on remote; no main merge, no source rewrite. Recovery receipt artifact `11621460985`.
- No market direction, entry, exit, momentum, funding carry, PnL or future return computed. Three minutes of observations do NOT establish a trend or evidence of informed sellers.

## 4. Economic warning
Hyperliquid documented standard base fees at observed source research: taker 0.045%/fill (4.5bps); maker 0.015%/fill (1.5bps) for perp markets without special fee modifiers:
https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
A simple taker short entry/exit costs >=9bps in direct exchange fees before spreads, impact, slippage and leverage. Actual account-specific rates, HIP-3 deployer/growth settings may differ.

Funding settles hourly on Hyperliquid:
https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
**Negative funding => SHORTS PAY LONGS**. So following negative funding via shorts pays the crowded-side carry rather than harvesting it. At illustrative -1bp/hour for 24h that is 24bps funding against short, plus 9bps base taker round trip, or **33bps minimum illustrative gross price-move hurdle** BEFORE spread and adverse fill. Do not mistake this hypothetical for observed net PnL.

## 5. Scientific decision and non-duplication
- `PERP-LAUNCH-POSTLAUNCH-SHORT-001`: same generic new-perp short story already frozen; 83 2023 events but 0 complete eligible trades => INSUFFICIENT_DISCOVERY_SAMPLE, 2024 price outcomes unopened.
- `PERP-LAUNCH-BASIS-CONVERGENCE-001`: frozen 2023 Discovery NO NET EDGE.
- `DCV-001`: triple funding×OI×volatility 2021–23 Discovery FAIL.
- `FUNDING-DISPERSION-DN-001`: Bybit/OKX funding carry SOURCE_BLOCKED.
- This project is allowed to proceed ONLY for the distinct venue- and *contemporaneous OI-source* hypothesis if a forward point-in-time data corpus emerges. It is not allowed to rescue older failed or blocked families by thresholds, 2024 reuse, crypto tickers or cost cuts.

## 6. Next required gates
A. **Automated observation cadence + append-only store:** require explicit operational scheduler authorized on a non-main surface with known zero incremental expenditure, or operator-triggered forward batches; no runnable branch-level cron has been created. Github Actions `schedule` on non-default branch alone is not an effective automation.
B. **Verified first-listed cohort:** use official listing T0 announcements/events; first observed market from periodic API is interval-censored, NOT precise listing T0. Guard symbol renames, delistings, pricing precision, OI units, missing snapshots.
C. **Causal count-only pilot:** pre-freeze contemporaneous OI growth, negative funding persistence, price weakness definitions, minimum events and independent comparator BEFORE viewing any later price outcomes. No post-event threshold tuning.
D. **Separate economic freeze and legitimate forward:** fee tier/route, funding accrual, spread/depth, slippage, latency, squeeze/margin controls, true capacity and a suitably long prospectively unobserved outcomes period. Fail closed if event/sample count inadequate.
E. No 2025 or pre-frozen 2026 outcomes may be opened as a convenient quick profit check. Earlier G1 snapshots remain SOURCE-ONLY.

**This deliverable is NOT a small diamond or a micro-live candidate. It is a strong public-source pathway plus explicit block on economically meaningful validation without continued collection.**
