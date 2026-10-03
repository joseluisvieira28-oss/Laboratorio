# LIQUIDATION-FLOW-FWD-001 — ONE-HOUR EXTENDED SOURCE CLOSEOUT

Date: 2026-10-03
Status: SOURCE-ONLY
Verdict: `PARTIAL_SOURCE`

## Authoritative run

- Workflow: `MEXC V0.13 Liquidation Extended Public Source Only`
- Run: `37075262340`
- Job: `111063614589`
- Head: `a29351858748db52c93e4e8dff75be370e77cb07`
- Artifact: `v013-liquidation-extended-public-source`
- Artifact id: `11257963990`
- Artifact digest: `sha256:1521ef40603b46a3e76fc148c1e6df9d830faae7c00030ed720e23c45c3e1a5f`

## Result

Observation window: 3600.987 seconds approximately.

Public Bybit linear websocket subscription acknowledgement succeeded and heartbeat traffic remained healthy. There were no transport exceptions.

Valid liquidation records:

- BTCUSDT: 3
- ETHUSDT: 0

The three BTC records passed the frozen schema and freshness checks.

Anchored valid BTC evidence:

1. raw SHA256 `4680e77698c7903751dcda04c1a8165ca2134cb4d6cf572a90198d414fefc302`
   - side: Sell
   - event T: 1790983190942
   - v: 0.004
   - bankruptcy price p: 84733.00
2. raw SHA256 `f09a4ca383e36acf2f0e3316a2133631734f01604b6b27d978eeb1fe66b23c49`
   - side: Sell
   - event T: 1790984109287
   - v: 0.008
   - bankruptcy price p: 84769.80
3. raw SHA256 `282b7fa22e79458d4b25c665d74c3eb79837d1d5fa99c428bc257436ad960455`
   - side: Sell
   - event T: 1790984671901
   - v: 0.001
   - bankruptcy price p: 84808.50

Per the frozen source semantics, Bybit `Sell` means a SHORT position was liquidated, corresponding to forced buying pressure. These records are source evidence only and MUST NOT be used as calibration observations because the family had not yet completed its two-symbol source gate.

## Scientific meaning

BTC source semantics are now demonstrated with real production liquidation payloads.

ETH remains unproven by a real liquidation payload. Zero ETH messages in this hour is neither zero liquidation flow nor no edge.

The family remains `SOURCE_GATE_REQUIRED`.

No MEXC payout/index/outcome was opened and no trading occurred.
