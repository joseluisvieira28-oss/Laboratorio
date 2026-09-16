# PMD-001 — SOURCE INDEX REDUNDANCY AMENDMENT V0.2A

Date: 2026-09-16
Status: RESEARCH-ONLY / PRE-OUTCOME / SOURCE-INTEGRITY ONLY

## Reason

The exact 50-observation public-RPC probe reproduced the frozen 1,012-observation execution universe and returned pre-T0 bonding-curve-account activity for 44/50 observations, with zero provider errors and two pagination caps. No outcome was opened.

Before classifying a token as lacking pre-migration activity, PMD-001 must distinguish true absence of address-linked history from an indexing/linkage failure. A Pump trade is a Solana transaction involving the token mint and the bonding-curve accounts. Using more than one deterministic transaction index to locate the same underlying transaction does not change the economic hypothesis, decision time, population, feature cutoff, cost model, outcome, or promotion gate.

## Frozen lookup hierarchy

For every source-eligible mint, uniformly:

1. query the authoritative `bonding_curve_key` history;
2. traverse far enough to cross `T0-300s`, otherwise classify coverage as unresolved rather than zero;
3. when curve-index coverage is unresolved or returns no successful signature in `[T0-300s,T0)`, use the token `mint` as a redundant transaction index;
4. the mint-history query must be anchored before an on-chain signature at the migration boundary when an anchor is available, to avoid scanning arbitrary post-migration history;
5. take the union of recovered signatures and deduplicate by transaction signature;
6. only successful transactions with authoritative `blockTime < T0` can enter the source set;
7. full transaction payload/metadata, not index summaries, remains the scientific source of truth for later feature reconstruction.

The fallback condition is based only on source missingness/coverage and is applied uniformly. It is not conditioned on price, return, token popularity, outcome, or manual selection.

## Fail-closed rules

- A mint-index hit does not by itself prove a Pump trade; full transaction decoding must establish the Pump instruction/event before feature use.
- If neither index can establish a bounded complete source window, the observation is `SOURCE_UNRESOLVED`, not zero demand.
- No post-T0 transaction may enter a feature.
- No outcome file, return, PnL, direction label or post-migration feature may be used to decide which index to query.
- Frozen sample gates remain unchanged: total >=1,000, Validation >=200, Holdout >=200, >=20 migration dates.
- Frozen 3.00 percentage-point round-trip stress remains unchanged.
- No lowering of thresholds or rescue is authorized.

This amendment authorizes only redundant retrieval of the same pre-T0 on-chain evidence. Discovery outcomes remain sealed.
