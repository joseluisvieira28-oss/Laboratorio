# OPTIONS-SPOTPERP-002 — CONFIRMATION / OOS AUTHORITY V0.1

Status: PROSPECTIVELY FROZEN BEFORE 2025 OOS ACCESS
Parent state: TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE under ND-PROMOTION-POLICY-V2.0-FROZEN-2026-09-14
Mode: research-only / fail-closed / no live trading / no exchange mutation / no merge to main

## Authorization boundary

This protocol explicitly authorizes 2025 market-data acquisition and one-shot OOS Confirmation for OPTIONS-SPOTPERP-002 only, after source/provenance validation passes.

2026 remains LOCKED and MUST NOT be requested, downloaded, inspected, inferred, or used to complete any 2025 outcome.

No parameter, regime, threshold, cost, horizon, option filter, signal sign, sample rule, or pass/fail rule may be changed after any 2025 outcome is opened.

## Frozen candidate

Candidate regime: UP_LOW only.
The candidate is not re-selected in OOS.

Signal construction is unchanged from the parent implementation:
- asset: BTC
- source: Deribit BTC option trades
- option DTE: 30 to 120 calendar days
- calls moneyness: strike/index_price in [1.05, 1.20]
- puts moneyness: strike/index_price in [0.80, 0.95]
- minimum distinct eligible instruments per side/day: 5
- daily signal: median(call IV by instrument) minus median(put IV by instrument)
- position: +1 if skew > 0, -1 if skew < 0, 0 if skew = 0
- outcome: BTC open-to-open log return from signal day +1 to signal day +2

Frozen regime definition:
- BTC 30-day momentum = log(open_t / open_t-30)
- trend = UP iff momentum > 0; otherwise DOWN
- BTC 30-day realized volatility = stdev of the 30 daily open-to-open log returns * sqrt(365)
- vol = LOW iff annualized realized volatility < 0.80; otherwise HIGH
- only UP_LOW observations are eligible for the Confirmation candidate

No calendar year, month, quarter, asset, option subset, alternative volatility threshold, nearby trend window, nearby DTE band, nearby moneyness band, alternative signal aggregation, or alternative holding period may be selected after OOS outcomes.

## OOS window

Confirmation market-data period: 2025-01-01 through 2025-12-31.
Evaluable signal dates: 2025-01-01 through 2025-12-29 inclusive.
2025-12-30 and 2025-12-31 signals are not evaluable because completing their outcomes would require 2026 data.

BTC prehistory needed only for regime assignment may include 2024-12-02 through 2024-12-31 and is not an OOS outcome period.

## Frozen economics

Base cost: 10 bps per entered trade.
Stress cost: 20 bps per entered trade, diagnostic only.
No cost reduction is permitted after OOS.

## Source/Data Gate before outcomes

Before any skew, regime-qualified signal, forward return, or PnL is computed, source acquisition must prove:
- 2025 Deribit option-trade acquisition complete for the authorized window;
- no Deribit request timestamp reaches 2026;
- raw page hashes recorded;
- no duplicate trade IDs after canonical de-duplication checks;
- no timestamp leakage outside the authorized window;
- required fields present and parseable for the frozen filters;
- BTCUSDT 1d source covers required 2024 prehistory plus 2025 through 2025-12-31;
- no 2026 BTC row is present;
- source manifests contain no outcome metrics.

Any source, schema, provenance, or execution-environment failure remains a non-scientific blocker and MUST NOT be classified as OOS failure.

## OOS classification

The Confirmation runner emits one of:
- OOS_REPLICATED
- OOS_FAILED
- INSUFFICIENT_SAMPLE
- SOURCE_OR_DATA_BLOCKED
- TECHNICAL_FAILURE

OOS_REPLICATED requires all of:
1. provenance/leakage/source firewalls PASS;
2. at least 80 entered UP_LOW trades in 2025;
3. OOS beta for skew -> next-day return is positive;
4. base-cost net mean > 0 bps/trade;
5. base-cost profit factor > 1.00;
6. at least 2 of the 4 calendar quarters with >= 15 entered trades have non-negative base-cost net mean;
7. no single calendar quarter contributes > 75% of total positive gross PnL when total positive gross PnL > 0.

INSUFFICIENT_SAMPLE applies if fewer than 80 entered UP_LOW trades are available after all frozen filters and source gates pass.

OOS_FAILED applies when the sample is adequate and at least one substantive OOS replication criterion 3-7 fails.

The 20 bps stress result is mandatory reporting but is not by itself an OOS_REPLICATED gate.

## Tier-1 boundary

OOS_REPLICATED does NOT automatically authorize live trading.
After OOS_REPLICATED, apply ND-PROMOTION-POLICY-V2.0-FROZEN-2026-09-14 to determine whether evidence is sufficient for TIER 1 — VALIDATED EDGE.

OOS_FAILED preserves TIER 2 history but blocks Tier-1 promotion for this tested implementation. No rescue, asset isolation, subperiod rescue, threshold change, or re-run because of an unfavorable outcome is authorized.

## Governance

- research-only
- one-shot OOS
- no tuning after outcomes
- no cherry-picking
- no 2026 access
- no live trading
- no real orders
- no exchange mutation
- no merge to main
- no deployment
- all material receipts and closeouts must be persisted in GitHub artifacts and Google Drive
