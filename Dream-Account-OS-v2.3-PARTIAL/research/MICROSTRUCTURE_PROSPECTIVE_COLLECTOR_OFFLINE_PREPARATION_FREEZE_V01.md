# Microstructure Prospective Collector — Offline Preparation Freeze V0.1

Status: **FROZEN OFFLINE PRE-OBSERVATION INFRASTRUCTURE / NO TARGET OBSERVATION**  
Date: 2026-09-12  
Branch: `dream-account-phase-b-signal-research-v0.1`

## Authority

This freeze implements only the work authorized by `MICROSTRUCTURE_PROSPECTIVE_COLLECTOR_OFFLINE_PREPARATION_AUTHORITY_V01.json`.

It is additive to the already-frozen prospective collector, provenance, schema/alignment, measurement and non-directional contracts. It does not redesign them.

Scientific rule:

> CORRIGIR INFRAESTRUTURA, NÃO AJUDAR A HIPÓTESE A SOBREVIVER.

`H02_STATUS = NOT_AUTHORIZED`

## Purpose

Prepare deterministic and auditable offline infrastructure so that a later separately-authorized prospective observation can begin without implementation changes after target outcomes become available.

This stage establishes **operational readiness only**. It cannot establish edge, profitability, directional predictability, `SURVIVES`, trading readiness or H02.

## Frozen offline architecture

### 1. Session manifest

Every future capture segment is bound to a session manifest containing at minimum:

- session ID;
- canonical venue;
- symbol/product;
- channel/stream;
- exact allowlisted public market-data host;
- collector commit SHA;
- opening UTC wall-clock ns;
- opening monotonic ns;
- deterministic manifest SHA-256 fingerprint.

Only the already-authorized public paths are represented:

- Binance Spot market-data-only WebSocket: `data-stream.binance.vision`;
- Binance Spot market-data-only REST snapshot: `data-api.binance.vision` + GET depth only at runtime under separate authority;
- Coinbase Advanced public WebSocket: `advanced-trade-ws.coinbase.com`.

No generic host or URL execution path is introduced.

### 2. Immutable exact-byte segment storage

Raw source payload bytes are preserved exactly. A segment uses exclusive-create semantics and deterministic lineage:

`venue / symbol / channel / session_id / segment_id / messages/`

Each raw message has:

- contiguous zero-based ordinal;
- exact `.bin` source bytes;
- sidecar metadata JSON;
- collector wall ns;
- collector monotonic ns;
- source/exchange timestamp when present;
- sequence interval when present;
- SHA-256 of the exact bytes.

A closed segment receives:

- `SESSION_MANIFEST.json`;
- `SEGMENT_RECEIPT.json`;
- `CLOSED` digest marker.

The ordered segment fingerprint is the SHA-256 of the ordered per-message SHA-256 hex digests. Re-opening the same deterministic segment path is forbidden. Appending after close is forbidden. Post-close modification is detected by verification and fails closed.

### 3. Continuity and resynchronization state

No reconnect preserves L2 synchronization by assumption.

Frozen operational state transitions:

- reconnect -> unsynchronized;
- detected gap -> unsynchronized;
- deterministic trusted resync -> synchronized;
- no L2-derived metric may be emitted while unsynchronized.

Sequence diagnostics preserve the already-frozen venue rules:

- Binance diff depth: stale/duplicate may be ignored; overlap is allowed; `next_start > previous_end + 1` is a fail-closed gap;
- Coinbase Advanced connection envelope: exact `+1` continuity before channel/product filtering;
- Coinbase per-book sequence: strictly increasing/non-regressing, not necessarily adjacent.

### 4. Clock diagnostics

The offline layer records and diagnoses both wall-clock and monotonic receive time.

It detects deterministically:

- wall-clock regression;
- non-increasing monotonic time;
- maximum absolute change in wall-vs-monotonic elapsed-time drift.

No arbitrary clock-uncertainty threshold is invented in this freeze. Drift magnitude is descriptive until a separate cross-venue clock-uncertainty rule is prospectively authorized and frozen.

Receive-time ordering is fail-closed when wall time regresses or monotonic time is non-increasing.

### 5. Completeness receipt

The future observation completeness surface is frozen to the existing venue/symbol/channel scope:

Binance Spot, each of BTCUSDT and ETHUSDT:

- `depth@100ms`;
- `bookTicker`;
- `trade`;
- `depth_snapshot`.

Coinbase Advanced Spot, each of BTC-USD and ETH-USD:

- `l2_data`;
- `market_trades`;
- `heartbeats`.

Missing required keys remain explicit. No missing stream, symbol, venue or interval may be silently substituted.

### 6. Storage planning

Disk estimation is operational and descriptive only. It is derived from observed bytes / observed seconds and reports baseline plus 1.25x, 1.5x and 2x capacity-planning scenarios. These are storage planning sensitivities, not scientific model parameters.

### 7. Deterministic event-window extraction

The already-frozen non-directional windows are preserved exactly as half-open UTC intervals:

- prebaseline: `[-30m, 0)`;
- primary state: `[0, +30m)`;
- recovery descriptive: `[+30m, +60m)`.

Boundary extraction is deterministic and stable-sorted by timestamp, source order and source hash. No observation at an interval end is included in that interval. No directional return or PnL field is created.

### 8. Preflight gate

The offline preflight function cannot start observation. It only evaluates whether the scientific authority prerequisites are present.

Target observation remains blocked unless **both** are true:

1. complete official 2027 CPI/NFP/FOMC calendar is frozen; and
2. a separate explicit target-observation authorization exists.

Even if both become true later, the result is only `ELIGIBLE_FOR_RUNTIME_PREFLIGHT_NOT_STARTED`.

### 9. Observation receipt template

A machine-readable receipt template is prepared with status:

`TEMPLATE_NOT_EXECUTED`

It contains no fabricated counts, outcomes or classification. Infrastructure receipts and fingerprints may be attached only after real authorized collection. Scientific classification remains null under this stage.

### 10. Scientific audit chain

Each audit record can be chained by:

`SHA256(canonical_json(previous_fingerprint, current_record))`

This provides deterministic lineage and makes record ordering/parentage part of the fingerprint.

## Forbidden in this stage

- any new real market-data capture;
- target observation;
- target-outcome inspection;
- directional returns;
- PnL or hit rate;
- entries/exits/stops/targets/position sizing;
- new directional hypothesis generation simply to continue;
- H02 creation/freeze/retest/rescue;
- MEXC Sep-Dec 2025 access;
- reuse of the 2026 holdout for new hypothesis generation;
- authentication/account access;
- exchange mutation;
- live or paper orders;
- merge to main;
- Render deployment.

## Implementation gate

Before this offline preparation can be called complete:

1. synthetic unit/integration tests must pass;
2. exact-byte storage and post-close tamper detection must pass;
3. allowlist and scope rejection tests must pass;
4. sequence/gap/reconnect/resync tests must pass;
5. clock-regression diagnostics must pass;
6. half-open event-window boundary tests must pass;
7. completeness and preflight fail-closed tests must pass;
8. inherited full research suite must remain green;
9. compileall must pass;
10. existing research network/mutation AST guard must remain green.

## Stop condition

After offline implementation and CI validation:

`STOP_AT_COMPLETE_2027_OFFICIAL_CALENDAR_AND_SEPARATE_EXPLICIT_TARGET_OBSERVATION_AUTHORIZATION_GATE`

No target observation is authorized by this freeze.
