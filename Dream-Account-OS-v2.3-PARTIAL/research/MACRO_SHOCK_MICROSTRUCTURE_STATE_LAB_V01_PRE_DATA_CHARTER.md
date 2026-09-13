# Macro Shock Microstructure State Lab V0.1 — Pre-Data Charter

Status: **PRE-DATA / PROVENANCE-ONLY / NO EDGE HYPOTHESIS**

## Purpose

Investigate whether scheduled U.S. macro announcements create reproducible changes in crypto execution conditions and price-discovery state that are useful for risk management or may later justify a separately frozen trading hypothesis.

This charter is intentionally **not** a directional H02 and does not authorize a trading strategy.

## Independent basis

Internal evidence from FOMC V0 and CPI/NFP V0.2 repeatedly showed abnormal event-time volume, trade-count intensity and short-horizon order-flow persistence. MSM_H01 failed to establish subsequent 15–30 minute continuation. Independent literature also supports sharp event-time changes in volatility, spreads, volume and price discovery.

Therefore the next legitimate question is about **market state and execution conditions**, not direction.

## Research domains permitted for feasibility/provenance work

1. bid-ask spread widening and recovery;
2. top-of-book and multi-level depth depletion/refill;
3. realized-volatility expansion and decay;
4. trade intensity and signed-flow intensity;
5. cross-venue price-discovery lead/lag;
6. slippage/adverse-selection proxies that can be measured without placing orders.

## Current stage — allowed

- identify public/read-only data sources;
- document field-level provenance and timestamp semantics;
- assess historical coverage and checksum/integrity support;
- estimate storage/compute requirements without inspecting target outcomes;
- design deterministic normalization and clock-alignment rules;
- create synthetic fixtures and unit tests;
- document venue-specific caveats.

## Current stage — forbidden

- defining a directional entry/exit rule;
- selecting a venue because observed outcomes look better;
- selecting CPI/NFP/FOMC because observed outcomes look better;
- choosing thresholds/windows from observed target data;
- reusing the MSM_H01 2026 holdout to generate a new edge;
- live trading;
- exchange mutation;
- merge to main;
- Render deployment.

## Data-quality gate required before any prospective hypothesis

A future hypothesis cannot be frozen until the chosen data source has documented:

- exact venue and market type;
- exact raw fields needed;
- timestamp unit and event-time alignment;
- update frequency/granularity;
- historical availability;
- gap/duplicate handling;
- checksum or equivalent integrity method;
- survivorship/symbol mapping policy;
- no look-ahead path;
- reproducible acquisition method.

## Hypothesis boundary

`H02_STATUS = NOT_AUTHORIZED`

No scientific H02 exists under this charter. A future hypothesis requires a separate prospective freeze on untouched data and must be justified without pointing to favorable 2026 MSM_H01 subgroups.

## Priority order

1. provenance feasibility for spread/depth data;
2. timestamp and cross-venue alignment feasibility;
3. synthetic implementation/tests;
4. pre-data contract review;
5. only then decide whether a prospective non-directional or trading hypothesis is scientifically justified.

Final gate: **STOP BEFORE TARGET OUTCOMES OR H02 FREEZE.**
