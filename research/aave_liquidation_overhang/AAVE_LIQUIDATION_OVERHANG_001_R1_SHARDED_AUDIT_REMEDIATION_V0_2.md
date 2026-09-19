# AAVE-LIQUIDATION-OVERHANG-001 — R1 SHARDED AUDIT REMEDIATION V0.2

Date: 2026-09-19
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

The original deterministic R1 scaled-ledger audit was terminated twice solely by GitHub Actions wall-clock ceilings:

- run `35226616121`: cancelled at the explicit 45-minute workflow ceiling;
- run `35355395431`: cancelled at the explicit 120-minute workflow ceiling.

Neither run produced a canonical audit receipt. Neither run reached a reconstruction verdict. No health factor, liquidation-overhang predictor, future liquidation outcome, market return, PnL, or 2025/2026 data was opened.

Classification of both attempts: **OPERATIONAL_WALL_CLOCK_CANCELLATION / NO SCIENTIFIC VERDICT**.

## Frozen remediation

V0.2 changes only execution partitioning.

### Borrower sample recovery

The exact frozen borrower selection rule remains:

1. universe = every unique canonical `Borrow.onBehalfOf` address in the frozen source envelope;
2. digest = `keccak256(raw 20-byte borrower address)`;
3. sort ascending by `(digest,address)`;
4. select exactly the first 16 borrowers.

Instead of rescanning the full Portal envelope inside the audit monolith, V0.2 must recover that same borrower universe from the eight immutable canonical Source Census shard artifacts produced by run `35214027573`, which already covered the exact no-gap/no-overlap envelope and recorded the Borrow participant identities before any economic outcome access.

Required census evidence:
- exactly eight `SHARD_PASS` receipts;
- exact frozen shard ranges;
- aggregate unique Borrow participant count = 30,691;
- no protected-period breach.

Any mismatch fails closed.

### Reserve partition

The exact 37-reserve R0 universe remains unchanged.

Sort the 37 underlying reserve addresses lexicographically and assign each reserve deterministically by:
`sorted_index % 8 == shard_id`, for shard ids 0..7.

Each audit shard must:
- use the same recovered 16-borrower sample;
- use the same token-native Mint/Burn/BalanceTransfer rules;
- use the same Aave round-half-up ray arithmetic;
- scan the same frozen block envelope `16,490,000..21,525,890`;
- replay every touched sample-user/token pair for its assigned reserves;
- validate the exact same four frozen audit blocks:
  - 17,748,972
  - 19,007,945
  - 20,266,917
  - 21,525,890
- use the exact same five frozen historical RPC endpoints;
- require at least two usable endpoints per target;
- require exact endpoint agreement;
- require exact equality between replay and historical `scaledBalanceOf()`;
- fail on any variable-debt `BalanceTransfer`;
- fail on any negative replay state.

No borrower, token, target, block, endpoint, or failure may be dropped or replaced.

### Aggregate equivalence

The canonical V0.2 audit aggregate may emit `R1_AUDIT_PASS` only if:

- the recovered sample is exactly 16 borrowers and its deterministic SHA256 is identical across all eight shards;
- exactly eight audit shard receipts exist with ids 0..7;
- the reserve union is exactly the canonical 37-reserve R0 universe with no duplicate/missing reserve;
- every shard is `R1_AUDIT_SHARD_PASS`;
- the union of validation targets contains no duplicates;
- zero validation failure, negative replay state, or variable-debt transfer exists.

Otherwise the aggregate preserves the strongest applicable terminal class:
`RECONSTRUCTION_PROVENANCE_FAILURE`,
`RECONSTRUCTION_RECONCILIATION_FAILURE`,
`RECONSTRUCTION_INSUFFICIENT_COVERAGE`, or
`RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`.

## Downstream authorization

Only canonical `R1_AUDIT_PASS` may release the already-prepared:
- `r1_global_state_v01.py`;
- eight `r1_reserve_shard_v02.py` jobs;
- `aggregate_r1_reconstruction_v02.py`.

Only that final canonical aggregate may emit `RECONSTRUCTION_DATA_PASS`.

## Scientific invariants unchanged

V0.2 does **not** change:
- hypothesis;
- source envelope;
- sample rule;
- reserve universe;
- audit blocks;
- event semantics;
- arithmetic;
- RPC quorum;
- validation equality;
- pass/fail rules;
- eMode/config/oracle requirements;
- any future predictor, direction, horizon, cost, or promotion gate.

## Firewall

Still forbidden:
- health factor;
- liquidation-overhang predictor;
- adverse-shock selection;
- future liquidation outcome;
- market-return prices;
- returns, PnL, PF, win rate, drawdown;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation, alerts/webhooks;
- merge to main.

This is a source/reconstruction remediation only.
