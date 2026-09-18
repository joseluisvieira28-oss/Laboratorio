# CRYPTO EDGE RADAR V0.3

Status: **PUBLIC SHADOW / PROMOTED-MOTOR INFRASTRUCTURE ONLY**  
Development branch: `crypto-edge-radar-v0.1`  
Draft PR: `#22`  
Live trading: **FORBIDDEN**  
Authenticated exchange APIs: **FORBIDDEN**  
Order creation / cancellation / mutation: **NOT IMPLEMENTED**

## Purpose

Run a strategy-agnostic public-data radar that may host only research candidates with explicit upstream promotion/shadow authority.

The radar does not discover edges, tune strategies, rescue rejected candidates, auto-promote strategies, or authorize capital.

## V0.3 promoted motor state

The current canonical motor manifest is:

`PROMOTED_MOTOR_MANIFEST_V0.3.json`

Current V3 Tier-2 set reconciled for Radar:

1. **CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1**
   - Tier 2 / Quase Diamante.
   - Prospective public-data shadow activation authorized.
   - First eligible signal completion: `2026-09-19T00:00:00Z`.
   - Native Radar V0.3 adapter: **ACTIVE only on Binance USD-M public provider**.
   - Exact symbol/provider binding; Spot substitution forbidden.
   - Late backfill after the 00:01 reference entry is forbidden.
   - Immutable signal key deduplication prevents repeat notifications.

2. **BNB-LAUNCHPOOL-DEMAND-001**
   - Tier 2 / Quase Diamante.
   - Existing forward watcher retained.
   - Radar native adapter: **not yet loaded**.
   - Requires a dedicated event/provenance bridge; a snapshot-only adapter would be scientifically invalid.

3. **ETF-CME-INSTFLOW-001**
   - Tier 2 / promoted candidate.
   - Existing forward shadow active.
   - Radar native adapter: **not yet loaded**.
   - Requires provenance-preserving ETF/CME/CFTC input bridge.

4. **HTF-DONCHIAN DH-02-HO1 6H**
   - Tier 2 / Quase Diamante.
   - Shadow preflight ready.
   - Protected 2026 access remains locked under its own candidate authority.
   - Radar adapter must remain blocked until a separate candidate-specific authority opens that access.

Rejected/Tier-4 candidates are not loadable into the promoted registry.

## AVAX20 native adapter

Research identity is preserved exactly:

- market: Binance USD-M AVAXUSDT perpetual
- lookback: 20 calendar days
- signal: `ln(close_D / close_D-20)`
- direction: CONTINUATION
- signal completion: UTC day boundary
- reference entry: +1 minute
- reference exit: +1 calendar day
- first eligible completion: 2026-09-19 00:00 UTC
- no stops/targets/regime filter added
- no late signal backfill
- no real order path

The adapter reads only allowlisted public USD-M daily klines and filters out incomplete candles. A directional signal is valid only inside the one-minute interval between frozen signal completion and frozen reference entry.

## Signal deduplication

Every promoted directional adapter must provide an immutable `metadata.signal_key`.

New signals are written once to the append-only evidence chain as:

`VALID_SHADOW_SIGNAL`

If a later service cycle sees the same signal key, the decision is retained for audit but notification/emission is suppressed. A process restart therefore cannot spam the same shadow signal.

## Provider firewall

Default research/runtime provider: Binance USD-M public market data.

GitHub-hosted runners may receive HTTP 451 from `fapi.binance.com`. The CI public soak therefore continues to use Binance's official market-data-only Spot endpoint **for infrastructure validation only**.

Spot does not load the AVAX20 adapter, cannot produce AVAX20 signals, and is never treated as futures-equivalent.

## Current capability

- Explicit public provider identity on all market/evaluation/health records.
- Core5 observation universe plus exact promoted-strategy symbols when their adapter is loaded.
- Optional broader liquid universe.
- Provider-bound promoted strategy registry.
- Native AVAX20 Tier-2 shadow adapter.
- Immutable signal-key deduplication.
- SQLite SHA-256 evidence chain.
- Atomic JSON health/status file.
- Local JSONL informational notification sink.
- Heartbeat-enabled service loop.
- Bounded CI soak.
- No dashboard, webhooks, API keys, balances, positions, orders, cancels, amendments or exchange mutation.

## Scientific firewall

```text
RESEARCH LAB / PROMOTION POLICY
          |
          | explicit candidate-specific shadow authority
          v
PROMOTED MOTOR MANIFEST
          |
          | exact provider + exact identity
          v
STRATEGY ADAPTER REGISTRY
          |
          | PROMOTED_SHADOW only
          v
PUBLIC READ-ONLY RADAR
          |
          +--> deterministic signal
          +--> immutable signal_key
          +--> append-only evidence
          +--> local informational notification
          |
          X  no order/account/wallet path
```

## Run locally

Requires Python 3.11+ and no third-party runtime packages.

```bash
cd crypto_edge_radar
python -m radar once
python -m radar service --interval 30
python -m radar status
python -m radar verify-evidence
```

Default USD-M mode loads compatible promoted native adapters. The Spot validation provider loads none.

## Governance

V0.3 does **not** authorize:

- live trading
- authenticated exchange APIs
- account API keys
- wallets
- leverage
- order creation or cancellation
- exchange mutation
- external execution webhooks
- production capital
- automatic Tier-1 promotion
- merge to main

The Radar is an evidence and signal-observation surface only.
