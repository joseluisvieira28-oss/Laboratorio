# Coreum historical mainnet binary / upgrade ledger — V0.8

Candidate: `POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001`  
Recorded: 2026-10-07  
Status: source/replay evidence only; no census or market outcome authorization.

## Independent official operator documentation

Official TX node documentation, "tx upgrade history" / "Run from genesis":

`https://docs.tx.org/docs/next/nodes-and-validators/upgrades/upgrades-history`

The page explicitly instructs full-history operators to provide every historical binary and lists the following **Mainnet** sequence:

| interval / plan | activation height | required version |
|---|---:|---|
| genesis | 0 | v1.0.0 |
| v2 | 6,947,500 | v2.0.2 |
| v3 | 13,480,000 | v3.0.3 |

The same official page separately lists `v2patch1`, `v3patch1`, and `v3patch2` under **Testnet**, not Mainnet.

This is materially independent of the V0.7 archive `AppliedPlan` discovery queries: it is operator documentation describing how to run full history from genesis.

## Source-code corroboration

Pinned historical Coreum source also distinguishes the patch plans as testnet transitions:

- v2.0.2 `app/upgrade/v2/v2patch1/upgrade.go`: patch is described as testnet-only.
- v3.0.3 `app/upgrade/v3/v3patch1/upgrade.go`: patch is described as testnet-only.
- v3.0.3 `app/upgrade/v3/v3patch2/upgrade.go`: patch is described as testnet-only.

Pinned commits:
- v1.0.0: `40759d9d8a37e998f6e01229311b2ce3ac19ff63`
- v2.0.2: `dc41e552ebf9dd7b1e42e4727679bbd74c19e5c6`
- v3.0.3: `14454e7001e9f0d1d703e1dd6fbff4ac09a04cfe`

## Relation to inherited Source-A hints

V0.7 had untrusted archive-state hints:
- `v2` applied at 6,947,500
- `v3` applied at 13,480,000
- patch plan lookups empty at H=15,000,000

The independent operator documentation agrees exactly on both mainnet heights and assigns the already-pinned v2.0.2 / v3.0.3 binaries.

## V0.8 adjudication

The historical **mainnet binary activation ledger through H=15,000,000 is now sufficiently specified for a deterministic replay attempt**:

`v1.0.0 [genesis .. 6,947,499] -> v2.0.2 [6,947,500 .. 13,479,999] -> v3.0.3 [13,480,000 ..]`

This does **not** by itself establish replay validity. The runner must still:
1. execute exact application semantics;
2. prove the upgrade handoff/store migrations;
3. reproduce canonical AppHash checkpoints;
4. prove contiguous history and lifecycle evidence.

If execution contradicts this ledger, execution fails closed and this document is not used to override local evidence.
