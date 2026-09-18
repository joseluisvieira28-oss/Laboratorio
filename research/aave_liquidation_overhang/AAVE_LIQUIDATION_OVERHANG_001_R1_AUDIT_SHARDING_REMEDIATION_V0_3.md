# AAVE-LIQUIDATION-OVERHANG-001 — R1 AUDIT EXECUTION SHARDING REMEDIATION V0.3

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE V0.3 EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

Two executions of the exact deterministic R1 scaled-ledger audit terminated only at explicit GitHub Actions wall-clock ceilings:

- run `35226616121`: cancelled at the original 45-minute ceiling;
- run `35355395431`: cancelled at the remediated 120-minute ceiling.

Neither run emitted an audit receipt or a reconstruction/scientific verdict. Neither opened health factor, liquidation overhang, future liquidation outcomes, market returns, PnL, 2025 or 2026.

The monolithic transport shape is therefore operationally unsuitable.

## Scientific invariants

V0.3 changes execution decomposition only. It MUST preserve exactly:

- frozen source envelope: blocks `16,490,000..21,525,890`;
- frozen 37-reserve R0 bootstrap;
- borrower sample definition from R1 Execution Protocol V0.2:
  1. all unique `Borrow.onBehalfOf` identities in the frozen envelope;
  2. `keccak256(raw 20-byte address)`;
  3. sort by `(digest,address)`;
  4. first exactly 16 borrowers;
- audit blocks: `17,748,972`, `19,007,945`, `20,266,917`, `21,525,890`;
- exact token-native Mint/Burn/BalanceTransfer semantics;
- Aave round-half-up RAY arithmetic;
- exact independent archive-RPC set;
- >=2 usable RPC endpoints per target;
- exact agreement between usable endpoints;
- exact replay equality;
- variable-debt non-transferability;
- no dropping/replacing borrower, token, block or failed target.

## Reuse of canonical Source Census bytes

V0.3 MAY derive the frozen borrower universe from the already-canonical Source Census run `35214027573`, using all eight preserved `AAVE_CENSUS_SHARD_01..08` receipts.

This is not a new population definition. Those receipts were produced from the exact same frozen envelope and contain the canonical `Borrow` participant identities already counted by the Source Census closeout.

The sample selector MUST:

- require all 8 shard receipts;
- require every shard classification = `SHARD_PASS`;
- union only `participants_by_event["Borrow"]`;
- require exactly 30,691 unique borrowers;
- apply the unchanged R1 V0.2 ranking rule;
- emit the exact 16-address sample and its SHA-256 before any audit shard runs.

## Execution decomposition

After the sample is frozen, split the ordered 16-address sample into exactly four contiguous shards:

- shard 0: sample positions 0..3;
- shard 1: sample positions 4..7;
- shard 2: sample positions 8..11;
- shard 3: sample positions 12..15.

Each shard independently executes the unchanged token-native replay and exact historical `scaledBalanceOf(address)` validation for its four borrowers across all frozen audit blocks.

Parallelization MUST NOT alter event filtering semantics, RPC quorum, arithmetic or target identity.

## Canonical aggregation

A single V0.3 audit aggregate may emit `R1_AUDIT_PASS` only if:

- the sample selector passes;
- exactly four expected audit shard receipts exist;
- all four shards cover the exact disjoint 4-borrower partition;
- their union equals the frozen 16-address sample;
- every shard independently passes provenance, non-negative replay, variable-debt non-transferability and archive-RPC equality;
- all validation targets are retained;
- no safety firewall is violated.

Any shard failure preserves the strongest applicable terminal reconstruction class and blocks downstream R1.

For reproducibility, the aggregate validation target order is canonicalized as `(user, token, block)`, matching the logical order of the original monolithic replay.

## Downstream authority

Only V0.3 aggregate `R1_AUDIT_PASS` may release the already-prepared:

- `r1_global_state_v01.py`;
- eight `r1_reserve_shard_v02.py` reserve shards;
- `aggregate_r1_reconstruction_v02.py`.

Only that final canonical adjudicator may emit `RECONSTRUCTION_DATA_PASS`.

## Hard firewalls

Still forbidden:

- health factor;
- liquidation-overhang predictor;
- adverse-shock selection;
- future liquidation outcome;
- market-return prices;
- returns, PnL, PF, win rate or drawdown;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation, alerts/webhooks;
- merge to main.

This remediation changes speed/parallelization only, never scientific eligibility.
