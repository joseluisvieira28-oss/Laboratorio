# TRIPLE_FISHING_OPERATOR_V0.3 — deployment handoff

Date: 2026-09-30
Branch: `triple-fishing-operator-v0.3-2026-09-30`
PR: #160 (DRAFT)
Build source SHA: `47ec9997dbd9d68afe2316c9693fcbc4f15f0579`
Release metadata receipt commit: `b2f99ef0bee4d3fad7d39583aa021307a698d479`

## Result

The software release candidate is built and CI-green. It is **not installed or armed on the operator PC yet**.

Lanes packaged behind one persistent global Futures slot:

1. BNB-LAUNCHPOOL-DEMAND-001 — operator real-money fork / no scientific credit.
2. OPTIONS-SPOTPERP-001-V2.1 — 5x BTC_USDT Futures operator fork, parent signal/risk weight preserved / no scientific credit.
3. HTF-DH03-12H-STANDALONE-FORWARD-V1 — prospective operator fork, true receipt-time gate, MEXC exchange-hosted TP/SL / no scientific credit.

## Validation

Release audit run `36712859411`: SUCCESS.
- six original synthetic release failures: 6/6 fixed;
- failed invariants: 0;
- targeted regressions: 74 PASS.

Windows build run `36712851727`: SUCCESS.
- compile PASS;
- release audit PASS;
- 74 tests PASS;
- three EXEs built;
- EXE help smoke PASS;
- flat Windows bundle uploaded.

Artifact:
- name: `mexc-triple-fishing-operator-v03-windows`
- ID: `11094842456`
- ZIP SHA256: `eab3d9015e4b6fa39441f349147e799d8547fd97a6b5e46ec018028c9c56770c`
- expiry: 2026-10-07T12:12:46Z

EXE SHA256:
- `MEXCTripleFishingOperatorV03.exe` = `4fb9ee43361ec7765efba43e627918c7cb48ccdec3ddc48bbbc4d33c37309c32`
- `MEXCTripleFishingReadyV03.exe` = `79515772d66d5d4dea2b69398376c1507a34a71396260829b3826d99d0551139`
- `BuildOptionsCorrectionOverlayV01.exe` = `0f9de73236213d6becae90a82625f9d7ea61efe2e31f601ba83e5c35b42f7de4`

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
