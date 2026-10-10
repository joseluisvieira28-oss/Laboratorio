# HYPE-BUYBACK-FLOW-001 — PRE-SOURCE AUTHORITY V0.1
Date: 2026-10-10 UTC
Status: SOURCE-ONLY; NO OUTCOMES / NO STRATEGY FREEZE / NO TRADING AUTHORITY
Parent: audit/crypto-lab-net-edge-verdicts-2026-10-09
Scientific family: systematic protocol-fee-induced HYPE spot demand (not BTC transaction fees, ETH gas burn, funding cash carry, forced liquidations, or HIP-3 equity quotes).

## Immutable scope before first probe
- Query PUBLIC official Hyperliquid `POST https://api.hyperliquid.xyz/info` only, not account-credential endpoints.
- Fixed public SYSTEM address (Hyperliquid fees docs): `0xfefefefefefefefefefefefefefefefefe`.
- Requests: `spotMeta`; `userFillsByTime` at `[request_utc-24h,request_utc]` and `[request_utc-90d,request_utc-89d]`. One bounded page per window, `aggregateByTime:false`, no pagination that could imply completeness.
- Only classify source accessibility/schema/coverage/causality. Record public raw response SHA256, endpoint, body, UTC start/end, HTTP and request timestamps, latency, count, field quality; never compute forward returns, lead-lag correlations, direction of price changes, signal rank, profit, or trade PnL. Publish only status and source metadata.
- Validate `spotMeta` *dynamically*: HYPE token index and HYPE/USDC pair identity by token metadata (never trust a hard-coded @107 as permanent). Retain unchanged public spotMeta raw evidence for recheck.
- Accepted **real executions** require full verifiable fill fields `coin`, `side=B`, `time` (ms), positive `sz` and `px`, unique event identifier `tid` plus `hash` or independently verifiable L1 linkage, exact bind to official AF system address. Quarantine unknown asset, side, timestamp, missing ID, and ambiguous classification. No claim that any `userFillsByTime` response necessarily includes L1 internal automatic conversion.
- Sample route is NOT historical completeness: published API limits each response to 2,000 and provides only last 10,000 account fills; the absence of an old fill may mean retention rather than absence of buybacks.
- Physical/archive alternate: official Hyperliquid S3 `node_fills_by_block` (and historical `node_fills/node_trades`), `replica_cmds`, `misc_events_by_block`; requester-paid transfer EXCLUDED. Do not use S3 or AWS credentials.
- Third-party analytics (Strata Terminal; ASXN) = lead only; no source PASS until exact immutable primary receipts, capture time, backfill method, and gaps are independently auditable. Holdings deltas, issuance, token transfers, fee proxies, buybacks, L1 fee burn, and Assistance Fund-held/burned HYPE are separate event types.
- Quarantine any source observation timestamps from 2026-10-10 onward for *future* confirmatory market-return evaluation unless an independent new pre-outcome freeze is committed before future outcomes exist.
- No cloud deployment, exchange actions, wallet/account private reads, keys, fees, external purchased data, main mutation, or unsealed 2026 holdout inspection.

## Precommitted source-pass tests
All required:
1. Verified exact public AF HYPE BUY fills, not just balance/fee-rate/transfer observations.
2. Reproducible stable unique ID/clock ordering; no unbounded gaps, duplicates, timezone ambiguity, or undisclosed corrected history.
3. Continuous source authority: at least 90 UTC days of immutable causal fill records with >=60 active UTC days, plus demonstrably stable collection/recapture and no >24h unexplained missing **collector** gap.
4. Source-published/observed-at timestamps available and realistic latency bounds; cannot learn fill/event at a timestamp earlier than the indexer/API actually exposes it.
5. Source-integrity proof of correct HYPE spot market mapping and AF side (buy vs transfer).
6. Contemporaneous public depth/best quotes and HYPE trading-cost source demonstrably match the intended feasible execution venue over an independent non-contaminated window.
Until all six tests PASS, do NOT publish a market return backtest or a predictive-economic hypothesis freeze. Missing sample with an otherwise proven complete source => INSUFFICIENT_SAMPLE. Unproven access/identity/retention/timing/coverage => SOURCE_BLOCKED.

## Potential economic mechanism — not yet a tradable rule
Fees are generated endogenously by market activity; protocol can demand HYPE automatically. The market may absorb or arbitrage this impact immediately. A nonzero net after-cost lead is unproven, even if all daily buybacks are positive. HYPE supply vesting/unlocks and other risk changes can dominate flow.

## Sources + links frozen before probe
Official mechanism and address: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
Official API types and `userFillsByTime` cap: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
Official historic data / requester pays: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
Official fill & side_info structure: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/nodes/l1-data-schemas
Independent third-party (not accepted as primary): https://app.strata-terminal.com/buybacks/hype
US SEC filing (token allocation/unlocks exposure): https://www.sec.gov/Archives/edgar/data/2078856/000119312526370281/purr-20260630.htm

## Prior-science no-resurrection comparisons
- Global audit 2026-10-09: `audits/CRYPTO_LAB_GLOBAL_NET_EDGE_VERDICTS_2026-10-09.md` from parent branch.
- BTC Fee Pressure terminal Discovery FAIL NO PROMOTION: branch `btc-fee-pressure-v0.5-discovery`, `research/btc_fee_pressure/BTC_FEE_PRESSURE_001_DISCOVERY_V0_5_CLOSEOUT.md`.
- ETH Demand Fee Flow terminal REPLICATION_MIXED: branch `eth-demand-fee-flow-v0.2`, `research/eth_demand_fee_flow_001/REPLICATION_CLOSEOUT_V0.1.md`.
- Forced Flow Atlas mechanism classification: `crypto-forced-flow-atlas-001-v0.1-2026-10-05`.
- Older Hyperliquid HIP-3 source census is a different equity market topic.
- Scientific audit 2026-10-08: `audit/science-only-all-fronts-2026-10-08/audits/CRYPTO_LAB_SCIENCE_ONLY_ALL_FRONTS_ATTACK_2026-10-08.md`.

## Gate result protocol
No source pass by analogy, enthusiasm or a userFills HTTP 200 response. The eventual receipt must report EXACT output status, observed fill sample count, authenticated data use=none, trading authority=NONE, protection unchanged, run ID, commit SHA and raw-response SHA-256. Next move only after observing actual one-shot execution result.
