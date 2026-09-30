# TRIPLE_FISHING_OPERATOR_V0.3 — deployment handoff

Date: 2026-09-30
Branch: `triple-fishing-operator-v0.3-2026-09-30`
PR: #160 (DRAFT)
Build source SHA: `e581823ae82c6c14ab9ae9d984430ba6e248a9ea`
Release metadata receipt commit: `b2f99ef0bee4d3fad7d39583aa021307a698d479`

## Result

The software release candidate is built and CI-green. It is **not installed or armed on the operator PC yet**.

Lanes packaged behind one persistent global Futures slot:

1. BNB-LAUNCHPOOL-DEMAND-001 — operator real-money fork / no scientific credit.
2. OPTIONS-SPOTPERP-001-V2.1 — 5x BTC_USDT Futures operator fork, parent signal/risk weight preserved / no scientific credit.
3. HTF-DH03-12H-STANDALONE-FORWARD-V1 — prospective operator fork, true receipt-time gate, MEXC exchange-hosted TP/SL / no scientific credit.

## Validation

Release audit run `36722713131`: SUCCESS.
- six original synthetic release failures: 6/6 fixed;
- failed invariants: 0;
- targeted regressions: 74 PASS.

Windows build run `36722620249`: SUCCESS.
- compile PASS;
- release audit PASS;
- 74 tests PASS;
- three EXEs built;
- EXE help smoke PASS;
- flat Windows bundle uploaded.

Artifact:
- name: `mexc-triple-fishing-operator-v03-windows`
- ID: `11101231947`
- ZIP SHA256: `33991b881f43f112bee10ce895a3c5abff25113c047b74873a5d0698ca3f8b4a`
- expiry: 2026-10-07T13:40:03Z

EXE SHA256:
- `MEXCTripleFishingOperatorV03.exe` = `3fc834c2a26514861cfd51ae3ff47776c49042748baf4a969b1639c06c68af35`
- `MEXCTripleFishingReadyV03.exe` = `aa47f4ed3e009d20c4bfbada458ccb2b03a6b74a6ad2d2a857c84c0e4a98d733`
- `BuildOptionsCorrectionOverlayV01.exe` = `4e2827ac12b3faba5e049cbb94df3389c59acb108ae29510cd33b5b655110291`

## Frozen operator envelope

- max initial isolated margin: 10 USDT
- leverage: exactly 5x
- max notional: 50 USDT
- max simultaneous Futures positions: 1
- daily realized-loss kill: 5 USDT
- rolling 7-day realized-loss kill: 5 USDT
- Auto Margin Add OFF
- no martingale, averaging, pyramiding, late chase or blind resend

## API transport verification

MEXC official Postman contract collection, relevant 2026-03-31 commit `0174c98ccdd7965026e134eb51ac55cfb2e825bf`, confirms the TP/SL placement and read endpoints used by the V0.3 adapter. Current Mexc.Net implementation independently corroborates position TP/SL parameters/enums and funding-history access.

## Deployment truth

Existing BNB V0.2 remains the installed live authority until controlled handover.

Do not stop or replace the legacy BNB supervisor if it may own an open position.

Safe sequence:
1. fresh legacy BNB status on the PC;
2. if no open position, download and hash-verify artifact 11092198218;
3. install V0.3 supervisor UNARMED;
4. verify V0.3 status and live DH03 heartbeat;
5. run controlled switch/readiness;
6. only a clean authenticated readiness PASS creates the V0.3 ARMED marker;
7. legacy tasks are disabled only after clean V0.3 readiness.

No order or account mutation was performed by CI/build. Main remains untouched.


## OPTIONS Deribit zero-IV source hotfix

Fresh public-source probing on 2026-09-30 reproduced the installed V0.3 blocker. Deribit returned four BTC option rows with `iv=0`; every observed invalid sample was 0-2 DTE, already outside the frozen V2.1 30..120 DTE universe. The old parser validated IV before applying the frozen DTE filter, so scientifically ineligible rows could poison the entire source.

The hotfix changes only validation order:
- frozen DTE rejection happens before IV validation;
- an in-range DTE row still requires a finite positive index to determine moneyness;
- a frozen-eligible moneyness row still requires finite positive IV;
- no DTE, moneyness, signal, risk-weight, cost or execution threshold changed.

Evidence:
- raw schema probe run `36712636956`: 4 zero-IV samples / 2255 rows;
- fixed production-parser live probe run `36713492494`: PASS on 2266 current rows, 1606 rejected by frozen DTE and 364 by frozen moneyness;
- release audit `36712859411`: SUCCESS;
- rebuilt Windows package `36712851727`: SUCCESS.

The currently installed first V0.3 package predates this source hotfix and should remain UNARMED. Replace it with artifact `11094842456` before the controlled switch.


## Supervisor freshness race hotfix

A fresh read-only pre-switch check on 2026-09-30 showed all account/source gates healthy but returned `TRIPLE_SUPERVISOR_STATE_STALE` with `age_seconds=-1.872183`. Root cause: readiness captured `now` before network/account checks, while the supervisor kept updating its state concurrently. By the time readiness loaded the supervisor JSON, its `checked_at_utc` could legitimately be later than the old readiness-start timestamp.

Hotfix:
- supervisor freshness is measured against a fresh UTC timestamp captured after loading the supervisor state;
- genuine future timestamps still fail closed when age < 0;
- stale timestamps still fail closed when age > 15 seconds;
- no science, risk, source, signal, fee, sizing or execution threshold changed.

Evidence:
- fix commit `e581823ae82c6c14ab9ae9d984430ba6e248a9ea`;
- regression commit `0d70b5e0b093a348e66125da677406224270594f`;
- audited branch head `6e216b30e5e063a4ed63cec78bad20886280c490`;
- release audit run `36722713131`: SUCCESS;
- Windows build run `36722620249`: SUCCESS;
- artifact `11101231947`, SHA256 `33991b881f43f112bee10ce895a3c5abff25113c047b74873a5d0698ca3f8b4a`.

The production-code diff from build source `e581823a...` to audited head `6e216b30...` contains only the two CI workflow files and the new readiness regression test. No production runtime code differs.
