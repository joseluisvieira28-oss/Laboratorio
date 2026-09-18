# AAVE-RISK-PARAMETER-SHOCK-001 — SOURCE CENSUS SPARSE-WINDOW REMEDIATION V0.1A

Date: 2026-09-18
Status: PREPARED BEFORE V0.1 RESULT / NOT EXECUTED

## Problem class

The frozen census queries sparse PoolConfigurator risk-configuration events through the SQD Ethereum Portal in exact 75,000-block windows.

V0.1 treats a healthy zero-match window as a technical failure. That transport behavior is suitable for dense streams but not for sparse governance/configuration events.

## Allowed remediation

If and only if V0.1 fails because an exact SQD request window returns no matching rows, V0.1A may treat that healthy zero-match response as:
- zero structural events in that exact requested window;
- transport coverage through the exact requested window end;
- no synthetic event;
- no decoded log.data;
- no economic outcome.

All frozen scientific boundaries remain unchanged:
- contract address;
- event signature set;
- from/to blocks;
- 2024-12-31 ceiling;
- primary mechanism freeze;
- no market prices, returns, future liquidations or PnL.

## No duplicate execution

V0.1A must not be launched while V0.1 remains a valid in-progress run. It is a prepared technical remediation only.
