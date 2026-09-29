# MEXC BNB OPERATOR AUTOLIVE V0.1 / GLOBAL RISK V0.2

Status: PREPARED / DO NOT ARM WHILE THE CURRENT OPTIONS V2.1 POSITION IS OPEN.

## Frozen operator envelope

- Initial isolated margin per operator position: 10 USDT.
- Leverage: exactly 5x.
- Maximum notional: 50 USDT.
- Maximum simultaneous Futures positions: 1 globally.
- Daily realized-loss kill: 5 USDT.
- Rolling 7-day realized-loss kill: 5 USDT (unchanged from prior firewall until separately re-authorized).
- Cross margin: forbidden.
- Auto Margin Add: OFF.
- Martingale / averaging / pyramiding / late chase / blind resend: forbidden.
- Per-position stop-loss: none.
- Important: the daily 5 USDT realized-loss kill blocks future entries after losses are realized. It is NOT a stop-loss on an already-open 5x trade. The isolated margin is the position loss container and a single trade can lose more than 5 USDT.

"10 USDT / position" is interpreted here as 10 USDT of initial isolated margin. At 5x that targets up to 50 USDT notional. If the intended cap was 10 USDT notional, do not arm this package.

## Candidate truth

BNB-LAUNCHPOOL-DEMAND-001:
- operator-only route, no scientific credit;
- MEXC BNB_USDT perpetual;
- LONG only on a canonical eligible Binance Launchpool event;
- first 15m open strictly after the canonical announcement;
- +2s maximum technical lateness, no chase;
- automatic +24h exit;
- projected round-trip friction must remain <=30 bps.

CED1D-0031:
- transport/risk infrastructure can reuse this engine later;
- still source-locked and not activated by this package.

ETF-CME-INSTFLOW-001:
- Q4 no-peek protected;
- shadow only; no live dispatch.

OPTIONS-SPOTPERP-001-V2.1:
- existing installed executor remains independent;
- do not stop, replace or reconfigure it while its current live position is active;
- its receipt root is included in the new global risk scan when present.

## Windows order of operations

1. Verify current OPTIONS position closes and POST_TRADE_RECONCILIATION exists.
2. Extract this bundle to a stable folder.
3. Run Install_MEXC_BNB_Operator_AutoLive_V01.ps1.
   - This starts the 24x7 watcher but does NOT arm entries.
4. Run Status_MEXC_Operator_V02.ps1.
5. Run Ready_And_Arm_MEXC_Operator_V02.ps1.
   - This performs authenticated GET-only readiness checks.
   - It creates the local ARMED marker only if the account is clean and all readiness gates pass.
6. Leave the PC and internet online.

Disarm_MEXC_Operator_V02.ps1 removes permission for NEW entries without stopping management of an existing operator position.

Emergency_Stop_MEXC_Operator_V02.ps1 creates the kill switch. A running operator position is then sent through the governed emergency-exit path.

## Secrets

The bundle expects the already-existing local DPAPI files:

- %LOCALAPPDATA%\CryptoEdgeRadar\secrets\mexc_api_key.dpapi
- %LOCALAPPDATA%\CryptoEdgeRadar\secrets\mexc_api_secret.dpapi

Secrets are loaded only into the child process environment. They are not printed or stored in GitHub/Drive.

## Science boundary

This is an OPERATOR_REAL_MONEY lane. It does not earn Tier / Diamond / forward-sample credit for BNB because BNB_USDT Futures is not the frozen BNBBTC scientific instrument.

No main merge is implied by this package.
