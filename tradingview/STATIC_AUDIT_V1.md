# Static Audit V1 — Institutional Flow TradingView Mirror

Audit date: 2026-09-14

## Governance checks

PASS — indicator(), not strategy().
PASS — no strategy.* calls.
PASS — no alertcondition() calls.
PASS — no webhook/exchange/order code.
PASS — no mutable research parameters exposed through inputs.
PASS — CFTC code frozen at 133741.
PASS — Legacy Futures Only preserved.
PASS — sign-only direction preserved.
PASS — 7-calendar-day hold preserved on 24/7 daily BTC bars.
PASS — 2025-only OOS display; 2026 hard masked.
PASS — separate branch; no main merge.

## External API checks

TradingView official LibraryCOT documentation confirms LibraryCOT v6 and the exported `requestCommitmentOfTraders(COTType, CFTCCode, includeOptions, metricName, metricDirection, metricType)` interface. Legacy supports `Noncommercial Positions` with Long/Short and `Open Interest` with No direction.

## Remaining runtime gate

Repository-side validation cannot run TradingView's Pine compiler or proprietary COT feed. Exact mirror acceptance therefore remains conditional on the TradingView runbook: compile unchanged, 50/50 weeks, zero mirror faults, correct first/last OOS dates, no 2026 signals.
