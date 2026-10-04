# MEXC-WTI-EVENT-SHOCK-001 — SOURCE GATE CLOSEOUT V1.2

Date: 2026-10-04
Run: 37201216413
Artifact SHA256: `87e48926bbb586f6c9da3f613925b5ce59a715ea39ffeba1cb05197f38ca3f9c`

## Verdict

`MEXC_WTI_EIA_SOURCE_PASS`

## MEXC evidence

- exact symbol: `USOIL_USDT`
- display name: `OIL(WTI)_USDT`
- apiAllowed: true
- contract size: 0.01
- public 1m klines: PASS
- live public index: PASS
- index origins: BINANCE_FUTURE / ALLTICK / BINANCETICKER / HYPERLIQUID
- source-gate fee metadata snapshot:
  - makerFeeRate = 0
  - takerFeeRate = 0.0001
  - isZeroFeeSymbol = false

The fee snapshot is current metadata only. It is not treated as historical fee authority.

## EIA authority

Official EIA WPSR schedule page was retrieved and hashed.

Proven:
- standard Wednesday 10:30 a.m. Eastern release;
- 2026-02-19 12:00 ET exception;
- 2026-05-28 12:00 ET exception;
- 2026-09-10 12:00 ET exception.

## Governance

- historical outcomes opened: 0
- historical WTI backtest run: false
- inventory surprise used: false
- consensus used: false
- account reads: false
- auth: false
- wallets: false
- orders: false
- exchange mutation: false
- live trading: false

No WTI/EIA research family was found in the repository before this source gate.
