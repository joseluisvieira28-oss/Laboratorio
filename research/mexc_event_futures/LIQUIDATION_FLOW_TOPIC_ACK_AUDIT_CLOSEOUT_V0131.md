# LIQUIDATION-FLOW-FWD-001 — INDEPENDENT TOPIC ACK AUDIT CLOSEOUT V0.13.1

Date: 2026-10-03
Status: SOURCE-ONLY
Verdict: `PARTIAL_SOURCE`

## Run

- workflow: `MEXC V0.13.1 Liquidation Independent Topic Ack Audit`
- run: `37100075588`
- job: `111137718301`
- head: `d776e9f23a843305fd64638f09ea0889a823c615`
- artifact: `v0131-liquidation-independent-topic-ack-audit`
- artifact id: `11265289330`
- artifact digest: `sha256:590fd5d3ab57aec6603ed67840ea1d99c67e648aba50fa39462d6592c55969fd`

## Result

Two independent public Bybit websocket connections were used, one per liquidation topic.

- BTCUSDT subscription acknowledgement: PASS
- ETHUSDT subscription acknowledgement: PASS
- BTC valid real liquidation events in this 90-second audit: 0
- ETH valid real liquidation events in this 90-second audit: 0
- transport/schema errors: 0
- Event Futures outcomes opened: 0

This independently removes "ETH topic was silently rejected" as the leading explanation for the prior zero-ETH interval. It does NOT prove ETH liquidation payload semantics, because no real ETH liquidation payload arrived.

The authoritative prior BTC real-payload evidence remains anchored separately.

Family state remains `SOURCE_GATE_REQUIRED / PARTIAL_SOURCE` until at least one valid real ETHUSDT liquidation payload is preserved under the frozen validator.
