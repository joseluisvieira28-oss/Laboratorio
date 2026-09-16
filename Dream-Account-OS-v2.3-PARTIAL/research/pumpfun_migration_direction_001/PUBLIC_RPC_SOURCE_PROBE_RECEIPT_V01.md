# PMD-001 — PUBLIC RPC SOURCE PROBE RECEIPT V0.1

Date: 2026-09-16
Status: **SOURCE_ACCESS_PROBE_PASS / FULL_POPULATION_GATE_NOT_RUN / OUTCOME-LOCKED**
Branch: `pumpfun-migration-direction-v0.1`

## Governance

Research-only. Fail-closed. No live trading. No exchange mutation. No main merge. No post-outcome tuning.

No post-migration price value, return, PnL, direction label, feature/outcome correlation, Discovery result, Validation result or Protected Holdout result was opened during this probe.

## Frozen public manifest gate

The outcome-blind manifest builder reproduced the previously established pre-feature executable ceiling exactly:

- candidate migrations: **1,012**;
- distinct migration dates: **20**;
- manifest SHA-256: `56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`;
- `outcomes_opened=false`;
- `post_price_values_projected=false`;
- `postgard_outcomes_opened=false`.

Frozen source hashes:

- `migrations.parquet`: `ef5d5141fd94acbcd121bed50e39e525cf7777d25338fc9852a67fd8a085105d`
- `tokens.parquet`: `c005d86d424013e5c78701161b025f3d8c3d472afb61466e0ad6fd5afe9e8ea6`
- `postgard_snapshots.parquet`: `34a63b8333a41b3cc84d05461febe725cf37842fa0e21d6ea00472dcdcfa1e72`

## Deterministic source-access probe

Probe target: earliest candidate in the frozen manifest.

- mint: `9af7PmWRca2QYmknQehoLH19jG5ss9ajYFpgL8dMpump`
- T0: `2026-06-23 20:14:39.303560+00:00`
- bonding-curve PDA: `6pGrN2S4ffLfsqLmNN6GZcHXZMgEMSnbE1diaALATDds`
- source-access endpoint class: standard Solana public RPC
- reconstruction window: `[T0-300s, T0)`

### Signature history

`getSignaturesForAddress` returned:

- unique signatures seen for the PDA: **436**;
- signature pages: **1**;
- history exhausted: **true**;
- null blockTime observed: **false**;
- in-window signatures: **37**.

The signature route therefore located substantial final-curve activity for this candidate.

### Direct getTransaction result

The direct transaction-body route was incomplete:

- in-window signatures: 37;
- bodies initially unavailable through direct `getTransaction`: **28**.

This was treated as source incompleteness, not as zero activity and not as an economic result.

### Authorized getBlock remediation

`SOURCE_REBUILD_AUTHORITY_V01.md` already permits `getBlock` for integrity remediation. Missing transaction bodies were grouped by their known slots and the corresponding full blocks were requested.

Results:

- fallback blocks requested: **4**;
- fallback blocks returned: **4 / 4**;
- fallback blocks missing: **0**;
- missing transaction bodies recovered from blocks: **28 / 28**;
- final missing transaction bodies: **0**;
- signature conflicts: **0**;
- final `source_complete`: **true**;
- transactions containing successful target Pump program + mint + bonding-curve PDA evidence: **8**.

Raw reconstructed transaction file SHA-256:

`43d6968528303176b65d0c7aa91adcc691ed0d51655687ad1c469f007de1be49`

## Execution evidence

GitHub Actions run: `35121711126`

Workflow conclusion: **SUCCESS**.

Pre-outcome artifact:

- artifact: `PMD-001-source-rebuild-preoutcome-v01.zip`
- artifact ID: `10457231939`
- artifact ZIP SHA-256: `a3c32689e3a7847e5c62a45b1b7489ed559c2d82c99b897f66597ac31ce3654a`
- artifact size: 4,003,405 bytes

## Scientific classification

**SOURCE_ACCESS_PROBE_PASS / FULL_POPULATION_GATE_NOT_RUN**

This probe establishes that, for one deterministic frozen candidate, final-curve bonding-curve PDA signature history is discoverable and complete transaction bodies can be reconstructed from canonical block data even when direct `getTransaction` is incomplete.

It does **not** establish:

- coverage for the remaining 1,011 candidates;
- the frozen `n>=1000` Source Gate;
- any feature formula;
- any predictive relationship;
- any economic edge.

## Authorized next step

Before full-population reconstruction, freeze and test a uniform block-first method and run an outcome-blind deterministic cross-date source-access audit spanning the 20 migration dates in the frozen 1,012-candidate manifest.

Outcomes remain locked.
