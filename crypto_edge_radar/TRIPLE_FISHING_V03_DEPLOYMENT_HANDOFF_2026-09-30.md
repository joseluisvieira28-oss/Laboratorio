# TRIPLE_FISHING_OPERATOR_V0.3 — deployment handoff

Date: 2026-09-30
Branch: `triple-fishing-operator-v0.3-2026-09-30`
PR: #160 (DRAFT)
Build source SHA: `59192ee2748796885c67bc77c892e963c60b01a1`
Release metadata receipt commit: `b2f99ef0bee4d3fad7d39583aa021307a698d479`

## Result

The software release candidate is built and CI-green. It is **not installed or armed on the operator PC yet**.

Lanes packaged behind one persistent global Futures slot:

1. BNB-LAUNCHPOOL-DEMAND-001 — operator real-money fork / no scientific credit.
2. OPTIONS-SPOTPERP-001-V2.1 — 5x BTC_USDT Futures operator fork, parent signal/risk weight preserved / no scientific credit.
3. HTF-DH03-12H-STANDALONE-FORWARD-V1 — prospective operator fork, true receipt-time gate, MEXC exchange-hosted TP/SL / no scientific credit.

## Validation

Release audit run `36706573491`: SUCCESS.
- six original synthetic release failures: 6/6 fixed;
- failed invariants: 0;
- targeted regressions: 74 PASS.

Windows build run `36706573593`: SUCCESS.
- compile PASS;
- release audit PASS;
- 74 tests PASS;
- three EXEs built;
- EXE help smoke PASS;
- flat Windows bundle uploaded.

Artifact:
- name: `mexc-triple-fishing-operator-v03-windows`
- ID: `11092198218`
- ZIP SHA256: `818f9aa128bed21b4e4cfb8f7fe91767e398be174062f0fd3b38a0730fb9cfd2`
- expiry: 2026-10-07T11:14:15Z

EXE SHA256:
- `MEXCTripleFishingOperatorV03.exe` = `c92e91314e5b71605e23c3a6e5df52d2313ae0d50f24bb08618ce68b3c7dcfaf`
- `MEXCTripleFishingReadyV03.exe` = `769a5e192bf5c08d3385a8f21561c3ad8512d104097e299003fe01c64c4eed72`
- `BuildOptionsCorrectionOverlayV01.exe` = `fe7d64c1c83581c260caed756ccaca0d6adb2c31ace8bddaa7e955a954925ac0`

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
