# CED-1D-V1 — V3 2025 CONFIRMATION EXECUTION FREEZE — 2026-09-18

**Status:** FROZEN BEFORE ANY 2025 MARKET OUTCOME  
**Execution authorization:** OWNER AUTHORIZED IN CURRENT SESSION  
**Historical verdict:** PRESERVED / RE-ADJUDICATED UNDER PROMOTION POLICY V3  
**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`

## 1. Parent authority and immutable evidence

Parent V3 boundary closeout commit:
`2927172d237d7aa188e7f191eda005d18c694545`

Canonical Phase 1 V0.2 contract SHA256:
`4a6ee27a8b6fd66dcc89e3d2b4211d3f5d5c8020c151f8908f081108803acfb4`

Canonical derived 1D Discovery fingerprint:
`b92741d682a704a237cc1ab1a4d1fb0beb13798b11993ddde9ef54bcd4f3ab20`

Canonical Phase 2 dataset fingerprint:
`0b3de834cf5a126cb348596a466ce191e956640f4e7c3d8d3fbc8f38e1c5ad93`

Historical mapped closeout ZIP SHA256:
`d590b2fe3b86baa9b9b0c1e092cf53c6cb0067ebcafb9fd7a21002dd2df50841`

The source recovery and V3 Discovery re-adjudication completed with 2025 unopened and 2026+ untouched.

## 2. Confirmation target population — immutable

Only these three historical V3 survivors may receive a 2025 Confirmation verdict:

1. `CED1D-0031` — AVAXUSDT — A_MOMENTUM — lookback 20D — CONTINUATION — horizon 1D
2. `CED1D-0241` — SOLUSDT — A_MOMENTUM — lookback 20D — CONTINUATION — horizon 1D
3. `CED1D-0251` — SOLUSDT — A_MOMENTUM — lookback 60D — CONTINUATION — horizon 1D

No other historical cell may become a candidate from this Confirmation.

## 3. Fixed confirmatory Holm family

The V0.2 contract requires every finalist plus the union of immediate predeclared grid neighbours to enter the fixed confirmatory multiplicity family.

The family is frozen as exactly eight cells:

- `CED1D-0031` — AVAX 20D / H1
- `CED1D-0033` — AVAX 20D / H3
- `CED1D-0041` — AVAX 60D / H1
- `CED1D-0241` — SOL 20D / H1
- `CED1D-0243` — SOL 20D / H3
- `CED1D-0251` — SOL 60D / H1
- `CED1D-0253` — SOL 60D / H3
- `CED1D-0261` — SOL 120D / H1

Neighbour cells exist only for frozen stability/multiplicity accounting. They cannot be promoted or substituted for the three target cells.

## 4. Signal and execution semantics — unchanged

Use the exact frozen V0.3 CED-1D mechanics:

- signal uses completed daily information through signal day D;
- entry = exact Binance USD-M 1m open at D+1 00:01 UTC;
- exit = exact Binance USD-M 1m open horizon calendar-days after entry;
- one active event per asset/config until exit;
- later qualifying signals before prior exit = `OVERLAP_BLOCKED`;
- missing exact entry/exit/path = `DATA_UNAVAILABLE`;
- CONTINUATION sign and all lookbacks/horizons remain unchanged;
- no stop, target, leverage, position resize or intrabar rule is added.

## 5. Confirmation period and temporal firewall

Independent Confirmation outcomes = calendar 2025 only.

2024 data may be opened solely as lagged warm-up input required by the frozen 120D maximum Momentum lookback.

For the candidate-only source workspace:
- AVAXUSDT and SOLUSDT 1m monthly archives: 2024-09 through 2025-12.
- 2025 official archive bytes must match the already-recovered canonical `target_registry_R1.json` provider/local SHA256 pins.
- 2024 official archive bytes must match their same canonical registry pins.

No 2026 market byte may be opened. Any event whose required exit/path crosses 2026 is `DATA_UNAVAILABLE`.

## 6. Boundary-week rule

Use the already frozen signal-completion UTC-week authority:

- UTC week = Monday 00:00 inclusive to next Monday 00:00 exclusive;
- week anchor = signal completion day;
- partial split-edge weeks stay in ledger but are inference-ineligible;
- 2025 complete-week inference begins Monday 2025-01-06;
- the last fully contained UTC week ends Monday 2025-12-29 exclusive;
- inference/sample/bootstrap/stability use only complete signal weeks;
- no row becomes `DATA_UNAVAILABLE` solely because its signal week is partial.

## 7. 2025 funding source — frozen before access

Official Binance USD-M public market-data endpoint:

`GET https://fapi.binance.com/fapi/v1/fundingRate`

Symbols:
- AVAXUSDT
- SOLUSDT

Frozen query window:
- `startTime = 1735689600000` (2025-01-01 00:00:00 UTC, inclusive)
- `endTime = 1767225599999` (2025-12-31 23:59:59.999 UTC, inclusive)
- `limit = 1000`

Pagination:
- request ascending history;
- first request uses frozen start/end above;
- if response size reaches the limit, next request starts at `last_fundingTime + 1 ms`;
- stop only when the last returned fundingTime reaches the requested end or a page contains fewer than 1000 rows;
- save every raw response page before parsing;
- no retry may change query semantics.

Required fields per funding settlement:
- `symbol`
- `fundingTime`
- `fundingRate`
- `markPrice`

Source integrity:
- exact raw page bytes are SHA256-pinned;
- normalized rows are strictly increasing by fundingTime and duplicate-free;
- fundingTime must be inside 2025;
- markPrice must be finite and >0;
- fundingRate must be finite;
- 2026 funding rows are forbidden;
- no funding interval is assumed from a fixed 8h schedule: actual settlement rows returned by Binance are authoritative because Binance funding frequency can vary.

## 8. Funding accounting — frozen before outcomes

Each event is normalized to 1.0 unit of USD notional at entry.

Position quantity:
`q = 1 / entry_price`

For every official funding settlement with:
`entry_timestamp < fundingTime < exit_timestamp`
(or fundingTime exactly at a settlement while the position is demonstrably still open), funding PnL relative to entry notional is:

`funding_pnl = -direction * fundingRate * (markPrice / entry_price)`

where:
- direction = +1 for long;
- direction = -1 for short;
- positive `funding_pnl` means funding received;
- negative means funding paid.

Funding bps:
`funding_pnl_bps = 10000 * sum(funding_pnl)`

The exact entry is 00:01 UTC and exact exit is 00:01 UTC, therefore an official 00:00 settlement immediately before entry is excluded and a 00:00 settlement one minute before exit is included.

No fixed number of settlements per trade is assumed.

## 9. Confirmation execution-cost contract

The frozen V0.2 Confirmation nonfunding floors apply:

- BASE nonfunding floor = **14 bps round-trip**
- STRESS nonfunding floor = **20 bps round-trip**

Primary funded economics:

`BASE_FUNDED_NET_BPS = gross_bps - 14 + funding_pnl_bps`

`STRESS_FUNDED_NET_BPS = gross_bps - 20 + funding_pnl_bps`

The historical 10 bps Discovery band may be reported only for comparability. It is not the 2025 Confirmation base.

No cost may be lowered after outcomes.

## 10. Sample adequacy — stricter V0.2 Confirmation floors

Per cell, inference-eligible Confirmation requires:

- min events = 300
- min active days = 120
- min complete signal-week clusters = 39
- min active months = 9

Insufficient sample remains `INSUFFICIENT_SAMPLE`, not NO_EDGE.

## 11. Strict V0.2 Confirmation statistical gate

For each of the eight fixed family cells calculate funded BASE statistics using the frozen weekly block-bootstrap arithmetic and seed 20260908.

A target receives `V02_CONFIRMATION_PASS` only if all applicable frozen V0.2 conditions hold:

- sample gates PASS;
- mean BASE funded net > 2 bps/event;
- uncentered 95% bootstrap lower CI > 0;
- Holm FWER adjusted p <= 0.05 across the exact fixed eight-cell family;
- STRESS funded mean >= 0;
- temporal/stability/concentration gates PASS;
- complete lineage and ledger;
- funding source/provenance PASS.

Bootstrap null remains mean funded BASE net <= 2 bps.

No p-value threshold is relaxed after outcomes.

## 12. Confirmation stability and concentration

Use funded BASE net for:

- positive active-month fraction >= 2/3;
- positive quarters >= 3;
- immediate-neighbour support under the frozen grid rule;
- max single-month share absolute PnL <= 0.30;
- max top-5 event share absolute PnL <= 0.20;
- max single-day share absolute PnL <= 0.10;
- leave-one-month-out aggregate funded BASE mean >0 for Confirmation.

All failures are reported; no month/event deletion is allowed.

## 13. V3 promotion routing after Confirmation

Historical V1/V2 verdicts remain immutable.

After the strict Confirmation output:

- A target that passes the stricter V0.2 Confirmation gate and the V3 universal hard eligibility may be re-adjudicated to **Tier 2 — PROMOTED CANDIDATE / QUASE DIAMANTE**.
- A target with useful positive independent evidence but unresolved execution feasibility or another hard eligibility item remains **Tier 3 — WATCHLIST**.
- An adequate independent 2025 block that materially destroys the exact target under realistic BASE funded economics may support **Tier 4 — REJECTED**.
- Source/provenance/sample failure remains outside tiers.

Reference-price Confirmation alone cannot claim live executability. Execution-feasibility evidence remains a separate hard gate if unresolved after 2025 economics.

## 14. Prohibitions

- no 2026+
- no live trading
- no exchange mutation
- no orders
- no wallets
- no leverage optimization
- no alerts/webhooks
- no parameter rescue
- no direction flip
- no asset/month selection
- no cost reduction
- no new grid values
- no merge to main

## 15. Authorized next actions

1. execute 2025 source/provenance gate for the frozen AVAX/SOL kline workspace and Binance funding history;
2. pin all 2025 source bytes before opening economic outputs;
3. build and test the one-shot Confirmation runner against synthetic fixtures only;
4. freeze implementation hashes;
5. execute the exact 2025 Confirmation once;
6. adjudicate all three targets under the frozen rules above.