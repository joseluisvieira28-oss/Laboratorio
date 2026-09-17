# BINANCE-MARGIN-BORROW-ACCESS-001 — PRE-SOURCE AUTHORITY V0.1

Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**  
Date: **2026-09-17**  
Branch: `binance-margin-borrow-access-v0.1`

## 1. Governance

Research-only. Fail-closed. No live trading, account access, authenticated exchange calls, orders, wallets, execution webhooks or merge to `main`.

Until a separately recorded source pass, forbidden:
- price/return inspection;
- basis or abnormal-return calculation;
- borrow-cost calculation;
- PnL, win rate, PF or drawdown;
- 2025/2026 data;
- event filtering based on market outcomes.

## 2. Provisional lab identity

- LAB_ID: `BINANCE-MARGIN-BORROW-ACCESS-001`
- Primary family: `ACCESS`
- Mechanism: relaxation of a short-sale/hedging constraint when an asset that is already traded on Binance Spot becomes newly borrowable on Binance Cross Margin.
- Economic counterparty: existing holders / long-biased participants facing newly enabled borrowers, short sellers and hedgers.

This lab is not a spot listing shock, perpetual listing shock, delisting shock, funding threshold or price-event study. The structural event is specifically **new borrowing/short-inventory access for an already traded asset**.

## 3. Source-stage objective

Determine whether a reproducible, point-in-time event universe can be enumerated for 2023-01-01 through 2024-12-31 from official Binance announcements without using market outcomes.

The source census must answer only:
1. can all relevant official announcement records in the frozen window be enumerated deterministically;
2. can announcement release/effective time be recovered;
3. can the exact asset(s) described as newly borrowable on **Cross Margin** be parsed;
4. can same-announcement structural confounds be classified before outcomes;
5. can independent proof establish that the asset was already Binance Spot-listed before the borrow-access event;
6. can later execution-cost provenance be obtained without retroactive/current-state substitution.

## 4. Canonical event authority

Canonical event authority = official English Binance Support announcement article.

A Binance public website/CMS endpoint may be used as **transport/index only** to enumerate article code, title and release date. It is not by itself the scientific authority. Every qualifying event must resolve to a stable official Binance Support article URL/code whose text explicitly states that an asset is a new borrowable asset on Cross Margin.

Search-engine result ordering is not an admissible event-universe definition.

## 5. Frozen event window

- start: `2023-01-01T00:00:00Z`
- end: `2024-12-31T23:59:59Z`
- 2025/2026 locked.

The census must enumerate the full available Binance announcement index far enough backward to cover the entire frozen window. It may not stop after finding a convenient number of events.

## 6. Inclusion semantics

A candidate event is structurally eligible only when the official article states that the asset is newly borrowable on **Cross Margin**.

The census must record, before any price outcome is opened:
- article code;
- official release timestamp;
- explicit effective timestamp if the article provides one, otherwise release timestamp is retained as event-information time and effective time remains unknown;
- asset symbol/name as stated;
- whether the same announcement also introduces a new Cross Margin trading pair;
- whether the same announcement also introduces Isolated Margin borrowing;
- whether the same announcement bundles Spot listing, Convert, Earn, Futures/perpetual launch or other access changes.

No event is yet accepted for Discovery merely because it appears in the source census.

## 7. Already-traded requirement

The economic hypothesis requires the asset to have been independently tradable on Binance Spot **before** margin-borrow access.

Before later Discovery authority, each candidate must have point-in-time proof of an earlier Binance Spot listing/trading start. Same-day initial listing events, or events where Spot and borrow access are inseparable, are prospectively classified as **ACCESS_CONFOUND** and cannot be silently retained.

This requirement is source-only and must be resolved before outcomes.

## 8. Borrow-cost / execution-source gate

A later executable short implementation would require historical point-in-time borrow interest and realistic evidence of borrow availability/inventory.

The known Binance historical margin-interest endpoint is authenticated `USER_DATA`; this pre-source authority does **not** authorize credentials or authenticated account calls.

Therefore this census may classify:
- event source = reproducible;
- execution cost source = credential-bound / unavailable;
without opening or requesting credentials.

No current margin-rate/current inventory endpoint may be backfilled as historical launch-time cost/availability.

## 9. Source pass criteria

`SOURCE_CENSUS_PASS` requires all of:
- deterministic enumeration route reaches through the complete 2023-2024 window;
- official article code/title/release date available for every enumerated article record;
- at least one official Cross-Margin new-borrowable event can be resolved and parsed from each calendar year 2023 and 2024;
- article identities are stable and deduplicable;
- no search-engine ranking defines the event universe;
- source receipt records zero price/return/PnL access;
- 2025/2026 firewall passes.

A pass does not authorize Discovery. It only permits a second source adjudication of event confounds, prior Spot listing and execution-cost feasibility.

Permitted classifications:
- `SOURCE_CENSUS_PASS`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `SOURCE_ENUMERATION_INCOMPLETE`
- `PROVENANCE_FAILURE`
- `INSUFFICIENT_EVENT_SAMPLE`

`NO_EDGE` is forbidden at this stage.
