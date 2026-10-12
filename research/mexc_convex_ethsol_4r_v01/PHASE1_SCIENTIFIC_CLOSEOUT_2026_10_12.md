# MEXC-CONVEX-ETHSOL-4R-001 — SCIENTIFIC ATTACK PHASE-1 CLOSEOUT — 2026-10-12

## Finite verified verdict
**DESIGN_FREEZE_COMMITTED / SYNTHETIC_ENGINE_CI_PASS / PUBLIC_ETH_SOL_SOURCE_CAPITAL_GATE_PASS / NO_FORWARD_ACTIVATION / ECONOMIC_4R_EDGE_NOT_TESTED / NO_LIVE_AUTHORITY.**

This is an engineering/source decision, NOT a market strategy promotion. No forward ETH/SOL 4R entries, trades or trade outcomes were scored. No current forward edge exists for this child. Parent and its negative independent cross-asset expansion remain unchanged.

## Binding science and source lineage
- Historical Parent recovered Pine V5, ETH/SOL/BNB 2021-2025 positive first basket; five-asset next basket 0/5 positive; original V0.2 2026 early losses preserved. See `research/historical-only-convex-economic-verdict-2026-10-09` and `audit/asymmetric-payoff-verdict-2026-10-09`.
- Previous Binance GitHub Actions official Futures source test HTTP451 blocked; no geographical/legal access inference.
- Existing one-shot public MEXC quote gateway of 2026-10-09 passed 4/4 source transport but 0 future scoreable signals, without durable observer; copied code retained as source lineage.
- BTC 1H `PAYOFF-FIRST-TOUCH-RETRO-001` 2026-10-12 had 18 TARGET_FIRST, 71 CENSORED among 89 observed original-entry windows. Zero economic 4:1 proof. No original history used to score new ID.

## Frozen-before-new-outcome proof
1. New branch `research/mexc-convex-eth-sol-4r-v01-2026-10-12`, forked only from `research/mexc-convex-v01-causal-gateway-2026-10-09`, no `main` mutation.
2. DESIGN_FREEZE_V0_1.md commit `b871a4dded74586a38d6da4e9592e89688ac0b5f` BEFORE all new experimental code and new quote outcome reads.
3. ENGINE_CONSTANTS_V0_1.md commit `7efed6ab4037a8421b3e714492d4bb7ba298efe0`, max quote age 2 seconds, max unobserved quote gap 30 seconds, exact high-cost fail-closed rules.
4. Offline deterministic math/first-touch model commit `bd09aaf965d9a482c16b0ab0487e59c349a2fb7f`; 16 unittest invariants committed `eef86bc7217c3522a20159cc8362a9654e9eeb85`.
5. Initial CI `38286104286` failed 1/16 ONLY because finite Decimal arithmetic differed by 1e-28 for mathematical 4R equality. Correction pre-documented `CI_DECIMAL_TEST_PRECISION_CORRECTION_2026_10_12.md` commit `afe3287f259aa65698731147ec41d3efe4c65018`, replaced ONLY a test equality assertion with 1e-24 tolerance; the economic model/formula unchanged. Original failures preserved. Final run `38286203131` CI SUCCESS 16/16 tests + compilation + explicit NO_ACTIVATION guard, head `f2c4abe3de03367a71e5905c48d1e377410b2fb7`. Latest model/probe CI also passed `38286449119`.
6. Public ETH/SOL MEXC capital SOURCE freeze `PRE_PUBLIC_CAPITAL_SOURCE_GATE_FREEZE_V0_1.md` commit `90b9b3cd9aa191257bd4c884d699191b9281979a` BEFORE executing the quote probe; probe commit `1d18bb4acb859aee1e60bac6c3b13400354e8af1`, workflow commit `d427ca8e36c47de03d741801be0518250ceb5b07`.

## One-shot public only source verdict (2026-10-12)
Canonical workflow https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38286474264 — **SUCCESS** (source diagnostics, NOT profitability).
Artifact ID `11764210387`; ZIP SHA256 `05d242febf1cf3ab9f35138212467982897998acab381f38354e9b917c0fa61f`. Artifacts include read-only source response digests, timestamps and paper 500-USDT size checks.
- MEXC ETH_USDT contract source/public book: quote age 913ms; hypothetical 1 contract, 25.0625 USDT notional and 1.0417980 USDT ideal fee-included planned stop risk.
- MEXC SOL_USDT: quote age 977ms; hypothetical 2 contracts, 21.490 USDT notional, 0.893296320 USDT ideal planned stop risk.
- Both `PUBLIC_SOURCE_HYPOTHETICAL_SIZE_PASS`, 50-USDT source book-depth scenarios passed, no source errors; PASS 2/2 at this one timestamp under the frozen size contract. Combined ideal planned stop risks `1.935094320` USDT of the hypothetical 500-USDT account, below aggregate 2.50 USDT cap.
- Present public quote/lot feasibility is not exchange order acceptance, historical/forward fill, capital jurisdiction suitability, genuine margin affordability, funding or mark-liquidation feasibility.
- No 2026 strategy future trade outcomes read, no real exchange orders, no authenticated requests.

## Prespecified fee-only payoff geometry, not actual expectancy
- Original 4% price stop, 8bps MEXC taker fee per side charged on entry/exit notionals. Planned fee-only long stop loss = 4.1568% initial notional.
- Fixed hypothetical target BID price = ENTRY_ASK times `1 + 0.168006405...` to deliver fee-only profit 16.6272% initial notional, exactly 4 times ideal 4.1568% loss. This is *not* a 4:1 achieved net with slippage/funding/mark/stop errors.
- At the frozen Oct12 public size snapshots, theoretical stop-risk budget ETH -1.041798 / SOL -0.89329632 USDT; ideal fee-only target PnL ETH +4.167192 / SOL +3.57318528 USDT. No trading PnL observed, no support for 5x/10x/20x usable leverage.
- In first-touch model: missed quote >30 seconds, bid/ask stale >2 seconds, missing mark/liquidation for leverage or conflicting mark/stop first touch => BLOCK/UNKNOWN, not winner. Historical OHLC high does NOT equal fill.
- A fixed 4R target requires testing 2026+ untouched entries, competing time exits, gap losses, funding, execution and common-equity overlap. None were scored.

## Explicit remaining blockers
- **RUNTIME**: no durable SINGLE-WRITER append-only public read-only MEXC collector running at every UTC 1h boundary with <10min signal SLA AND quote/mark observations at intervals <=30s. Github research branch push-triggered one-shot workflow is NOT a continuous scheduled runtime.
- **SIGNAL_PARITY**: exact frozen Parent 1H/RSI/Pine causality and separate child 4R / Parent comparator positional state needs validated deterministic parity and restart tests; only source gateway signal code previously existed, current new model is pure offline math/quote classifier.
- **COST**: point-in-time funding for every holding interval, actual slippage/book fill assumptions, marketable exit depth and mark liquidation/maintenance tier incomplete.
- **CAPITAL**: $500 actual tradability, account fee tier and region/access, actual stop-limit behavior and leverage tiers unverified. No account read authorized.
- **SCIENCE**: 0 eligible prospective signals and 0 resolved future paired trades. Target gate >=100 valid independent clusters, >=30 per symbol, >=12 UTC weeks, bootstrap lower bounds and all predeclared costs and robust tail tests.
- **AUTHORITY**: `ACTIVATION_FREEZE_V0_1.md` deliberately absent. No future boundary, scoring or trading implied. Source GO does not produce strategy GO.

## Next legitimate gate
Only after an isolated, no-capital, non-production, continuously durable observer exists; validated signal parity, funding/mark source and restart/dedup tests pass; commit a NEW ACTIVATE freeze with code SHA, exact future UTC boundary, custody and scoring definition BEFORE future outcomes. Prospective entries must be actual close-time causally observed. Do not alter this source/design freeze or convert current source successes into PnL.

## Capital, venues and governance
No real trades; no bots activated; no credentials, private endpoint, balances, wallets, money, account margin or Render changed. No `main` merge, no existing experiment freeze changed, no 2026 protected holdout reopened, no after-outcome optimization. CI PASS means arithmetic invariants only; SOURCE PASS means public quote availability only.
