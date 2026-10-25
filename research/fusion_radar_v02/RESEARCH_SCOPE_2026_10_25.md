# Fusion Radar V0.2 — source-only three-panel research scope

Date: 2026-10-25. Branch: research/fusion-radar-three-panels-v02-2026-10-25. Main remains unchanged.

## Explicit scope
Research-only, no portfolio allocation, margin, fees optimized from old outcomes, market orders, broker/authenticated requests, or automations. The completed offline Python prototype is distributed as a ZIP in the conversation; it is not yet committed to this branch. 38/38 tests passed locally on synthetic observations and emulated public HTTP payloads. Those software tests are not market efficacy evidence.

## Existing positive primitives retained only as source research
1. BTC institutional panel: ETF-CME-INSTFLOW-001, CFTC Futures Only 133741, weekly net noncommercial positioning, 7-day horizon, info-safe report Tuesday +8 calendar days as in original TradingView mirror PR #6. Optional BTC spot 20D is newly proposed contextual state, not a transported proven alpha.
2. BNB event panel: original BNB-LAUNCHPOOL-DEMAND-001 was on BNBBTC and event 24h context. Official announcement time and receipt are mandatory. No implied long BNB position or false BNBUSDT substitution. Optional BNBBTC 20D is an exploratory context.
3. AVAX/SOL tendency panel: CED1D-0031 AVAX20 uses USD-M perpetual daily 20-day close state; SOL CONVEX 4H requires an unchanged V5 external source receipt and is a different instrument; they cannot cast combined directional votes.

## Source admission / data protection gates
- UTC explicit publication/receipt/decision clocks, no future received-at, no expired daily bars, 21 contiguous closed 1D candles, strict symbol/venue/provider and horizon binding, per-input deterministic payload digest, no duplicate family observations.
- A hash or asserted provider URL does not prove remote origin. The local package labels receipts as unverified and synthetic fixtures as synthetic.
- No claim of actual source capture in this runtime. Current session cannot resolve public Binance DNS. An optional bounded single-GET collector was implemented/tested against synthetic HTTP responses; no requests were executed against markets successfully.
- 2026 protected outcomes stay unopened, published historical results are not relabelled untouched OOS; no post-outcome selection of weights, subgroups, cost assumptions or filters.

## Economic honesty and avoid-duplication
BNB historical +80.16bps BASE; ETF 2025 +11.40bps BASE / +1.60 STRESS; CED AVAX20 +8.55bps BASE / +2.55 STRESS are published metrics in PR #141's Edge Primitive Map V0.2, not predicted returns of the fusion. CONVEX V11/V12 historical skew is not independently validated (#265). OPTIONS V2.1 forward gross 19 events negative (#175), so is not a promoted voter. 6H Donchian 2026 readiness FAIL (#21) and no resurrected Radar motors (#203). L2 standard-fee execution is economically blocked (#270).

## Definitive V0.2 status
SOFTWARE_ONLY_PASS / ECONOMIC_EDGE_NOT_TESTED / INDEPENDENT_SOURCE_ATTESTATION_PENDING / NO_PROMOTION.
To seek scientific validation, freeze a new ensemble identity, complete member universe including negatives, primary estimand and control, known-at/latency policy, uncertainty/power planning, all real fees, OOS forward start, multiplicity, and ablation tests prior to any new outcomes. No live execution authority arises from confluence.

## Existing references
- PR #141: Edge Primitive Map + survivor signature.
- PR #162: Crypto Lab V2 governance, Section 10 Ensemble Lab.
- PR #6: CFTC TradingView mirror.
- PR #203: zero active fishing.
- PR #265: CONVEX asymmetry.
- PR #270: microstructure economic closeouts.
