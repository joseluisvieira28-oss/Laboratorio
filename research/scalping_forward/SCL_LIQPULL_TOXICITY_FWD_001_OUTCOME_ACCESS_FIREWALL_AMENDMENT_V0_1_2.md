# SCL-LIQPULL-TOXICITY-FWD-001 — OUTCOME ACCESS FIREWALL AMENDMENT V0.1.2

Date: 2026-09-25
Status: FROZEN BEFORE ANY MARKET OUTCOME / MARKOUT ACCESS

Parent protocol commit: edd69260fe4b86cc453223df38ff0a69bde980d3
Implementation clarification commit: 5747e3ef38ab1dc490641f78d8a30a467ebfe21e

## Reason for amendment

A pre-outcome code review found that evaluator V0.1 could construct +1s/+5s/+15s markouts before determining whether the frozen minimum forward sample had been reached.

No V0.1 evaluator was run on real market data. No market markout, return, PnL, win rate, regression slope, quartile result, or economic outcome was opened.

The only real-market activity before this amendment was a public source/schema smoke:
- GitHub Actions run 36187712815;
- 30 seconds;
- raw/public Hyperliquid BTC l2Book + trades only;
- 27 raw messages;
- 0 reconnects;
- 0 parse errors;
- no derived features;
- no outcomes;
- no orders/authenticated endpoints/exchange mutation;
- artifact ID 10886333676;
- artifact ZIP SHA256 1eab30fc510de030f0bf38f9681cafa003c249149fd88f9c37ca41f0e2375c28.

That smoke is SOURCE-QA-ONLY and is explicitly excluded from the scientific MVE population.

## Canonical outcome-access rule

Evaluator V0.1 is INVALIDATED_PRE_OUTCOME and must never be used on market data.

Canonical evaluator is V0.2 or later only if it preserves this amendment.

The evaluator must:
1. parse raw books/trades;
2. construct conservative proved-fill events without any future markout;
3. compute only sample counts and distinct UTC days;
4. if any sample gate fails, stop with INSUFFICIENT_FORWARD_SAMPLE and outcome_accessed=false;
5. only after all sample gates pass may +1s/+5s/+15s markouts be computed and scientific gates evaluated.

Frozen sample gates remain unchanged:
- >=14 distinct UTC days;
- >=5,000 proved hypothetical fills globally;
- >=1,500 BUY fills;
- >=1,500 SELL fills.

No fill-level markout file may be written before those gates pass.

## New forward boundary

Scientific MVE data must be collected after the commit that freezes this amendment.
The earlier 30-second source smoke is never countable toward the MVE.

All future raw shards must carry the exact canonical post-amendment authority commit selected by the implementation lock.

## Scientific invariance

This is a contamination-prevention amendment only.
It does not change:
- mechanism;
- liquidity-pull definition;
- 1,000 ms lookback;
- top-5 depth;
- 0.001 BTC hypothetical size;
- 2,000 ms fill window;
- queue rule;
- markout horizons;
- +5s primary horizon;
- bootstrap settings;
- required signs;
- pass/fail thresholds.

No outcome existed when this amendment was frozen.
