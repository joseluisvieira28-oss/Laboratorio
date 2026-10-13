# BTC-CONVEX MULTIFRONT V0.1 — ENGINEERING / ECONOMIC HURDLE CLOSEOUT
Date: 2026-10-13, before first permitted future bar 2026-10-15 00:00 UTC.
Freeze commit: 346c6bf9355e11a284a3b974f077571f57977f88.
Branch: research/btc-convex-multifront-v01-2026-10-13.
Parent branch: btc-convex-trend-capture-001-v0.1 (Pine and freezes untouched).
PR: https://github.com/joseluisvieira28-oss/Laboratorio/pull/210 (DRAFT; not against main).

## Concrete completed deliverables
- F1: offline two-route MEXC time-stamped quote/depth validator A now / B 5min later, blocks absent/stale/undersized, no fill claims.
- F2: causal 5min paper-only BTC long rebound exit engine, +0.75% TARGET / -0.35% STOP (price), max 4h, first complete 5min start strictly after witnessed 1h close, stop-first same bar, adverse gap execution, incomplete paths OPEN_UNRESOLVED, explicit 8bps-side taker fee and 2/5bps assumed slippage, separate attested funding input.
- F3: sizing guard simulates 0.25% stop-planned account risk / 0.5% cumulative, 20% paper notional cap, including assumed fee/slip loss per quantity. This is not a true worst-case loss bound.
- F4: predeclared +6h delayed signal placebo; no forward performance evidence generated.
- Exact two-outcome ideal fee/slippage math on the fixed F2 barriers, not a forecast or observed BTC returns.
- New branch push-only synthetic QA: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38419632545 SUCCESS, **15/15** tests pass; compile and static offline/no-trading guard PASS. This validates code contracts only, not source parity, exchange execution or performance.

## F2 mathematical hurdle — NOT observed win rates
Under the model's fee 8bps each side and target/stop defined relative to the slip-adjusted entry price:
- BASE (2bps adverse exit slippage): ideal barrier winning net +0.56926612% of entry notional; losing net -0.529634056%; two-outcome break-even win probability 48.19673957%.
- STRESS (5bps adverse exit slippage): ideal barrier win +0.53906530%, loser -0.55950514%, break-even 50.93029264%.
- Includes fee on exit notional. Does NOT include funding variation, spread/impact beyond assumed slippage, price gaps, 4h TIME_EXIT or actual order fills. With time exits and gaps, the true required conditional frequency differs. Price needs to travel from market ask to a slip-adjusted target, so barriers are not implied future outcomes.
- No observed forward trade, no hit-rate measured. Therefore scalp alpha is **UNPROVEN**, not automatically plausible merely from these thresholds.

## F3 risk feasibility
For illustrative 10000 USDT equity and raw price 100, BASE modeled fees/slip, 4% stop:
- 0.25% risk budget = 25 USDT.
- Max unlevered capped position ~598.66 USDT notional / ~5.99% equity, versus historical Parent exposure 95%. Original exposure must NEVER be called safe or automatically scaled to small-account salary expectations.
- 4% stops can gap; funded futures funding/mark liquidation can exceed planned bounds.

## Frozen scientific state and operational blocker
- ALPHA: NO NEW OUTCOMES / NO_FORWARD_PROMOTION.
- F1: point-in-time consecutive venue quotes, public book depth, independently verified custody and exit-side executable prices not available in this branch. Existing one-shot MEXC source feasibility elsewhere in the repo is NOT a continuous F1 observer.
- F2: source parity to original Pine and immutable 1h signal witness receipts not proved; no validated future 5m raw input, observed future marks/funding/quotes, or continuous collector. It is a pure deterministic research implementation, NOT a live scalping bot.
- F3: planned sizing arithmetic PASS but tail and liquidation execution UNVERIFIED; no small-account 1x contract feasibility declared.
- F4: structural delayed control only, requires the same truly future event dataset. No historical score.
- Existing 2021–25 positive first ETH/SOL/BNB Parent basket, failed XRP/DOGE/ADA/LINK/AVAX expansion, weak prior 5m/15m seed PF, and H1 sticky child remain unchanged. No candidate is saved by looking at prior winners.

## Next legitimate activation steps
1. A reliable continuous *public read-only* immutable single-writer observer and exact T0 timestamped signal parity with Parent recovered Pine V5, independent 1h and 5m cadence; no cron-on-research-branch persistence claim.
2. MEXC public BTCUSDT quote/size/fair/funding source integrity for matched signals; verify fees and min/lot/order depth before executable comparison. No private account reads under this authority.
3. Pre-outcome activation custody proof and protocol/checkpoint contract; 2026-10-15 boundary is an eligibility lower bound ONLY, not an active observer.
4. At >=60 independent BTC signal clusters spanning >=12 UTC weeks, assess BASE/STRESS expectation, weekly-block lower confidence bound, year/regime and tail/stop-gap sensitivity; if signals infrequent, report INSUFFICIENT rather than change sample or rules.
5. Preserve Parent with original economics. Any later authorized actual capital action requires independent evidence and explicit new operator authorization.

**Closeout: FOUR FRONTS ENGINEERED / SYNTHETIC_CI_PASS / IDEAL_SCALP_HURDLE_QUANTIFIED / SOURCE_CUSTODY_NOT_ACTIVATED / ZERO_FORWARDED_TRADES / NO_LIVE_GO.**
No main merge, trading, private API, exchange mutation, wallets, Render, paid data, account access or 2026 protected holdout use.
