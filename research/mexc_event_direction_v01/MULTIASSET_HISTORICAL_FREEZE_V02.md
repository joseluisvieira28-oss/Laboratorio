# Event Futures Multiasset Historical V0.2 — Pre-outcome fixed discovery protocol
Frozen 29 October 2026 before first directional outcome evaluation on this branch. Parent PR #280 public source run #40897851853 established five exact internal symbols and complete Min5 history on 2026-10-22/23. Strictly research-only, no trading or account access.

## Scope and symbols
Exactly BTC_USDT, ETH_USDT, NVIDIA_USDT, SPCXSTOCK_USDT, MUSTOCK_USDT. The screenshot's MLIUSDT is unresolved and is excluded; no attempted alias.
Exactly UTC 2026-10-22 00:00 through UTC 2026-10-24 00:00, 576 five-minute MEXC standard-futures INDEX OPEN bars per symbol, with EXACT full response hashes frozen below:
BTC_USDT b9d15f93fa42cfd41fc575b46b69a3727c47492fbe6d310477a100afc7632f11
ETH_USDT 73cc1abc1212bd5388a2a78a1aad7be4774c7827b86c6a4b4aaf254d4dde5835
NVIDIA_USDT 7d7dab388ffae69d78d592f938a1ba33c0eb9b236c57efb1c64d8d528e1ae4ca
SPCXSTOCK_USDT 1ca4a17ec40a3514847226f728858b47ac7c75fc79d5f424a7883fe958896b0c
MUSTOCK_USDT fcb039e436cb14c5bc55f62f778a3bcc99d223e3811d47da678cc2797615d81d
If full source hashes differ, fail closed rather than changing benchmarks or source.

## Frozen diagnostic models
1. UP_ALWAYS: predict UP at each scheduled decision.
2. DOWN_ALWAYS: predict DOWN.
3. ROC3_CONT: if INDEX OPEN(t-5m) > INDEX OPEN(t-15m), UP, if below, DOWN, if same abstain.
4. ROC3_REV: exactly reverse ROC3_CONT, abstain on equality.
These rules only use completed historical features before hypothetical decision time t. Entry proxy = INDEX OPEN(t); expiry = INDEX OPEN(t+H). Comparison => UP/DOWN/TIE; TIE 0 unit EV. Not actual executed Event Futures open price or expiry! No lookahead in directional rule, but source is post-published historical data and not point-in-time independently cached.

## Fixed horizons/time strata
H=10min and H=30min. Decisions every H (non-overlapping within each cell), exactly anchored at UTC midnight in source date (not a user-selectable favorable phase). Compare ALL_24H and US_REGULAR_PROXY strata: weekdays Oct22/23, 13:30 <= decision UTC and expiry <=20:00 UTC; this is an illustrative stock-market reference window, NOT a verified MEXC Event Futures trading eligibility schedule. All-session and regular-session results overlap and must NOT be treated as independent samples. Missing or tie-only features never imputed.

## Economic diagnostic
Report every cell (5 assets x 4 rules x 2 horizons x 2 strata = 80), with wins/losses/ties, win rate, unit EV under purely illustrative symmetric q 0.40, 0.70, 0.80, 0.85. These are NOT historical realized Event Futures pay rates; even the October 29 exact product snapshot is NOT bound to October22. Report chronological day-level splits, source counts/strata differences and cumulative total, never select best rule as a winner. No claim of certified edge or execution feasibility from 2 days/80 nonindependent tests; p-values, CI and Holm are not promotion mechanisms here. Zero economic tests are made for screenshot MLI due unresolved identity.

## Boundaries
No new September 2026 protected holdout; no selective repeat dates/assets, payout tuning, signal generation, exchange account, orders, API keys, paid source, live trading, main merge. Current product state on Oct29 ONLINE doesn't prove 22/23 product was ONLINE. Old LICP-001 NO_EDGE and Triple Flow source limitations remain untouched.
