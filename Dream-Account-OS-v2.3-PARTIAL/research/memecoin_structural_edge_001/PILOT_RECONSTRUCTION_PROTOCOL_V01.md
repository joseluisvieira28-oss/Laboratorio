# MSEL-001 — PILOT RECONSTRUCTION PROTOCOL V0.1

Status: RESEARCH-ONLY / OUTCOME-BLIND PILOT DESIGN
Branch: `memecoin-structural-edge-v0.1`
Date: 2026-09-15

## 1. Objective

Before any predictive test, prove that we can reconstruct an unbiased all-launch sample and the first five minutes of each launch with sufficiently high fidelity to support point-in-time features.

The pilot is a DATA INTEGRITY experiment, not an alpha test.

## 2. Sample size

Three-stage pilot:
- Stage A: 25 launches for manual transaction-by-transaction reconciliation.
- Stage B: 100 consecutive launches for parser/completeness testing.
- Stage C: 1,000 consecutive launches only if A and B pass.

No cherry-picking. The launches must be consecutive under a deterministic UTC/slot inclusion rule once the source window is frozen.

## 3. Source window selection

The first pilot window must satisfy all of:
- a single Pump/PumpSwap schema regime;
- a single quote-asset regime for the primary analysis (SOL only initially);
- no known program-upgrade boundary inside the window;
- sufficient provider archival coverage;
- no selection by subsequent performance.

The exact UTC interval is frozen only after `SCHEMA_REGIME_MAP_V01` is complete.

## 4. Universe inclusion

Include every qualifying Pump launch whose authoritative create transaction falls in the frozen window.

Do NOT require:
- graduation;
- minimum volume;
- minimum holders;
- later DEX listing;
- survival to any future horizon.

Failed create transactions are not launches but should be counted separately for source diagnostics if observable.

## 5. Required launch fields

Per launch:
- mint
- create signature
- create slot
- create block time
- decoded instruction variant
- user/signing payer
- creator identity
- token program
- quote mint
- bonding-curve PDA
- creation metadata fields available in the transaction/event
- source/provider receipt identifiers

## 6. T+5m event capture

Capture all successful relevant Pump-program interactions from launch timestamp through `launch_time + 300 seconds`, preserving:
- transaction signature
- slot
- block time
- transaction index/order information when available
- instruction/event type
- wallet/user
- token amount
- quote/SOL amount
- fee values if emitted/derivable
- pre/post balance deltas
- curve reserve state/event values when available

T+1m and T+3m snapshots are derived from the same immutable event stream.

## 7. Reconciliation tests

### 7.1 Create completeness
PASS only if every launch in the deterministic source window has a unique authoritative create transaction and mint.

### 7.2 Event ordering
Transactions must be strictly reproducible by `(slot, intra-slot ordering if available, signature tie-break only as documented)`.
Unknown intra-slot ordering that changes balances/feature values is a BLOCKER.

### 7.3 Reserve reconciliation
For Stage A, independently reconcile curve reserve deltas across buys/sells against decoded events/account state.
Tolerance: exact integer-unit agreement where the protocol exposes exact integer quantities; otherwise any tolerated rounding must be documented before Stage B.

### 7.4 Wallet balance reconciliation
At each snapshot, reconstructed wallet token balances must reconcile to token supply/account state after excluding protocol-owned balances under the documented rule.

### 7.5 Creator identity reconciliation
Manual audit Stage A must verify creator derivation against instruction/event semantics. Any ambiguous creator is flagged and creator-derived features are disabled for that launch.

### 7.6 Duplicate/missing transaction check
Query overlap pages/slot ranges to detect pagination gaps and duplicate signatures.
A source that silently omits relevant successful transactions fails the gate.

## 8. Quantitative PASS gate

Stage B may advance to Stage C only if:
- 100% unique create reconstruction for the sampled launches;
- >= 99.5% relevant successful transaction capture by independently checked signatures/counts, with every discrepancy explained;
- zero unexplained timestamp inversions;
- zero unexplained duplicate signatures after deduplication;
- >= 99% launches have reproducible T+5m structural snapshots;
- creator identity is either unambiguous or explicitly missing, never guessed;
- reserve/balance reconciliation errors are within the frozen exact/rounding tolerance.

Any systematic missingness correlated with activity level, token success, creator, or venue = DATA_FAILURE.

## 9. Outcome firewall

During this pilot:
- do not calculate +15m/+1h/+6h/+24h returns;
- do not calculate graduation rate for model use;
- do not label rugs/winners;
- do not inspect future price paths to decide parser fixes.

Parser fixes are based only on source correctness and transaction/account reconciliation.

## 10. Provider cross-check

Primary archival source may be Helius or another complete Solana archive, but Stage A must cross-check a subset against an independent source where feasible (official Solana RPC/explorer/raw transaction endpoint).

Provider-specific parsed labels are convenience fields, not scientific authority. Raw transaction/program semantics win conflicts.

## 11. Artifacts to produce after pilot execution

- `PILOT_WINDOW_FREEZE_V01.json`
- `SCHEMA_REGIME_MAP_V01.json`
- `PILOT_SOURCE_MANIFEST_V01.json`
- `PILOT_RECONCILIATION_REPORT_V01.md`
- immutable launch/event parquet/csv hashes
- discrepancy ledger

## 12. Stop conditions

STOP / DATA_FAILURE if:
- launch universe cannot be enumerated without survivorship selection;
- provider history has unexplained truncation;
- account/instruction versioning cannot be mapped reliably;
- T+5m balances cannot be reconstructed reproducibly;
- parser corrections require looking at future outcomes.

Only after this protocol passes may `FEATURE_DICTIONARY_V01` be materialized against actual pilot data.
