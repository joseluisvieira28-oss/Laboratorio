# REACTIVE-SHOCK-SCALP-005 — DISCOVERY MVE RESULT V0.1

Date: 2026-09-26
Workflow run: 36230855963
Status: REACTIVE_CEILING_SURVIVOR_EXISTS

## Frozen Discovery MVE
Official BLS-derived events:
- 4 CPI
- 4 NFP
- 8 total
- all after Bybit L2 archive availability
- no consensus
- no 2025 OOS
- no 2026 holdout

## Surviving frozen rule
Variant: FLOWPRICE_W2
Entry:
- observe T0 to T0+2s;
- direction = sign(BTC mid displacement versus pre-release mid);
- 0–2s aggressive trade flow must be nonzero and same-sign;
- enter at first BBO at/after T0+2s.

Exit horizon:
- +60s after entry.

Resolved events:
- 8 / 8

Pooled:
- mean future directional mid: +35.2417 bps
- mean optimistic maker/maker gross: +35.6767 bps
- mean MEXC maker/maker net after 12 bps fees: +23.6767 bps
- mean taker/taker gross: +34.9908 bps
- mean MEXC taker/taker net after 16 bps fees: +18.9908 bps
- mean Bybit maker/maker net using VIP0 reference: +31.6767 bps

By event family, MEXC perfect-maker net:
- CPI: n=4, mean +24.5899 bps
- NFP: n=4, mean +22.7635 bps

Event-level MEXC taker/taker net at +60s:
- 2023-02-03 NFP: +64.3955 bps
- 2023-02-14 CPI: -1.4547 bps
- 2023-04-07 NFP: -21.8818 bps
- 2023-04-12 CPI: +86.9555 bps
- 2023-07-07 NFP: +22.2938 bps
- 2023-07-12 CPI: +9.9915 bps
- 2023-10-06 NFP: +9.6038 bps
- 2023-10-12 CPI: -17.9776 bps

Taker-positive events after MEXC fee proxy: 6 / 8.

## Interpretation
This is the first microstructure/scalping family in the current program whose frozen rule produces average post-entry movement materially larger than the current MEXC API fee hurdle.

It is NOT yet an executable MEXC edge because:
- sample is only 8 Discovery events;
- historical BBO and fills are from Bybit, not MEXC;
- no MEXC slippage/latency model is applied;
- no fresh replication has been run;
- no OOS/holdout has been opened.

## Required next gate
Freeze FLOWPRICE_W2 +60s unchanged and replicate on every remaining eligible 2023 CPI/NFP event not used in the MVE.

No threshold tuning.
No alternate horizon selection in replication.
