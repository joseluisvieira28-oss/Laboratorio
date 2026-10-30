# V0.1 MU Cash→MUSTOCK canonical SOURCE PIN — BEFORE OUTCOMES

Source-only workflow [41013501292](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41013501292) on pre-outcome source freeze commit 9e527cdc8a5a96c1a17504611519b10024607a6d passed on 2026-10-30. Two independently retrieved raw public responses per source, exact required UTC price bar start timestamps, positive finite 1m OPEN+CLOSE, no missing. All canonical SHA256 matched, all full raw response SHA256 also matched. No signal or market outcome was calculated in that workflow. These are prices only and not exchange Event Futures execution open/expiry parity. Next outcome runner MUST re-fetch and reject any mismatched canonical response before calculating one outcome. Exactly frozen 2026-10-28/29, 12 slots/day, no dates added.

Canonical SHA256 exact sorted [epoch_minute, open, close] JSON representation:
```json
{
  "MU_CASH": {
    "2026-10-28": "75507bd294f80b45d99c4fbc8fe3abddd075f81c67dac38d0b741ed5920c6fbf",
    "2026-10-29": "c11671c50dabed40ce0e3a7800740f3aba42277cdb78fb75a141c49c1fcb7ab9"
  },
  "2026-10-28": {
    "2026-10-28": "1b28e0a2b6db3e9b921b8d9daa441e9653444023082aed367c5c56df7410fde5"
  },
  "2026-10-29": {
    "2026-10-29": "3043c944357dcdd757f2b35178d200a362ee80a81dc63a9d6135d2cdb903264f"
  }
}
```
Historic Event Futures payouts at Oct28/29 are not established; 0.80 is hypothetical, NO LIVE GO.