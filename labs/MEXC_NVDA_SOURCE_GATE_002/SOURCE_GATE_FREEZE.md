# MEXC-NVDA-SOURCE-GATE-002 — SOURCE-ONLY FREEZE

Date: 2026-10-05
Base branch: research/mexc-nvda-20261005
Branch: research/mexc-nvda-source-gate-002-20261005

Research-only, fail-closed. No market-outcome retuning, no trading, no private endpoints, no account reads, no wallet actions, no exchange mutation, no merge to main.

## Purpose

Resolve the three source blockers left by MEXC_NVDA_001 before any new forward H1/H3 experiment is allowed.

## Gate A — MEXC NVDA index architecture through time

PASS only if public/official evidence is sufficient to reconstruct, for the relevant history:
1. launch anchoring/source mode;
2. effective dates of material index-source changes;
3. actual source instruments/components;
4. weights or unambiguous single-source mapping;
5. fallback/staleness/deviation rules adequate for causal timing;
6. current architecture snapshot.

PARTIAL if dated architecture regimes are proven but at least one material transition date, source mapping, weight, or NVDA-specific fallback rule remains unproven.
BLOCKED if even the broad historical source regime cannot be reconstructed.

## Gate B — defensible public/free Nasdaq NVDA reference

PASS only if a source is public/free and supplies provenance-verified NVDA observations usable for lead-lag, with timestamp semantics documented well enough to know what was available at T. Preferred:
- Nasdaq trades/BBO/tick data;
- authoritative exchange/vendor bars with explicit publication/receive semantics.

Paid, trial-only, account-entitled, provisioned, or unauthenticated-but-undocumented feeds do not pass the free/public gate.

BLOCKED if no defensible free/public source is identified.

## Gate C — NVDA share ↔ NVDAON/NVDAX economic mapping

PASS only if issuer/venue documentation supports:
- underlying identity;
- backing/exposure model;
- dividend treatment;
- split/corporate-action treatment;
- a recoverable adjustment factor/multiplier or shares-per-token series adequate to avoid raw-price-equality assumptions through time.

PARTIAL if economic mechanics are proven but historical adjustment-factor reconstruction is incomplete for one rail.

## Global rule

A forward causal experiment NASDAQ -> token/index -> MEXC is authorized only if A, B and C all PASS.
Any critical SOURCE_BLOCKED gate => SOURCE_BLOCKED_FINAL for that causal experiment; do not start a 30-day collector that cannot resolve the missing causal source.
