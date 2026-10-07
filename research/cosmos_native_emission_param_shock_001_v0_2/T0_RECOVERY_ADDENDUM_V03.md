# COSMOS-NATIVE-EMISSION-PARAM-SHOCK-001 — T0 Recovery Addendum V0.3

Date: 2026-10-07  
Branch: `cosmos-native-emission-param-shock-001-v0.2-t0-remediation-2026-10-07`

## Scope

This addendum preserves the V0.1 pre-outcome freeze and V0.2 T0 source-remediation freeze. It does not open market prices, returns, OHLC, volumes, 2026 outcomes, Development, trading, account data, wallets, or private endpoints.

It certifies two previously unresolved Akash governance execution boundaries using deterministic, version-pinned ABCI semantics plus immutable block timestamps/hashes and the already persisted on-chain governance receipts.

No event substitution, outcome inspection, or post-outcome tuning occurred.

## Deterministic execution rule

The Akash node versions bracketing both relevant periods use Cosmos SDK v0.45.16 semantics for the relevant governance and mint modules:

- Akash `v0.36.2` / `v0.36.3-rc2`: `github.com/cosmos/cosmos-sdk v0.45.16`.
- Akash `v0.38.0`: `github.com/cosmos/cosmos-sdk v0.45.16`, replaced by `github.com/akash-network/cosmos-sdk v0.45.16-akash.3`.
- The Akash fork preserves the relevant `x/gov/abci.go` and `x/mint/abci.go` semantics.

In SDK v0.45.16:

1. `x/gov.EndBlocker` iterates active proposals whose voting periods have ended using the current block header time.
2. If a proposal passes, its handler executes during that block's EndBlock and successful state mutation is written.
3. `x/mint.BeginBlocker` runs at the beginning of a block, fetches the stored minter and mint params, recalculates inflation, annual provisions and block provision, and mints under those params.

Therefore, for a passed `ParameterChangeProposal` whose voting end lies strictly after block H-1 and at/before block H:

- BeginBlock(H) necessarily used the old mint parameters.
- Gov EndBlock(H) executes and commits the passed parameter change.
- BeginBlock(H+1) is the first mint BeginBlock that can read and apply the new parameters.

Thus the canonical first-reduced-mint T0 is H+1.

## AKT Proposal 265 — CERTIFIED

Persisted governance receipt:

- Proposal ID: 265.
- Type: `/cosmos.params.v1beta1.ParameterChangeProposal`.
- Status: `PROPOSAL_STATUS_PASSED`.
- Voting end: `2024-08-08T16:13:48.243802688Z`.
- Mint changes:
  - `InflationMin`: 13% -> 8%.
  - `InflationMax`: 20% -> 13%.

Canonical block-time bracket recovered from the source-only Akash block index:

- H-1 = block **17,526,665**
  - time: `2024-08-08T16:13:46.576Z`
  - hash: `01FB1EA6B5C987C6F5B50D608125E28C99FC9E0695943FFF6A7B128CDF4CF983`
- H = block **17,526,666**
  - time: `2024-08-08T16:13:52.420Z`
  - hash: `6FB3831566CB2E836C246F27DF0C9744374E8251566D1F9FC3E07172E9FFE3D7`
- voting end lies strictly between H-1 and H.
- H+1 = block **17,526,667**
  - time: `2024-08-08T16:13:58.676Z`
  - hash: `927E2BCC0033B18F2AC13C44D4DE54783F1B519596C8B43F9FC0A6D01486F2DD`

Deterministic mapping:

- BeginBlock(17,526,666): old params.
- EndBlock(17,526,666): proposal 265 is finalized/executed and new mint params are committed.
- BeginBlock(17,526,667): first mint under new params.

**Canonical T0: block 17,526,667 at 2024-08-08T16:13:58.676Z.**

Status: **T0_CERTIFIED**.

## AKT Proposal 283 — CERTIFIED

Persisted governance receipt:

- Proposal ID: 283.
- Type: `/cosmos.params.v1beta1.ParameterChangeProposal`.
- Status: `PROPOSAL_STATUS_PASSED`.
- Voting end: `2025-03-14T13:25:56.642245036Z`.
- Mint changes:
  - `InflationMin`: 8% -> 4%.
  - `InflationMax`: 13% -> 8%.

The corrected voting-end date is **2025-03-14**, not 2025-03-06.

Canonical block-time bracket recovered from the source-only Akash block index:

- H-1 = block **20,631,472**
  - time: `2025-03-14T13:25:53.881Z`
  - hash: `28ADA6EF5630AC3A32472841C5E43089DDBA1F0FF844F354EAEB80B31ED7423C`
- H = block **20,631,473**
  - time: `2025-03-14T13:25:59.825Z`
  - hash: `0ACB9BE2CFFF9ED4523C1568C878ABD651A2849DB84134B96D5312238490E1DE`
- voting end lies strictly between H-1 and H.
- H+1 = block **20,631,474**
  - time: `2025-03-14T13:26:06.017Z`
  - hash: `AE06847622A0C05350BA25661D2A78E948DB3BE78C5EA4064DC2D8A66EDDB97D`

Deterministic mapping:

- BeginBlock(20,631,473): old params.
- EndBlock(20,631,473): proposal 283 is finalized/executed and new mint params are committed.
- BeginBlock(20,631,474): first mint under new params.

**Canonical T0: block 20,631,474 at 2025-03-14T13:26:06.017Z.**

Status: **T0_CERTIFIED**.

## Integrity note on rejected pseudo-history

Public REST/LCD providers were observed returning current mint parameters while rejecting the requested historical block as pruned/unavailable. Such responses demonstrate that the `x-cosmos-block-height` header was ignored by those providers.

Those responses are explicitly rejected as historical evidence and are not used anywhere in the certifications above.

## Updated gate state

Previously certified: 9/12.

Newly certified here:

- AKT 265.
- AKT 283.

Current certified total: **11/12**.

Remaining unresolved event:

- SCRT Proposal 287.

Current family verdict remains:

`SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED`

until SCRT 287 receives a defensible canonical T0. No Development or market payload retrieval is authorized yet.
