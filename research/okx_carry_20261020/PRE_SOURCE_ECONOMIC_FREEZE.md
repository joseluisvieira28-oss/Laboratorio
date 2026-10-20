# OKX SINGLE VENUE SPOT–PERP CARRY: PRE-SOURCE FALSIFIER FREEZE (2026-10-20)
**Scientific scope:** one read-only public snapshot, source-first. No holdout 2026 historic prices, account, login, money, keys, orders, private endpoint, wallet, live trading, Render or main merge.

## Economic mechanism & payer
In a USDT linear perpetual, when funding rate is positive, long perpetual holders pay shorts. A long BTC/ETH/SOL spot plus a short matched USDT perp might receive the payer's funding. Funding changes and can reverse; quotes/basis, capital, margin, hedge mismatch and crashes can wipe out the payment. This is **neither guaranteed arbitrage nor proven edge**.

## Distinctness / no rescue
This is a *different* cash-and-carry implementation from frozen OKX linear-v-inverse V04 (28 FLAT) or the recently source-blocked OKX-v-Bybit pair. No V04 threshold is changed or reinterpreted. ONE new public-source feasibility audit, not a new backtest, and no reopening of prior sample.

## Fixed universe, source and observation
- EXACT BTC, ETH, SOL and OKX global public GET-only endpoints.
- Spot: BTC-USDT, ETH-USDT, SOL-USDT.
- Perp: BTC-USDT-SWAP, ETH-USDT-SWAP, SOL-USDT-SWAP.
- `/api/v5/public/instruments?instType=SPOT&instId=...`, analogous SWAP.
- `/api/v5/market/books?instId=...&sz=5` for each spot/perp.
- `/api/v5/public/funding-rate?instId=...` for swap.
- Request with no credentials, no authenticated derivatives eligibility claims. Public quotes do **not** imply Swiss resident can trade those products.

## Fail-closed source gate
- All five source packets per asset must be status=0, exactly one named instrument, spot+linear USDT-settled live state, valid minSz/lotSz/ctVal/base ctValCcy and fundingRate.
- Nonzero BBO, noncrossed, positive top qty, book age between 0–30s (no future timestamps). Total snapshot window <=30s. No mixed old/new days.
- Next fundingTime must be after acquisition start and the interval 8 hours verified from published prev/next times. If unavailable/other interval: `SOURCE_BLOCKED_INTERVAL`, not a 0 estimate.
- Any missing response => SOURCE_BLOCKED with cause and preserved HTTP hashes, NO resampling/backfill.
- Pre-outcome static symbols/venues, no alternate route or tuning to achieve a positive screen.

## Locked conservative hypothetical economics
- Model four taker fills: spot buy + spot sell at 10bps each, perp short + perp cover at 5bps each => **30bps roundtrip fees** per matched exposure. Separate STRESS = **60bps**, ignoring any fee rebates. **These are illustrative protocol assumptions, NOT a certified Swiss/account fee tier**. Any real fee quote must be obtained from user-specific venue, later and separately, without retrospective replay rescue.
- Current-book roundtrip top-of-book cost proxy bps: `10000 × ((spot_ask-spot_bid)/spot_mid + (perp_ask-perp_bid)/perp_mid)`. This assumes same future book and unchanged basis; therefore is a mathematical friction floor/sensitivity only, NOT observed future execution.
- `one_funding_predicted_gross_bps = funding_rate × 10000` for a delta-matched long spot / short perp. Negative rates cost shorts.
- `screen_8h_net_bps = one_funding_predicted_gross_bps - 30 - spread_proxy_bps`.
- `screen_24h_flat_rate_sensitivity_bps = 3 × one_funding_predicted_gross_bps -30 -spread_proxy_bps`. All 3 future rates held constant as an explicitly fictitious sensitivity, NOT a forecast, not a PnL, not live fees.
- `screen_7d_flat_rate_sensitivity_bps = 21 × one_funding_predicted_gross_bps -30 -spread_proxy_bps`, even more speculative.
- Future basis movements, funding reversals, leverage, margin, borrowing, USDT FX and timing not scored as zero costs. Report as unknown, so no `PROFITABLE` classification is possible.
- Display actual entered expected spot/perp basis (perp_bid - spot_ask)/spot_ask; not an assured convergence gain.
- Source only minimum theoretical matched base quantity and spot funding capital floor; if lot/ctVal unclear => pair blocked. No claim feasible wallet, exchange access or user's money requirements.

## Deterministic classification
For every valid pair:
  - `8H_ESTIMATE_COVERS_FROZEN_HURDLE_NOT_EDGE` iff `screen_8h_net_bps>0` — still no actual future funding, exits or fills.
  - Otherwise `8H_ESTIMATE_BELOW_FROZEN_HURDLE`.
  - 24h and 7d display **diagnostics only**, forbidden as rescue classification.
Every invalid pair: `SOURCE_BLOCKED` with exact reasons, no 0 defaults.
Total / per-asset source receipts with SHA256 and timestamp, plus outcome-blind same-day report. No real account cashflows, paper fills, trade orders or PnL.

## Abort gates for future work
If zero pairs cover 8h hurdle, stop developing bots on this 8h single-snapshot configuration. This **does not** disprove long-horizon carry generally. If any pair passes, classify ONLY source-screen interest; require new independently frozen prospective observation with actual future funding and exit BBO, basis, fee/account eligibility and adequate independent sample before considering real-money operation.

## Reference
OKX V5 docs: https://www.okx.com/docs-v5/en/
OKX fee rules (rates vary by account, region and instrument): https://www.okx.com/en-eu/help/trading-fee-rules-faq
Scientific firewall: original 2026 holdout stays protected.
