# MEME-DIAMANTE-004 — Reserve-constrained exit feasibility
Frozen 18 Nov 2026. **Economic NO-GO until independent prospective fills.**

## Difference from 003
003 searched for a second-wave print pattern and found 2 wallet-filtered signals, 0 observed complete exits. 004 tests whether an *earlier* pre-committed filter, based on bonding-curve reserves and buyer diversity, yields any **observable finite-size sell quotes** in the same real chain print tapes; this is NOT live edge discovery.

## Candidate ex-ante filter (exploratory, never optimized)
- Evaluate as-of ledger events, from first retained event age 120–2400s.
- Reserve threshold: at least 2 real SOL; reject source errors and unordered tx-index conflicts.
- 120s trailing flow: >=5 different buyer addresses, >=1 SOL buys, buy share >=60%, biggest buyer <=45% of SOL buys.
- Addresses are not beneficial owners; Sybil clusters can easily pass this filter.
- Baseline: first event with >=2 SOL real reserve and same age criterion, no flow gate; exactly 1 per mint.
- Fees: illustrative **1.70% each side** (including app-platform scenario), 0.0001 SOL total execution overhead and slippage stress 0,2,5% on both legs. These are NOT verified May/June 2026 venue quotes.
- Size: 0.05 SOL nominal budget.
- Entry = first observed reserve state >=30 seconds and <=180s after the signal; exit = first observed reserve state at or after 5min from entry, at most 120s late; otherwise CENSORED.
- Quotes are mathematical constant-product estimates on the virtual-reserve states. They do not prove real fill, and future market path omits our hypothetical buy impact. No winning claim from an indicative price print.
- Missing entry/exit never counted as winners; compute mean on observed proxy separately and an adversarial sensitivity in which missing exits lose 100%.
- No threshold adjustment after examining outcomes. Data are from a selected historical corpus (May–June 2026), NOT complete launch universe, not deployment, not holdout. License **PolyForm Noncommercial 1.0.0**; research only.

## Economic gate (pre-registered)
GO only if an *independent* 30+ calendar day prospective complete creation cohort yields >=200 filter-qualified **executably settled** opportunities, net expectancy positive with lower 95% block-bootstrap bound positive and beats fee-matched baselines, without optimistic missing exits; live risk and capital constraints verified. A positive historical price curve alone NEVER satisfies this.

## Safety
No keys, accounts, buys, sells, swaps, signatures, paid APIs, endpoints accepting orders or trading bot infrastructure. Read-only Github Actions fetching public permitted research sample. No automatic merge. No recurring schedule.

## References
- Official curve: https://solana.pump.fun/docs/bonding-curve
- Official fees: https://pump.fun/docs/fees
- Historical selected noncommercial source: https://huggingface.co/datasets/Tr4m0ryp/trenches-pumpfun-forward-2026-08
- Adversarial independent research: https://arxiv.org/abs/2610.39458 (follower loses OOS 32 configurations)
