# MEME-004 OCTOBER 2H SUBPROTOCOL (locked before outcome replay)
Date 2026-11-18 UTC. Source structural schema/coverage seen, **no outcome study run** at lock.

**Source**: Public free 13 Oct 2026 14:00–16:00 UTC curvetape sample https://huggingface.co/datasets/launchtape/solana-launch-tape
Source SHA-256: `5ecb0e31a6b1050584594d02e6e5ce339407db4b9c6d9a8e63bbd80b53c8d93e` (76 MB gzip).
Licence permits internal research and derived results, forbids redistribution of raw data.

## Ex-ante rules
- Only tokens with `create` event seen in same source window; remove all tokens whose first signal age not in [120,2400] seconds; exclude tokens touched by global feed gaps.
- Trade print must have recorded positive `vs`, `vt` and `sol`, nonnegative `curveSol`, valid side and wallet. Missing fields remain unknown/censored.
- Events sorted by recorded `t` then slot/off/index. De-duplicate exact event IDs conservatively; do not infer ultimate wallet owner.
- Baseline candidate at first observed real-curve SOL reserve >=2 SOL.
- Filter candidate: baseline + trailing 120s >=5 distinct buyer addresses + >=1 SOL buy flow + buy/(buy+sell) >=60% + biggest buyer share <=45%. Do not select based on future outcomes.
- One signal per mint per policy. Preserve baseline and filtered counts separately.
- Entry quote at first further observed state from 30 to 180 seconds after signal, no lookahead. Exit quote at first state 300–420 seconds after entry. Missing prices/quotes or migration = censoring or blocked state, never winners.
- Nominal 0.05 SOL and fee 1.7% each leg, stress 0/2/5% slippage each leg, fixed 0.0001 SOL expenses total. These are stress assumptions, not verified historical all-in fees. Constant-product indicative quote from virtual reserve fields; a capacity gate requires virtual quotation SOL out <= real SOL reserve at exit.
- NO actual order execution, no counterfactual price path adjustment, no contention, MEV, priority/tips or guaranteed settlement.
- Output **every missing-entry/missing-exit count**, optimistic mean only among fully observed curve quote proxies, and adversarial counterfactual missing = -100% (clearly hypothetical); never report a 'trading win rate' from proxies.
- Training/test split: NOT feasible to establish independent 30-day evidence from one two-hour sample. Even if mean positive, economic NO-GO; a credible candidate requires 30 days prospectively and independent fills.

## Rationale
Earlier May-Jun source had 116 wallet-filtered candidate events and 0 quote exits, because almost no mint histories spanned five minutes. This independent October sample contains 456,540 trades, 4,416 creation records, and about 5,567 mint groups with >=5min span. It is a better structural feasibility test, not proof of forward edge. No outcome thresholds will be changed after results.
