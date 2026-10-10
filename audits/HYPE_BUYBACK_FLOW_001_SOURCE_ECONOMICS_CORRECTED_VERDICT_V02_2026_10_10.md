# HYPE-BUYBACK-FLOW-001 — CORRECTED SOURCE-ECONOMICS CLOSEOUT V0.2
UTC date: 2026-10-10
Current classification: **RECENT_EXACT_AF_FILL_SOURCE_PASS / HISTORICAL_90D_SOURCE_BLOCKED / ECONOMIC_EDGE_NOT_TESTED**.
Governance-selected primary status: **SOURCE_BLOCKED** at the original 90d source gate, **NOT NO_EDGE**.
Do not describe this as 100% historical source coverage, OOS_SURVIVES, live trading feasibility or strategy profitability.
Authoritative supersession: this report corrects the *incorrect-address source interpretation* of `audits/HYPE_BUYBACK_FLOW_001_SOURCE_GATE_CLOSEOUT_2026_10_10.md` and `audits/HYPE_BUYBACK_FLOW_001_SOURCE_INTEGRITY_RECEIPT_2026_10_10.json`, which remain available as immutable prior evidence. The original closed-source conclusion was **premature due to an input bug**.

## Scientific lineage and exact runs
- Parent audit: `audits/CRYPTO_LAB_GLOBAL_NET_EDGE_VERDICTS_2026-10-09.md` at `audit/crypto-lab-net-edge-verdicts-2026-10-09`.
- Original source gate authority preregistered commit `71d4d33fe73c0a91d266ce23410d9cd63a33733d`. No user/private endpoints authorized.
- Pre-probe official fund address technical correction frozen commit `6b634e8a50bc967aedf9e716e9e263a1b6d91520`.
- Corrected exact trade source run `38042643639`, head `08165715333da50a6d5b082ea0ccfbb6d0f941fc`, first 24h 451 valid AF HYPE BUY fills; same-day 90-day-ago response empty due retention.
- Pre-source economic census frozen commit `32c66d7ae575dbd489392d2433f7dbbc27b880cb`.
- First full no-cost source census run `38042801061`, head `6aff40371e664646b5b74210889bb7f5c92bab4d`, archived evidence 5 full 24-hour slices: 5,250 fills / 123,467.42 HYPE / 10,965,550.56925 USDC; day6/7 capped at 2,000.
- Pre-source spot market context correction frozen commit `8cd95d055e63058114edd48cd8e7bd682a4252d1`. Prior context `dayNtlVlm=0` was MISMAPPED to @105 not target @107.
- Confirmatory mapping-only public run `38042924300`: `@107` pair market.index 107 vs `universe` array offset 105, contexts[107].coin exactly @107, one unique explicit match; matched public 24h HYPE/USDC spot volume 39,498,374.1664000005 USDC. Mapping raw SHA256 `565abbd779c6faf3e4cb8ca9097d841666b71a32644ecc70bfd12e3f5ae6596c`.
- Latest full corrected science run `38042996024`, head `03c96f11458e373e66d2ed336e1d8660a1284e68`, 5/5 synthetic regressions PASS. Retained archive artifact hash and ID to be attached in this document below.
- Operational clean-up: push trigger restricted to `research/hype_buyback_flow_001/*.py` and workflow itself in commit `3b85291573cc88efeaf421730d8934ea0019d6c7` to prevent documentation-only duplicate probes.
- All other historical economic closeouts untouched. `main` untouched.

## 42-character identity bug — root cause and fix
OFFICIAL AF system address must be EXACTLY `0x` + 20 repetitions of hexadecimal `fe` (42 chars).
Initial code used a 36-character address (17 repetitions) and variant code used 40 (19 repetitions), both malformed. Public API therefore responded HTTP 422. A corrected address gives 200 and hundreds of exact AF buy executions. Old SOURCE_BLOCKED receipts were real **input failures**, not evidence of absent demand. Synthetic address-length invariant now prevents repetition.
Official documentation: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees

## Source-only actual execution sample; DO NOT claim independent market-impact opportunities
Latest complete reproducible set: run `38042996024`, source checked 2026-10-10 09:53:55 UTC:
| Relative rolling 24h slice | Valid AF @107 side=B fills | HYPE sz bought | px*sz USDC executed | crossed true |
|---|---:|---:|---:|---:|
| D-1 | 451 | 12,537.74 | 1,064,938.02733 | 0 |
| D-2 | 1,285 | 33,541.98 | 2,835,125.14183 | 0 |
| D-3 | 927 | 22,104.90 | 1,948,776.01894 | 0 |
| D-4 | 907 | 19,564.46 | 1,790,604.66450 | 0 |
| D-5 | 1,658 | 35,386.78 | 3,295,271.01294 | 0 |
| **five 24h slices** | **5,228** | **123,135.86** | **10,934,714.86554** | **0** |
These slices did not individually reach the API 2000-response cap. Deduped `(tid,hash)`, validated coin, side, positive sz/px, timestamps; no malformed out-of-window rows in these slices.
CAUTION: FIVE THOUSAND fills ≠ independent statistical observations. There are multiple fills within 100 ms; HYPE buying is endogenous to protocol fee volume and closely clustered.

**Important source flag:** every verified fund fill in these five slices has `crossed=false`, and `crossed=true` count 0. In ordinary Hyperliquid fill semantics, this indicates passive/maker-side. However **automatic system fee conversions may require separate protocol-specific cross-check**, and these fields alone do not prove stable posted bids, quote queue mechanics or a known aggressor. This evidence is *in tension* with a naive aggressive market-order buyback narrative. Do not assume predictable upward price impact or front-run it.

## Free market source, exact HYPE identity and economic scale
- `spotMeta`: HYPE spot token 150 / USDC 0, coin market `@107`.
- Corrected `spotMetaAndAssetCtxs` binds by explicit `universe[].index=107` AND `assetCtxs[107].coin=@107` (not universe array position 105).
- Run `38042996024` reported contemporaneous rolling HYPE/USDC dayNtlVlm `39,517,108.5875700116` USDC.
- AF D-1 trailing 24h 1,064,938.02733 USDC / spot pair rolling day volume 39,517,108.58757 = 2.69487840936% **indicative**, NOT an exact synchronous causal ratio: the two rolling windows have different capture times and volume count definitions may differ; actual AF execution notional may be included in the same spot volume base, so not an independent explanatory factor.
- Instantaneous L2 @107 (same run): best bid 84.217, ask 84.218 USDC; spread 0.1187401668 bps, snapshot top-five total bids 20,286.22 USDC and asks 17,808.70 USDC. Snapshot cannot prove historical bid/ask at past AF trade times, liquidation/market impact or execution capacity.
- Official base lowest-volume tier spot fees: 0.070% per taker side, i.e. 14 bps roundtrip BEFORE spread/slippage/market impact, account-specific effective tier unverified. Maker posted rates 0.040% per side; maker fill and opportunity cost not guaranteed.
- Supply offset: core-contributor unlock/vesting is separate, NOT forced selling. SEC issuer 2026 filing discusses 23.8% core allocation subject to vesting. Burning is separate from transfer, execution and fee estimates. No historical sell-pressure signed evidence yet.

## Exact source gate failures
- `userFillsByTime` capped at 2000 per response and ONLY 10,000 most recent user fills retained. D-6 and D-7 day windows each returned 2000, i.e. **censored**. D-14, D-21, D-28, D-35, D-60 and D-90 each returned zero: this is **retention censoring**, NOT no historical AF buys.
- Original >=90 UTC days, >=60 active dates of complete attributed AF executions NOT MET. Public primary 90d archival route unresolved; official S3 historical data is requester-pays, **not downloaded**. No paid access.
- Point-in-time API first-availability latency at each historical fill NOT MEASURED by retrospective query; one public request RTT does not solve this.
- Contemporaneous (per-fill) execution quotes, spread, sizing and side aggressor mapping NOT VERIFIED across 90 days.
- No post-fill price returns, prediction discovery, out-of-sample, 2026 protected outcomes, strategy fees PnL or live trading was calculated.

## Decision and next legitimate action
**Scientific single next state: SOURCE_BLOCKED 90-DAY COMPLETE HISTORICAL FILLS**, with **RECENT_EXACT_BUY_FLOW_TRANSPORT_PASS**. The market-mechanism evidence is stronger than before; reject the earlier implication that the official-address API itself was unavailable.
Legitimate route: find a verified NO-COST historical exact-fill archive covering required 90d, or accumulate 90d genuinely prospective public snapshots with append-only durable first-seen receipts, future-independent holdout seal and monitoring source integrity. Existing GitHub Actions on this nondefault branch support manual/push-triggered source tests; a new durable daily schedule was NOT activated because GitHub Actions schedule triggers only on default branch and main changes are forbidden. No work falsely declared active in the background.
Only after source coverage and PIT event-order quality meet original immutable gates, commit one full economic pre-outcome freeze, then Discovery/OOS under separate authority. Never relax 90d because the latest 5d look interesting. No trading authority.
