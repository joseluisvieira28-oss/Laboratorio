# NEAR MEXC read-only scout

Run `python -m radar.near_mexc_scout --output ../receipts/near-mexc-current`
from `crypto_edge_radar`. The module and manual workflow use only public MEXC
GET market endpoints, with no credentials or operator imports. The output
`radar_verdict.json` is a read-only Radar sidecar; it is not a dispatch input.
No live service or scheduler is changed. Receipts include raw source payloads,
request timestamps, source commit and SHA256. Market snapshots expire in 30 seconds.

Branch base is the existing Radar branch
`triple-fishing-multislot-v04-2026-10-02` at
`810804e0851e84d550107ca4a8d04bc919e4df39`; main currently has no Radar tree.
Fee authority is reused from `radar/friction.py`: 8 bps per taker fill.
Public zero-fee flags do not supersede the Lab API-route fee model.

The prior LONG entry 5.32, stop 5.16 and targets 5.55/5.72 are explicitly
unvalidated scenarios. Contract rounding, visible-book VWAP, funding and
fee-adjusted scenario economics do not establish a directional signal.
Consequently this scout cannot emit TRADEABLE_CANDIDATE without a separately
validated MEXC strategy signal. It returns NO_TRADE with the exact reason.
Future fill/slippage and funding are unknown. No automatic execution is armed.
