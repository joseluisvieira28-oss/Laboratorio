# COSMOS-NATIVE-EMISSION-PARAM-SHOCK-001 — AKASH DETERMINISTIC T0 RECOVERY RECEIPT V0.2

Date: 2026-10-07  
Branch: `cosmos-native-emission-param-shock-001-v0.2-t0-remediation-2026-10-07`  
Authority: `research/cosmos_native_emission_param_shock_001_v0_2/T0_SOURCE_REMEDIATION_FREEZE_V02.md`  
Scope: SOURCE ONLY / NO MARKET DATA

## Verdict

**AKT proposal 265: T0 RECOVERED**  
**AKT proposal 283: T0 RECOVERED**

The recovery is deterministic and version-pinned. No price, return, volume, OHLC, trade, reserve, TVL, account, wallet, private endpoint or 2026 outcome was opened.

After this receipt, the only unresolved V0.2 execution boundary is **SCRT proposal 287**. The global all-six gate is therefore still blocked until SCRT 287 is closed.

## Why H+1 is the canonical first affected mint block

For both relevant Akash software lines, the application explicitly schedules:
- `minttypes.ModuleName` in **BeginBlock**;
- `govtypes.ModuleName` in **EndBlock**.

Akash application sources:
- `akash-network/node@v0.36.0/app/app_configure.go`
- `akash-network/node@v0.36.1/app/app_configure.go`
- `akash-network/node@v0.36.2/app/app_configure.go`
- `akash-network/node@v0.38.0/app/app_configure.go`

The v0.36.x line uses Cosmos SDK `v0.45.16`. The v0.38.0 line uses the Akash fork `v0.45.16-akash.3`.

In both SDK implementations:
1. governance `EndBlocker` calls `IterateActiveProposalsQueue(ctx, ctx.BlockHeader().Time, ...)`;
2. proposals whose voting-end key is at or before the current block time are processed;
3. if passed, the registered proposal handler executes and writes the state mutation in the same EndBlock;
4. the parameter-change handler calls `Subspace.Update(...)`;
5. mint `BeginBlocker` reads `k.GetParams(ctx)` before calculating inflation and minting.

Therefore, where **H is the first canonical block with block time >= votingEndTime**:
- BeginBlock H necessarily reads the old mint parameters;
- EndBlock H executes the passed parameter-change proposal and writes the new mint parameters;
- **BeginBlock H+1 is necessarily the first mint calculation using the new parameters.**

This is a protocol-ordering proof, not an inferred time approximation.

## AKT proposal 265

Canonical proposal source: Akash Console API, captured by workflow `source-t0-probe-v21-akash-canonical-anchors`, run **37618744626**.

Proposal:
- id: 265
- title: `August 2024 Inflation Update Proposal`
- status: `PROPOSAL_STATUS_PASSED`
- voting end: `2024-08-08T16:13:48.243802688Z`
- mint parameter changes:
  - `InflationMin = 0.080000000000000000`
  - `InflationMax = 0.13000000000000000`
- proposal description confirms reduction from 13% -> 8% minimum and 20% -> 13% maximum.

Version anchor:
- Akash proposal 257: `v0.36.0`, PASSED.
- proposal 257 explicitly schedules Mainnet 12 upgrade at height **16,708,237**.
- target boundary is later than this upgrade.
- v0.36.0, v0.36.1 and v0.36.2 all preserve the same relevant BeginBlock/EndBlock ordering and Cosmos SDK v0.45.16 semantics.

Canonical block bracket from Akash indexed chain data:
- H-1 = **17,526,665**, `2024-08-08T16:13:46.576Z`, hash `01FB1EA6B5C987C6F5B50D608125E28C99FC9E0695943FFF6A7B128CDF4CF983`
- H = **17,526,666**, `2024-08-08T16:13:52.420Z`, hash `6FB3831566CB2E836C246F27DF0C9744374E8251566D1F9FC3E07172E9FFE3D7`
- H+1 = **17,526,667**, `2024-08-08T16:13:58.676Z`, hash `927E2BCC0033B18F2AC13C44D4DE54783F1B519596C8B43F9FC0A6D01486F2DD`

Since H-1 < votingEndTime < H, H is uniquely the first eligible governance EndBlock. By the frozen deterministic ordering rule:

**AKT-265 canonical execution block = 17,526,666**  
**AKT-265 canonical first reduced-issuance block T0 = 17,526,667**  
**AKT-265 T0 timestamp = 2024-08-08T16:13:58.676Z**

## AKT proposal 283

Canonical proposal source: Akash Console API, captured by workflow `source-t0-probe-v21-akash-canonical-anchors`, run **37618744626**.

Proposal:
- id: 283
- title: `Akash Inflation Update Proposal - March 6 2025`
- status: `PROPOSAL_STATUS_PASSED`
- submit time: `2025-03-07T00:10:00.663526896Z`
- voting end: `2025-03-14T13:25:56.642245036Z`
- mint parameter changes:
  - `InflationMin = 0.040000000000000000`
  - `InflationMax = 0.080000000000000000`
- proposal description confirms reduction from 8% -> 4% minimum and 13% -> 8% maximum.

Version anchor:
- Akash proposal 281: `v0.38.0`, PASSED.
- proposal 281 explicitly schedules Mainnet 13 upgrade at height **20,608,553**.
- target boundary is later than this upgrade.
- `v0.38.0` uses `github.com/akash-network/cosmos-sdk v0.45.16-akash.3`.
- the fork retains the same relevant governance EndBlock, parameter handler, and mint BeginBlock semantics.

Canonical block bracket:
- H-1 = **20,631,472**, `2025-03-14T13:25:53.881Z`, hash `28ADA6EF5630AC3A32472841C5E43089DDBA1F0FF844F354EAEB80B31ED7423C`
- H = **20,631,473**, `2025-03-14T13:25:59.825Z`, hash `0ACB9BE2CFFF9ED4523C1568C878ABD651A2849DB84134B96D5312238490E1DE`
- H+1 = **20,631,474**, `2025-03-14T13:26:06.017Z`, hash `AE06847622A0C05350BA25661D2A78E948DB3BE78C5EA4064DC2D8A66EDDB97D`

Since H-1 < votingEndTime < H:

**AKT-283 canonical execution block = 20,631,473**  
**AKT-283 canonical first reduced-issuance block T0 = 20,631,474**  
**AKT-283 T0 timestamp = 2025-03-14T13:26:06.017Z**

## Source/code anchors

Akash:
- `https://github.com/akash-network/node/blob/v0.36.0/app/app_configure.go`
- `https://github.com/akash-network/node/blob/v0.36.1/app/app_configure.go`
- `https://github.com/akash-network/node/blob/v0.36.2/app/app_configure.go`
- `https://github.com/akash-network/node/blob/v0.38.0/app/app_configure.go`
- `https://github.com/akash-network/node/blob/v0.36.0/go.mod`
- `https://github.com/akash-network/node/blob/v0.38.0/go.mod`
- `https://github.com/akash-network/net/blob/main/mainnet/upgrades/v0.36.0/info.json`
- `https://github.com/akash-network/net/blob/main/mainnet/upgrades/v0.38.0/info.json`

Cosmos SDK v0.45.16:
- `x/gov/abci.go`
- `x/gov/keeper/keeper.go`
- `x/mint/abci.go`
- `x/params/proposal_handler.go`

Akash Cosmos SDK fork v0.45.16-akash.3:
- same four source paths above; relevant execution semantics verified unchanged.

Machine capture:
- workflow: `.github/workflows/source-t0-probe-v21-akash-canonical-anchors.yml`
- run: **37618744626**
- workflow commit: `c43532c68567432636d2161ac7c9a2b277618fd9`

## Gate state after this receipt

Recovered within V0.2:
- KAVA: recovered previously
- OSMO: recovered previously
- CTK 38: recovered previously
- AKT 265: **RECOVERED HERE**
- AKT 283: **RECOVERED HERE**
- SCRT 287: **UNRESOLVED**

Current V0.2 gate: **SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED — 5/6 remediation targets recovered.**

Do not open Development or market outcomes until SCRT 287 is recovered and the all-six restoration condition is explicitly closed.
