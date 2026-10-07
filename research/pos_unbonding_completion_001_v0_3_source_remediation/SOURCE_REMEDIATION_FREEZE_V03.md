# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — SOURCE REMEDIATION FREEZE V0.3

Date: 2026-10-07
Branch: pos-unbonding-completion-001-source-remediation-v0.3-2026-10-07
Base main: f263c6c6f3a57f26666a7aee28e782f2cbd08418
Immutable prior verdicts:
- V0.1 SOURCE_HISTORICAL_COVERAGE_BLOCKED @ 92f106cc
- V0.2 SOURCE_HISTORICAL_COVERAGE_BLOCKED @ f0cf559a33afcc6252dba5247714d7b836c77ed7

## Purpose

Test genuinely new source capability identified after V0.2: historical reconstruction without provider-side tx_search by scanning raw CometBFT blocks and decoding TxRaw protobuf messages, then reconciling against block_results / finalize-block events.

No market outcomes may be opened in this remediation.

## Frozen source interval

2023-01-01 through 2024-12-31 only for chain-event reconstruction.

2025 and 2026 chain/market outcomes remain closed unless a later separately committed authority explicitly opens a source-only extension. No current/latest chain state requests.

## Frozen reconstruction path

For each candidate chain:

1. Fetch a fixed historical block H from a public/free archive source.
2. Read block.data.txs[] raw base64 transactions.
3. SHA256 the decoded TxRaw bytes to derive tx hash.
4. Decode cosmos.tx.v1beta1.TxRaw -> TxBody.messages.
5. Identify /cosmos.staking.v1beta1.MsgUndelegate and record delegator, validator, amount, denom and block timestamp.
6. Fetch the same historical height's block_results/finalize-block result.
7. Record staking events needed to prove scheduled unbonding and actual complete_unbonding.
8. Decode MsgCancelUnbondingDelegation and MsgBeginRedelegate from raw transactions where supported by the chain/version.
9. Reconcile slash/validator/hold effects using chain-version-pinned x/staking semantics and available historical event/state evidence.
10. Reconcile Source A raw reconstruction against Source B from an independently operated archive/indexer/dataset.

Provider-side tx_search is not required and must not be treated as a blocker if raw-block reconstruction succeeds.

## Candidate order

Primary capability candidates:
- Cosmos Hub
- Osmosis
- Kava
- dYdX Chain
- Injective

Secondary only if one primary fails:
- Akash
- Secret

Celestia remains excluded unless consensus-event coverage equivalent to complete_unbonding is proven.

## Comparability rule

A chain qualifies only if production behavior is pinned to native Cosmos SDK x/staking semantics sufficiently comparable to the frozen lifecycle:
MsgUndelegate -> unbonding entry -> cancellation/slashing/holds as applicable -> actual EndBlock/finalize-block release.

Manual withdrawal, epoch-reset, liquid-receipt or incompatible regimes are excluded.

## Independent provenance

A qualifying chain requires:
- Source A: raw blocks plus block_results/finalize-block from a free/public historical archive; and
- Source B: an independently operated historical archive/indexer/dataset OR independently reconstructed second path.

Agreement targets frozen before any market outcomes:
- MsgUndelegate count: >=99.9%
- principal amount: >=99.99%
- delegator/validator identity: exact
- completion status: exact for matched entries
- completion block/time: same canonical block, or documented +/-1 block representation difference only

Unexplained pruning, pagination gaps or operator dependence blocks the chain.

## Gate thresholds

Unchanged parent gates:
- >=5 mechanically comparable qualifying chains;
- >=40 independently defensible material event clusters/source units TOTAL across those >=5 chains, NOT 40 per chain;
- source-only materiality using on-chain supply/staking state;
- >=12 consecutive months of pre-2026 liquid-market source capability for each selected instrument, without opening price/volume values.

Do not freeze a 0.1% circulating-supply threshold merely because an external challenger suggested it. Materiality must be established from source-only feasibility before outcomes and documented in this branch before counting the gate.

## Allowed work

- bounded fixed-height archive probes;
- raw-block protobuf decoding;
- chain-version source inspection;
- historical event/state reconstruction;
- source-only counts and source-only materiality after reconstruction capability is proven;
- market archive metadata/provenance checks without opening values.

## Forbidden

- market prices, returns, PnL or post-event market outcomes;
- live/current chain state;
- paid endpoints, API keys, accounts, wallets;
- orders/exchange mutation;
- lowering >=5 / >=40 gates;
- replacing mechanism after seeing market outcomes;
- merge to main.

## V0.3 verdict vocabulary

- SOURCE_GATE_PASS
- SOURCE_HISTORICAL_COVERAGE_BLOCKED
- INSUFFICIENT_INDEPENDENT_SAMPLE
- MECHANISM_NOT_COMPARABLE

If SOURCE_GATE_PASS: stop and create a new separate PRE-OUTCOME ANALYSIS FREEZE before any market values.
