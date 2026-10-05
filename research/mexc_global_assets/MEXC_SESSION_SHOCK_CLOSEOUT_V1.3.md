# MEXC SESSION-WIDE SHOCK CLUSTER V1.3 — SOURCE CLOSEOUT

Date: 2026-10-05
V1.2 source run: 37280235631
V1.2 source artifact ID: 11332285425
V1.2 source artifact SHA256: 87d7635ecf99588e3ba786c506196c0f3051b857d8169dfaffcc850324516976

Attempted untouched historical period:
2026-08-10 through 2026-09-08.

Source anchors:
- 2026-08-17
- 2026-08-31
- 2026-09-08

Result:
- 0 / 35 candidates passed all three anchors.
- MEXC returned zero 1-minute rows for the sampled 2026-08-17 and 2026-08-31 sessions across the candidate universe.
- MEXC history was available again on 2026-09-08.
- Binance and Bitget historical transports were generally available on the earlier anchors.

Verdict:
`UNTOUCHED_HISTORY_SOURCE_BLOCKED`

The V1.3 rule was frozen before this source verdict, but no V1.3 outcomes were opened because the required untouched MEXC history is unavailable through the public transport used.

No threshold change, horizon change, outcome scoring, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
