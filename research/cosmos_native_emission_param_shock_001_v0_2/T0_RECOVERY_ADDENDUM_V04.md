# COSMOS-NATIVE-EMISSION-PARAM-SHOCK-001 — T0 Recovery Addendum V0.4

Date: 2026-10-07  
Branch: `cosmos-native-emission-param-shock-001-v0.2-t0-remediation-2026-10-07`

## Scope

Source-only continuation under the existing V0.1 pre-outcome freeze and V0.2 T0 source-remediation freeze.

No market prices, OHLC, returns, volumes, trades, 2026 outcomes, Development, trading, account data, wallets, private endpoints, exchange mutation, or main merge were opened or performed.

## State entering this round

The V0.3 addendum certified:

- AKT proposal 265 — canonical first-reduced-mint T0 block 17,526,667.
- AKT proposal 283 — canonical first-reduced-mint T0 block 20,631,474.

That raised the certified event count from 9/12 to **11/12**.

The only unresolved event was and remains **SCRT proposal 287**.

## SCRT 287 canonical governance anchor

Persisted governance evidence remains:

- proposal: 287
- status: PASSED
- voting end: `2023-12-07T02:54:58.930543213Z`
- intended parameter change: `mint.InflationMax -> 0.09` and `mint.BlocksPerYear -> 5,435,774`
- source framing states the change takes effect immediately when the proposal passes.

The missing requirement is still the canonical execution / first-reduced-mint block and timestamp.

## V0.4 source remediation performed

Two additional source-only probes were added and executed.

### V26 — legacy/public Secret RPC archive sweep

Workflow:
`.github/workflows/source-t0-probe-v26-secret-legacy-archive-sweep.yml`

Commit:
`d3da25de37c3e0a859c48442237e9459eaa29499`

Run:
`37623781132`

Endpoints included historical/archive/public routes documented by Secret Network or historically used by ecosystem providers, including:

- scrt-rpc.blockpane.com
- rpc.secret.forbole.com
- secret.rpc.consensus.one
- secret-4.api.trivium.network:26657
- rpc.spartanapi.dev
- secretnetwork-rpc.stakely.io
- scrt-rpc.agoranodes.com
- rpc.archive.scrt.marionode.com
- secretnetwork-rpc.lavenderfive.com
- rpc.mainnet.secretsaturn.net
- rpc-secret.whispernode.com
- rpc-secret.01node.com
- scrt.public-rpc.com
- rpc.cosmos.directory/secretnetwork

Result:

- zero endpoint returned the requested historical anchor block 11,752,974;
- multiple historical endpoints no longer resolve;
- Mario archive timed out;
- active providers returned 404/502/503, connection reset, or pruned/unavailable behavior;
- no exact historical bracket could be constructed.

### V27 — Secret archive LCD / REST sweep

Workflow:
`.github/workflows/source-t0-probe-v27-secret-archive-lcd.yml`

Commit:
`d627bee4d83bb8dd30fede88cadec419d353204d`

Run:
`37623925877`

Metadata-only routes tested included:

- `https://lcd.archive.scrt.marionode.com`
- `https://lcd.mainnet.secretsaturn.net`
- `https://secretnetwork-api.lavenderfive.com:443`
- `https://rest-secret.01node.com`
- `https://public.stakewolle.com/cosmos/secretnetwork/rest`
- `https://secretnetwork-api.highstakes.ch:1317`
- `https://rpc.ankr.com/http/scrt_cosmos`

Both Cosmos REST block path and legacy `/blocks/{height}` path families were tested.

Result:

- Mario archive LCD timed out;
- SecretSaturn historical hostname did not resolve;
- Lavender.Five / Stakewolle / High Stakes returned 400 or 501 for the historical block requests;
- 01node timed out / 502;
- Ankr required access and returned 403;
- zero route returned a defensible historical block header at the target range.

## Scientific verdict

Certified canonical T0 count: **11/12**.

Remaining unresolved event:

- **SCRT proposal 287**

Current family verdict:

`SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED`

This is **not** `NO_EDGE_DISCOVERY`.

The economic hypothesis remains untested because the source gate has not reached 12/12.

No Development or market-data retrieval is authorized under the frozen protocol while SCRT 287 lacks a defensible canonical T0.

## What would resolve the blocker

Any one of the following, if independently reproducible and source-only, would be sufficient to continue:

1. a public/archive Secret RPC or REST endpoint returning canonical block headers around the proposal voting-end time;
2. a public historical indexer giving immutable Secret block-height/time mappings for the same boundary;
3. a verifiable archival block dump / snapshot / indexed dataset from which the first block at or after the voting-end timestamp can be recovered;
4. direct historical block-results evidence around the execution boundary.

Vote-end timestamp alone must not be promoted to T0.

No event substitution is authorized.
