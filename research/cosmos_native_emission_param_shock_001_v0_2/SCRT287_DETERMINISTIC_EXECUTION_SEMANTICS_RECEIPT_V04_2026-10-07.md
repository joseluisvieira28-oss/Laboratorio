# COSMOS-NATIVE-EMISSION-PARAM-SHOCK-001 — SCRT 287 deterministic execution semantics receipt V0.4

Date: 2026-10-07  
Branch: `cosmos-native-emission-param-shock-001-v0.2-t0-remediation-2026-10-07`  
Scope: SOURCE ONLY / NO MARKET DATA  
Market prices, OHLC, returns, trading volume, order books, account data, wallets, private endpoints and 2026 outcomes accessed: **NO**

## Status

This receipt closes the **protocol-semantics** portion of SCRT Proposal 287 T0 recovery.

It does **NOT** certify the canonical T0 by itself.

Remaining missing evidence is narrowly defined:

> identify from immutable historical block metadata the unique block **H** that is the first Secret Network block whose timestamp is greater than or equal to the proposal voting end `2023-12-07T02:54:58.930543213Z`.

Once H is pinned, the version-pinned execution semantics below deterministically imply that **H+1 is the first mint BeginBlock able to use the new mint parameters**.

## Canonical proposal anchor already persisted

Secret Network Proposal 287 is already preserved in `RECOVERY_EVIDENCE_V02.json` from the LavenderFive public REST source.

- proposal id: `287`
- type: `/cosmos.params.v1beta1.ParameterChangeProposal`
- status: `PROPOSAL_STATUS_PASSED`
- voting end: `2023-12-07T02:54:58.930543213Z`
- parameter change 1:
  - subspace: `mint`
  - key: `InflationMax`
  - value: `0.090000000000000000`
- parameter change 2:
  - subspace: `mint`
  - key: `BlocksPerYear`
  - value: `5435774`

This is a direct mint-parameter mutation, not merely a signaling proposal.

## Secret binary version active at Proposal 287 execution

The official Secret Foundation v1.12 upgrade instructions pin the v1.12 halt/upgrade boundary at block **11,136,666** and instruct validators to install the `v1.12.0` mainnet binary.

Source:
- repo: `SecretFoundation/docs`
- commit: `6ed4f467c782078370466610487c4b6ee58e1eb8`
- path: `infrastructure/upgrade-instructions/v1.12-1.md`
- blob SHA: `495f8588d5bffecc9e0cd4212ee02569b5141eb6`

The official v1.13 instructions pin the subsequent v1.13 halt/upgrade boundary at block **14,360,000**, expected on 2024-05-23, and explicitly instruct operators to stop the v1.12 node and install v1.13.

Source:
- repo: `SecretFoundation/docs`
- commit: `6ed4f467c782078370466610487c4b6ee58e1eb8`
- path: `infrastructure/resources/upgrade-instructions/v1.13.md`
- blob SHA: `9e328b5bb1fd7115818c89e63725a4471d73de94`

Proposal 287 voting ended on 2023-12-07, after the v1.12 activation and months before the v1.13 activation. Therefore the relevant mainnet application line is **Secret Network v1.12.x**, and the canonical v1.12.0 source is an appropriate version-pinned semantics anchor.

## Cosmos SDK / Secret fork pin

Secret Network tag `v1.12.0` pins:

- declared Cosmos SDK dependency: `github.com/cosmos/cosmos-sdk v0.45.16`
- effective replace:
  `github.com/cosmos/cosmos-sdk => github.com/scrtlabs/cosmos-sdk v0.45.13-0.20230802150248-ea64f27dc58d`

Source:
- repo: `scrtlabs/SecretNetwork`
- ref: `v1.12.0`
- path: `go.mod`
- blob SHA: `3ed581e70bb602c8165f76518bf00e5846be72ee`

The relevant execution semantics are therefore pinned to Secret's fork commit **ea64f27dc58d**.

## Application module ordering

Secret Network v1.12.0 `app/app.go` explicitly configures:

### BeginBlock order

`minttypes.ModuleName` is in `SetOrderBeginBlockers`.

### EndBlock order

`govtypes.ModuleName` is in `SetOrderEndBlockers`.

Source:
- repo: `scrtlabs/SecretNetwork`
- ref: `v1.12.0`
- path: `app/app.go`
- blob SHA: `cbb172b5bd5db93fb3b266953572ab3e7d738426`

The application wires `app.mm.BeginBlock` and `app.mm.EndBlock` as the ABCI BeginBlocker and EndBlocker.

## Governance finalization semantics

Secret fork `ea64f27dc58d`, `x/gov/abci.go`:

1. governance EndBlocker calls `IterateActiveProposalsQueue(ctx, ctx.BlockHeader().Time, ...)`;
2. therefore proposals whose voting period has ended at or before the current block header time are processed in that block's EndBlock;
3. if the proposal passes, the registered proposal handler is executed in a cache context;
4. on success, the state mutation is written and the proposal is marked passed.

Source:
- repo: `scrtlabs/cosmos-sdk`
- ref: `ea64f27dc58d`
- path: `x/gov/abci.go`
- blob SHA: `8749fc7f685e62d9788cfceda2990b9d537ce79e`

## ParameterChangeProposal mutation semantics

Secret fork `ea64f27dc58d`, `x/params/proposal_handler.go`:

- `NewParamChangeProposalHandler` dispatches `ParameterChangeProposal` to `handleParameterChangeProposal`;
- for every change it retrieves the target subspace and calls:
  `ss.Update(ctx, []byte(c.Key), []byte(c.Value))`.

Thus Proposal 287's `mint.InflationMax` and `mint.BlocksPerYear` values are written during the successful governance EndBlock handler.

Source:
- repo: `scrtlabs/cosmos-sdk`
- ref: `ea64f27dc58d`
- path: `x/params/proposal_handler.go`
- blob SHA: `173cc292df490c4f43c78e4d523f00dcbc691981`

## Mint read timing

Secret fork `ea64f27dc58d`, `x/mint/abci.go`:

1. mint executes in BeginBlock;
2. it fetches the stored minter and mint parameters at the start of the BeginBlock:
   `params := k.GetParams(ctx)`;
3. it then computes the new inflation, annual provisions and block provision and mints under those parameters.

Source:
- repo: `scrtlabs/cosmos-sdk`
- ref: `ea64f27dc58d`
- path: `x/mint/abci.go`
- blob SHA: `410415d743b82f21e773f90bfb7264f1d7b5b7c2`

## Deterministic H / H+1 rule

Let:

- `V = 2023-12-07T02:54:58.930543213Z`
- `H = min(height : block_time(height) >= V)`

Then, under the version-pinned v1.12.0 / Secret Cosmos SDK fork semantics:

1. `BeginBlock(H)` runs before governance `EndBlock(H)`.
2. `BeginBlock(H)` therefore reads the **old** mint parameters.
3. Because `block_time(H) >= V`, governance `EndBlock(H)` processes Proposal 287.
4. The passed `ParameterChangeProposal` updates `mint.InflationMax` and `mint.BlocksPerYear` in that EndBlock.
5. `BeginBlock(H+1)` is the first mint BeginBlock that can read the updated parameters.

Therefore:

> **canonical first-reduced-mint T0 = H+1**

provided that immutable block metadata independently proves H as the first block whose timestamp is >= V.

## What remains prohibited

This receipt does not authorize:

- use of voting end itself as T0;
- estimated block height as T0;
- market-price or OHLC retrieval;
- return/volume/outcome inspection;
- Development;
- replacement of SCRT 287;
- relaxation of the 12/12 gate.

## New source probes prepared

Two source-only probes were added without opening market data:

- `.github/workflows/source-t0-probe-v27-secret-public-index-archive.yml`
  - public historical explorer/index routes;
  - Wayback/CDX archived explorer discovery;
  - exact block-height <-> timestamp binary search only when real historical metadata is returned.
- `.github/workflows/source-t0-probe-v28-secret-event-index.yml`
  - Tendermint `block_search` for historical governance EndBlock index;
  - `active_proposal.proposal_id=287` / passed-event routes;
  - historical `blockchain` header-range index probes.

These are genuinely distinct from merely retrying historical `/block` and `/block_results` routes.

## Current verdict

**PROTOCOL_EXECUTION_SEMANTICS: CERTIFIED**

**SCRT287_CANONICAL_T0: NOT YET CERTIFIED**

**FAMILY: SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED**

Reason remaining: immutable historical H/H-1/H+1 block metadata is still required.

No economic verdict has been produced. The hypothesis remains untested.
