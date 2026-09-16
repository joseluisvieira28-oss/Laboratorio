# PMD-001 — SOURCE REBUILD AUTHORITY V0.1

Date: 2026-09-16
Status: **RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME / SOURCE-REBUILD AUTHORIZED**
Branch: `pumpfun-migration-direction-v0.1`

## Purpose

PMD-001 V0.1 closed its first source gate as `SOURCE_ALIGNMENT_FAILURE / INSUFFICIENT_SAMPLE` because the published raw trade shards did not provide enough final-curve trades for the already frozen post-migration executable population. No economic outcome was opened.

This document authorizes only a source replication/expansion. It does not alter the economic hypothesis, target, costs, execution window, sample gates, chronological split or promotion gates frozen in `PROTOCOL_FREEZE_V01.md` and `PREOUTCOME_SOURCE_AMENDMENT_V01.md`.

## Scientific question preserved

Can information observable strictly before a Pump.fun bonding-curve graduation predict economically tradable direction after migration to the canonical PumpSwap pool?

The economic mechanism remains fresh-demand absorption versus latent sell supply. This directional thesis may not be reversed.

## Primary chain source

Primary reconstruction source: archival Solana transaction history from an archival RPC provider, initially Helius archival RPC.

Allowed RPC methods for V0.1 source reconstruction:
- `getSignaturesForAddress` for a token-specific Pump bonding-curve PDA;
- `getTransaction` for signatures returned by the above;
- `getBlock` / `getBlockTime` only for integrity remediation or timestamp cross-checks, not as a substitute for missing token-specific history.

No exchange API and no exchange mutation is involved.

`getTransactionsForAddress` may be used only as an operational acceleration if the connected Helius plan supports it and its returned population is independently shown to be equivalent to the standard archival path. The experiment must not depend on upgrading a paid plan merely to obtain a different population.

## Why query the bonding-curve PDA

For each mint, derive the Pump bonding-curve PDA using:

`PDA = find_program_address([b"bonding-curve", mint], PUMP_PROGRAM_ID)`

with Pump program:

`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

The official Pump instruction specification binds buy/sell activity to this mint-specific bonding-curve account. Querying the PDA is therefore preferred to querying the mint itself because the bonding-curve account is specific to the pre-migration market and avoids a large amount of unrelated post-migration token history.

## Frozen reconstruction interval

For every candidate migration with authoritative `T0`:

- source reconstruction window: `[T0 - 300 seconds, T0)`;
- predictive cutoff remains strictly `< T0`;
- transactions at `T0` or later are not feature evidence;
- source collection may retain nearby rows for forensic ordering only, but any retained row timestamped `>= T0` must carry `feature_eligible=false` and may never enter predictive features.

The 300-second rebuild window is not a new outcome-informed choice. It matches the already intended final-curve microstructure family and the prior source gate's 300s coverage test.

## Completeness rule

For a mint to pass source reconstruction, the collector must paginate the bonding-curve PDA history until it has crossed below `T0-300s`, unless it proves there are no earlier signatures.

A mint is not considered complete if:
- pagination terminates on an RPC error;
- the oldest retrieved timestamp remains inside the 300s window and the provider indicates more history exists;
- transaction bodies for in-window signatures are missing;
- duplicate signatures have conflicting bodies;
- the reconstructed Pump instructions cannot be associated unambiguously with the target mint/PDA.

Missing transactions are never imputed as zero demand.

## Required raw fields

Preserve, at minimum:
- mint;
- bonding_curve_pda;
- signature;
- slot;
- blockTime;
- transaction success/error;
- full transaction message/account keys;
- full outer instructions;
- full inner instructions;
- pre/post SOL balances;
- pre/post token balances;
- log messages;
- source provider and request method;
- retrieval timestamp;
- SHA-256 of the stored raw response.

Raw source evidence must be stored separately from derived features.

## Outcome blindness

This source-rebuild stage MUST NOT read or compute:
- `postgard_outcomes.parquet`;
- post-migration price values;
- 5m return;
- PnL;
- UP/DOWN labels;
- feature/outcome correlations;
- Discovery, Validation or Holdout economic statistics.

The existing post-migration source may be referenced only through already-authorized metadata/nullness needed to define the 1,012 pre-feature executable ceiling.

## Source gate after reconstruction

Before any feature formula is frozen, the rebuild must report only coverage/integrity statistics.

Minimum gate remains unchanged:
- final eligible population >= 1,000;
- Validation count under the frozen chronological 60/20/20 split >= 200;
- Protected Holdout count >= 200;
- >= 20 distinct migration dates.

Because the already established post-execution source ceiling is 1,012, the chain rebuild must recover valid pre-T0 evidence for nearly the entire executable cohort. This difficulty is accepted; the threshold may not be lowered.

## Independent audit source

Dune Solana raw transaction/instruction tables or Google BigQuery's public Solana dataset may be used only as an independent source-integrity cross-check on a deterministic subset. They may not silently replace the primary source if their timestamp, instruction or account semantics differ.

Any disagreement between sources is a source-integrity event and fails closed until reconciled.

## Explicitly forbidden

- opening the previous 12/51 observable public-corpus cases as an economic sample;
- lowering `n>=1000`;
- changing the 300s reconstruction window after seeing coverage by outcome;
- using post-T0 transactions as features;
- using post-migration prices to choose which mints to reconstruct;
- selecting famous/successful tokens;
- imputing missing history as no activity;
- reducing the frozen 3.00 percentage-point execution stress;
- opening Discovery before source gate, exact feature formulas and partition manifest are frozen;
- live trading, exchange mutation, order placement, main merge.

## Authorized next actions

1. Build deterministic cohort manifest from the already-authorized source metadata without opening price values.
2. Derive bonding-curve PDA for each mint.
3. Collect complete archival signature history down through `T0-300s`.
4. Fetch and hash full transaction bodies for every in-window signature.
5. Run source-integrity and coverage audit only.
6. If and only if the unchanged sample gate passes, freeze exact feature formulas.

Until Step 5 passes, PMD-001 remains **OUTCOME-LOCKED**.
