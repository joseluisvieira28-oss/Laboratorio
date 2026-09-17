# CRYPTO EDGE RADAR — RENDER INTEGRATION AUDIT V1

Status: **AUDIT COMPLETE / MIGRATION BOUNDARY FROZEN / NO DEPLOYMENT**  
Date: 2026-09-17  
Branch: `crypto-edge-radar-render-v0.4`  
Base: `crypto-edge-radar-aggressive-v0.3@4430f95cb257d7f7159d987aad233b4612428974`

## 1. Purpose

Integrate the tested Crypto Edge Radar with durable 24/7 hosting without damaging the existing Render collector, without changing scientific strategy rules, and without introducing exchange mutation or autonomous order execution.

This document authorizes no deployment by itself.

## 2. Existing Render service — audit snapshot

The existing `Laboratorio` Render service is healthy and should be preserved during migration.

Observed production properties:

- Docker web service in Frankfurt;
- current deployed Dream Account OS recovery commit: `4642874962744b1c65e02cdc79d09e90fa527025`;
- persistent disk: 1 GB mounted at `/var/data`;
- one running instance;
- collector cadence: approximately 60 seconds;
- recent scans observed 100% MEXC coverage across approximately 1,592 active markets;
- normalized snapshot retention bounded at 500,000 rows;
- recent runtime state remained `NO TRADE`, `paper_open=0`;
- execution architecture remains `NONEXISTENT`;
- no recent application error loop was observed during the audit window.

The GitHub `main` branch is ahead of the deployed Render commit only through research/workflow files outside the Render root directory. No Dream Account OS production code drift requiring an emergency redeploy was identified.

## 3. Critical finding — old Dream Account OS is not the new radar

The existing Render runtime is useful as a public market sensor and storage/reliability chassis, but its legacy candidate engine is not suitable as the authoritative Crypto Edge Radar strategy engine.

Reason:

- the deployed `DreamAccountEngine` builds candidates without a concrete setup and without a computed net R:R;
- legacy scoring rejects candidates when `net_rr` is absent or below 2;
- therefore persistent `NO TRADE` in that runtime must not be interpreted as evidence that all current promoted Crypto Lab strategies are continuously being evaluated and finding no signal.

The old runtime should not be modified to manufacture eligibility.

## 4. Existing Crypto Edge Radar — authoritative migration source

The migration source is the dedicated radar codebase under `crypto_edge_radar/`, not the legacy Dream Account scoring engine.

Current capabilities inherited from V0.3:

- public/read-only market feeds;
- provider firewall;
- Core5 and liquid observation universes;
- fail-closed service cycle;
- append-only SQLite evidence chain with payload and chained hashes;
- atomic status persistence;
- local JSONL notification sink;
- deterministic strategy registry and promotion gate;
- no authenticated exchange API;
- no order/cancel/amend/withdraw/transfer path;
- advisory deployment gate only;
- exact frozen `ETF-CME-INSTFLOW-001` signal trap and public CFTC current-source adapter;
- `DO_NOT_CHASE` enforcement for expired entry timestamps.

## 5. Preserve / reuse

### KEEP from the existing Render/Dream Account service

- operational lessons from the 1 GB disk incident;
- fail-closed storage headroom concept;
- bounded retention;
- persistent-disk discipline;
- health endpoint pattern;
- structured runtime logging;
- public MEXC sensor as an independent market-observation source where scientifically appropriate;
- rescue/maintenance procedures and immutable backup discipline.

### KEEP from Crypto Edge Radar V0.3

- scientific/provider firewall;
- strategy registry;
- evidence hash chain;
- public market adapters;
- fail-closed service loop;
- current deployment registry;
- ETF-CME exact signal adapter/source trap;
- aggressive deployment policy as a governance layer, not as strategy logic;
- zero autonomous execution boundary.

## 6. Quarantine / do not reuse as radar authority

The following must not drive the new radar unless separately re-authorized:

- Dream Account generic A/A+ scoring;
- legacy `CHF 56` account/risk configuration;
- legacy `normal_risk_pct=0.02` / `exceptional_risk_pct=0.03` semantics;
- generic breakout/retest scoring as a substitute for a frozen promoted strategy;
- `setup=NONE` candidate path;
- old paper/live database table names as proof of live readiness;
- Gate K execution-layer work while its numerical risk-policy authority remains unresolved;
- any Tier 4 / rejected strategy;
- any Tier 3 candidate as real-money capital signal;
- any post-hoc subgroup as a promoted strategy.

These assets remain historical/audit evidence and should not be deleted.

## 7. Delete now

**Nothing.**

The repository and existing Render database contain provenance and recovery evidence. Deleting historical code or branches would reduce auditability and provides no material runtime benefit at this stage.

The correct action is isolation and explicit authority boundaries, not destructive cleanup.

## 8. Storage architecture for Radar V0.4

The existing 500,000-row Dream Account snapshot ring is appropriate as a short operational buffer, not as a long-term research archive. At roughly 1,592 snapshots per minute it represents only about 5.2 hours of raw rows.

Radar V0.4 should persist sparse, durable evidence rather than every market row indefinitely:

- service heartbeats;
- provider/source receipts;
- strategy evaluations;
- shadow signals;
- blocker decisions;
- evidence hashes;
- source timestamps and frozen entry/exit timestamps;
- operational failures/recovery events.

Raw high-frequency market data should remain bounded or be delegated to canonical provider archives rather than filling the Render disk.

## 9. Render migration topology

### Phase A — preserve legacy production

Existing Render `Laboratorio` service remains unchanged and continues as a legacy public MEXC sensor.

### Phase B — make Radar V0.4 Render-compatible

Add, on this branch only:

1. a small HTTP runtime exposing `/health` and `/status`;
2. continuous public-shadow service loop behind that HTTP runtime;
3. Render `PORT` support;
4. explicit durable-path configuration for evidence/status/notifications when a persistent disk is present;
5. startup fail-closed checks for writable storage;
6. bounded evidence growth / retention policy;
7. CI tests for HTTP health, persistence, restart, and zero exchange mutation;
8. deployment receipt containing exact commit and configuration.

### Phase C — canary

Run V0.4 as a separate Render canary before replacing or consolidating the legacy service.

Canary success criteria:

- stable service health;
- evidence chain verifies after restart;
- no unexpected storage growth;
- provider identity remains explicit;
- exact strategy adapters remain deterministic;
- zero authenticated exchange mutation capability;
- no signal emitted from non-promoted/blocked strategies;
- no late-entry/chasing behavior.

### Phase D — consolidation decision

Only after canary PASS decide whether to:

- keep both services separated; or
- retire the legacy Dream Account runtime and move Radar V0.4 onto its persistent-disk service.

No consolidation is authorized by this audit.

## 10. Current strategy deployment boundary

At the time of this audit:

- `ETF-CME-INSTFLOW-001`: Tier 2 promoted candidate / fragile; shadow observation allowed; micro-live remains blocked until strategy-specific execution venue, instrument, fees/slippage, and defensible exposure/maximum-loss contract are frozen;
- `BNB-LAUNCHPOOL-DEMAND-001`: Tier 3 forward-shadow only;
- Tier 4/rejected candidates: blocked;
- secondary/post-hoc diagnostics: no capital authority.

The radar must display scientific state and operational blocker separately.

## 11. Absolute safety invariants

Radar V0.4 must fail CI/deployment review if any of the following appears without a separate explicit future gate:

- authenticated exchange trading credentials;
- exchange order POST/PUT/PATCH/DELETE path;
- wallet signing;
- autonomous order creation, cancellation or amendment;
- strategy auto-promotion;
- post-outcome parameter tuning;
- late-entry tolerance invented after a signal;
- provider substitution across spot/futures without frozen scientific authority;
- capital permission for Tier 3, Tier 4, blocked or post-hoc candidates.

## 12. Audit verdict

**REUSE THE EXISTING RENDER INFRASTRUCTURE CONCEPTS, NOT THE LEGACY STRATEGY ENGINE.**

**DO NOT DELETE THE OLD SERVICE. DO NOT MERGE GATE K. DO NOT DEPLOY V0.4 YET.**

The next implementation action is the Render-compatible HTTP/persistence adapter on `crypto-edge-radar-render-v0.4`, followed by CI and a separate canary deployment gate.
