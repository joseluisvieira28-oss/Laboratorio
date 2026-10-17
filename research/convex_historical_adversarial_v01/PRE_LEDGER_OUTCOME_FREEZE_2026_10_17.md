# FREEZE — CONVEX HISTORICAL ADVERSARIAL V0.1

2026-10-17 UTC. Immutable historical-only diagnostic on **already disclosed** Binance USDM 2023–2025 parent V5 modelled trades. This is NOT untouched OOS and cannot promote economic edge or authorize live trading.

## Input identity and no-rerun rule

- **Source run 38432883246**, artifact names `CONVEX-8ALT-COMMON-3YEAR-SOLUSDT-RESEARCH` and `CONVEX-8ALT-COMMON-3YEAR-BNBUSDT-RESEARCH`, already finalized for original V5 8ALT+4TF per PR #215. Use only `1h_BASE/1h_STRESS` SOL and `4h_BASE/4h_STRESS` BNB.
- **Source run 38435206427**, artifact `CONVEX-NATIVE-5M-2023-25-SOLUSDT` as third separate SOL native 5m arm. Original closed trade CSV and summary `RESULT.json` required. If actual file naming or schema differs, classify SOURCE_SCHEMA_BLOCKED; never invent columns, missing episodes or outcomes.
- Exact 2023-01-01 through 2026-01-01 UTC, no 2026, no exchange account, no market downloads, no re-running indicator, stops or trade simulation, no post-selection of top winners. Publisher-hash source custody inherited, not independently re-fetched.
- Keep each of the three historical paper accounts separate. Never add the three portfolio returns or multiply by leverage.

## Frozen audit outputs BEFORE inspection of per-trade CSV

1. **Ledger integrity**: deterministic CSV hash, all closed rows, nonempty timestamps and finite numeric `net_pnl`, `entry_price`, `qty`, `entry_fees`, `exit_fee`, `funding`, `price_pnl`; `net_pnl = price_pnl - entry_fees - exit_fee + funding`, non-overlapping same-lane intervals (if original one-slot), count parity to canonical RESULT, period boundaries and fees sign. Ledger PnL vs source `removed_3_biggest_net_pnl_sum_usdt + sum(top3 winners)` identity where available; fail on material mismatches.
2. **Tail dependence**: top 1, top 3 and top 5 winners as fraction of total positive pnl, net closed remaining after static top-three winner removal, largest loss, winner and loser counts. This is *static trade deletion*, NOT alternative equity, re-entry or actual counterfactual.
3. **Year-by-year**: count trades, wins, closed net USD by UTC `exit_year` 2023, 2024, 2025, worst losing streak in chronological ledger, longest measured hold. This is in-sample description, not three independent OOS tests.
4. **Cost/adversarial static scenarios**: frozen **extra** ROUND TRIP bps = {0, 6, 12, 20, 40} applied per trade against original entry notional (`entry_price*qty`), subtract cash from original `net_pnl`; no changes to execution path, allocation, reinvestment, exits, entry timing or venue. Compute cash-only flat ledger and fraction of closed trades positive. Explicitly `+6bps` means *more cost*, not Kraken saving. For illustrative lower-fee comparison calculate STATIC `-6bps` only, tag `NON_EXECUTABLE_ACCOUNT_MODEL`; do not adjust historical BASE execution outcome as if venue-switched. Fee effect can be smaller than venue price basis/funding spread.
5. **Overlap / simultaneous risk**: count exact interval intersections for three named arms, max simultaneously open among these three; SOL1h/SOL5m overlaps flagged as correlated same-asset exposure. Do not claim portfolio risk/DD or summable returns without a new account simulator.
6. **BASE vs STRESS reconciliation**: frozen summaries for SOL1h and BNB4h must be two wholly reported tracks; no cherry-pick. If native5m STRESS file exists, audit it as well; otherwise flag unverified.
7. **Venue source gate**: no 2023–25 synchronized Kraken/MEXC/OKX L2/cost/funding source supplied. Documentation-only availability: OKX downloadable L2 from March 2023 https://www.okx.com/en-sg/historical-data ; Kraken derivatives public latest-trades v3 history defaults to recent 7 days (https://docs.kraken.com/api/docs/futures-api/trading/get-history); Kraken order-events historical endpoint exists but is NOT tested for 2023-25 coverage (https://docs.kraken.com/api/docs/futures-api/history/get-public-order-events). Do not infer venue liquidity, venue-account fees or native broker stop filling from generic pages.
8. **Death rules**: mathematical/ledger mismatch = SOURCE_INVALID; no costed reproducible trades = SOURCE_BLOCKED; 2023–25 returns attractive but concentrated, low sample, risk nonlatched or venue unresolved = HISTORICAL_HYPOTHESIS_ONLY; nothing in this retrospective study can output LIVE_GO, OOS_SURVIVES or money machine.

Canonical immutable baseline: original V5 no fixed TP, -4% entry position stop, +5% timeframe-close activates 12% nonlatched peak trail, taker 8bps/side, 2bps/side BASE slip, 5bps/side STRESS, funding market-open proxy, 1x/20%-equity notional separate 10k paper accounts. Different prospective tightened trail is new strategy and MUST NOT be called original V5 return.

Branch-only offline CI with `gh run download` original immutable source artifacts. Actions token scoped actions:read, contents:read, no trading secrets. No merge main or changes to installed Windows watchers, no protected 2026 holdout, no real orders/accounts/Render/deposit.

Status freeze before additional ledger computation: **FROZEN / AWAITING ARTIFACT READ**.
