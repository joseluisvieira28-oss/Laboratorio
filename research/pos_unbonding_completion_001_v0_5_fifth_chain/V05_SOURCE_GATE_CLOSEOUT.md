# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.5 SOURCE CLOSEOUT

Date: 2026-10-07
Freeze commit: c77013a5da826498c936b86a42902aed61c7dcd4
V0.5.1 Archway KYVE amendment: c5e4529f5ca32b5987583992c358bc3f08fc8522
Outcomes opened: NO
Main baseline: f263c6c6f3a57f26666a7aee28e782f2cbd08418

## Verdict

SOURCE_HISTORICAL_COVERAGE_BLOCKED

This is source-only. Economic hypothesis remains UNTESTED.

## Frozen fifth-chain order results

1. Terra 2 / LUNA — FAIL: 0 tested public RPC sources retained the fixed 2024 anchor.
2. Coreum / CORE — FAIL G2: Foundation archive reaches historical 2024 and exact block index works, but no independent second historical operator was proven.
3. Archway / ARCH — PARTIAL: KYVE pool 2 is a verified, checksum-protected full historical block source from genesis; however no independent second public/free historical source was able to serve the fixed 2024 anchor after an expanded REST/RPC sweep.

Archway KYVE fixed-height proof:
- H=3,554,500
- time=2024-03-04T14:19:15.221993843Z
- chain_id=archway-1
- bundle id=116762
- bundle SHA-256=5ed1e3dc344a08453f67f264732aab51290106d51fc44478f74b628a96ae55f5
- app_hash=9562F5DF73EE58E8612FC4FBD0A57460538C7E3EFC749246493EBD1437AB859A

No complete_unbonding counts, material-day counts, market prices, returns, volume or PnL were opened for Terra/Coreum/Archway.

## New source capability discovered after V0.5 candidate freeze

Source-only discovery identified a new capability not covered by V0.5:
- KYVE source-registry supports Axelar mainnet historical block pool;
- the open-source AxelarScan API configuration publishes a distinct mainnet archive LCD endpoint.

Because Axelar was not in the V0.5 frozen candidate order, it is NOT added to V0.5 after the fact. It may be evaluated only in a new version frozen before Axelar event counts.

## Disposition

V0.5 closes without SOURCE_GATE_PASS and without any economic verdict.
A future V0.6 may prospectively freeze Axelar as a fifth-chain source-remediation candidate using KYVE + an independently operated AxelarScan/archive path before inspecting Axelar completion counts.
