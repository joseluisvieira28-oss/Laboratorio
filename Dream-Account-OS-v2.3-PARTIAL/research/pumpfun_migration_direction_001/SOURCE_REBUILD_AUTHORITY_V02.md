# PMD-001 — SOURCE REBUILD AUTHORITY V0.2

Date: 2026-09-16
Status: RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME
Branch: `pumpfun-migration-direction-source-rebuild-v0.2`
Parent closeout: PMD-001 V0.1 `SOURCE_ALIGNMENT_FAILURE / INSUFFICIENT_SAMPLE`

## Purpose

V0.2 is a source replication/expansion only. It does not alter the economic mechanism, minimum sample gate, executable outcome convention, cost stress, chronological split, or promotion gates frozen in `PROTOCOL_FREEZE_V01.md`.

V0.1 failed because the selected public corpus did not contain sufficiently linked raw final-curve transactions for the intended pre-migration microstructure features. No economic outcome was opened. V0.2 is therefore authorized to rebuild the missing pre-T0 raw source from authoritative historical Solana transaction data without changing the hypothesis.

## Leakage wall

During the source rebuild:

- `postgard_outcomes.parquet` remains forbidden;
- no post-migration return, PnL, direction label, future high/low, feature/outcome correlation, Validation result, or Holdout result may be computed or inspected;
- only source identity, migration timestamps, canonical pool identity, regime flags, pre-T0 transactions, and post-source execution availability metadata already authorized by V0.1 may be used;
- predictive transaction material must satisfy timestamp `< T0`;
- raw provider responses must be persisted or hashed for auditability;
- missing observations may never be imputed as zero demand.

## Frozen population and scale authority

The V0.1 source ceiling is binding as the reference population logic: real canonical PumpSwap pool identity, non-Mayhem, exclusion of 2026-07-03, PRE-BOOST only, and frozen execution availability rules.

The V0.2 rebuild must not lower the existing sample gates:

- total eligible population >= 1,000;
- Validation >= 200;
- Protected Holdout >= 200;
- >= 20 distinct migration dates.

The previously observed V0.1 source ceiling of 1,012 is descriptive source metadata, not a license to lower any gate. If fewer than 1,000 observations can be reconstructed with valid pre-T0 raw microstructure, V0.2 fails closed.

## Authoritative source hierarchy

Primary rebuild source:

1. archival Solana transaction history returned by an RPC provider capable of complete historical retrieval for the relevant 2026 slots/time windows;
2. preferred query primitive: Helius `getTransactionsForAddress` against the token bonding-curve account, filtered to the frozen pre-T0 window, with full transaction data and cursor pagination;
3. acceptable fallback: deterministic archival Solana `getBlock`/`getTransaction` reconstruction if the provider demonstrably retains the full required history and raw responses can be audited.

Provider-derived parsed summaries may be used only as diagnostics. The scientific source of truth for feature reconstruction is the underlying Solana transaction payload / metadata.

## Probe before full backfill

Before spending credits on the full population, run an outcome-blind deterministic archival probe across a fixed set of source-eligible, non-Mayhem, non-outage migration records. The probe asks only:

- can historical transactions be retrieved for the bonding-curve account in `[T0-300s, T0)`;
- are blockTime/slot/signature/full transaction metadata returned;
- is pagination supported when required;
- can the response be hashed and preserved;
- does the source contain actual pre-T0 activity rather than a current-state substitute.

Probe success is not an economic gate and does not authorize outcomes. It authorizes only the full source backfill.

## Full source gate after probe

For every retained mint, reconstruct raw pre-T0 activity for at least the frozen backward windows required by the feature families (300s, 60s, 30s). The full source gate must report, before outcomes:

- target mints;
- mints queried successfully;
- mints with any valid pre-T0 Pump activity;
- mints with valid coverage in each 300s/60s/30s window;
- duplicate/missing/ambiguous transaction counts;
- provider/API failures;
- distinct migration dates;
- raw-response manifest hashes;
- explicit proof that no outcome file was acquired.

Only after >=1,000 observations pass the full raw-source integrity requirements may exact feature formulas be frozen.

## No-rescue rules

V0.2 may not:

- lower the >=1,000 minimum;
- cherry-pick the observable subset;
- change the decision time away from the migration boundary;
- substitute launch-time predictors for final-curve microstructure;
- use post-T0 data as predictive features;
- reduce the frozen 3.00 percentage-point round-trip stress;
- mix POST-BOOST migrations into the PRE-BOOST experiment;
- include Mayhem launches in the primary population;
- use stale wallet aggregates as point-in-time wallet behavior;
- open Discovery before the source, feature, partition, execution and promotion authorities are complete.

## Governance

Research-only. Fail-closed. No live trading. No exchange mutation. No main merge. No post-outcome tuning. No cherry-picking. No protected-holdout opening before prior gates pass.
