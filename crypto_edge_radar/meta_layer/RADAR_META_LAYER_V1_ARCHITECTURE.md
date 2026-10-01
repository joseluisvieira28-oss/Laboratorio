# RADAR META-LAYER V1 — architecture and activation gate

Date: 2026-10-01
Branch: `radar-meta-layer-v01-2026-10-01`
Parent: `triple-fishing-operator-v0.3-2026-09-30`

## Purpose

Improve the information captured around the existing Radar without modifying the parent strategies. V1 is an observational recorder, not a strategy and not an execution controller.

## Current operational picture used as parent

The current triple-fishing operator package contains three execution lanes:
- BNB-LAUNCHPOOL-DEMAND-001
- OPTIONS-SPOTPERP-001-V2.1
- HTF-DH03-12H-STANDALONE-FORWARD-V1

The wider Radar lineage contains eight motors/candidates, but this branch does not infer current live state for non-triple lanes from stale registry text. Runtime state must be evidenced separately.

## Existing evidence reused

The Radar engine already persists MARKET_SNAPSHOT and STRATEGY_EVALUATION receipts. MEXC public runtime can also persist MEXC_FRICTION_SHADOW. Meta-Layer V1 should link to these sources where timestamps satisfy T0 rather than duplicate or retroactively reconstruct them.

## T0 schema

Required identity:
- candidate_id
- immutable_signal_key
- captured_at_utc
- schema_version
- idempotency_key
- payload_sha256

Context families:
- market BBO / spread / 24h quote volume when present
- realized volatility
- volume ratio
- funding
- open interest
- spot-perp basis
- BTC regime
- execution friction
- simultaneous Radar signals

Unavailable data is recorded as UNAVAILABLE_AT_T0.

## Hard separation from execution

Meta-Layer V1 cannot:
- create or suppress a signal
- change direction, threshold, entry, exit or timing
- change sizing or leverage
- change single-slot arbitration
- send an order
- mutate exchange state
- enable capital

The existing earliest-target / lexical tie-break / no-chase dispatcher remains authoritative.

## Activation gate

Before wiring the recorder into any live/shadow runtime:
1. deterministic unit tests must pass;
2. an offline synthetic integration test must prove parent dispatcher output byte-for-byte unchanged with recorder enabled vs disabled;
3. duplicate capture must be idempotent at the persistence boundary;
4. restart/replay must not fabricate a T0 snapshot after the fact;
5. runtime clock/source timestamp violations must fail closed for the recorder without blocking the parent strategy;
6. a receipt must record exact source commit and schema hash.

## Later experiments — not authorized by this V1 freeze

Regime filtering, confluence weighting, execution selection and dynamic sizing each require a separate pre-analysis freeze and prospective/OOS adjudication. No result from this recorder automatically promotes or demotes a parent strategy.
