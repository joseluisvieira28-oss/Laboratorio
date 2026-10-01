# L2R-CROSSVENUE-001 — SOURCE GATE V0.1

Date: 2026-09-30

Status: **SOURCE_TIMING_READY / PARENT_EVENT_STATE_MATERIALIZATION_BLOCKED**

## Source facts

A prior source-only probe verified 20/20 Binance BTCUSDT spot aggTrades daily objects in 2024 across four quarters. No returns were computed.

Later canonical L2 receipts establish that the Hyperliquid 2024 BTC source was successfully preserved and processed:
- 8,707 present hourly objects;
- 6,832,137,900 compressed bytes verified;
- schema normalization PASS;
- sweep-event preflight PASS;
- horizon-timing preflight PASS;
- parent 2024 Discovery completed.

The 20 dates used by the old cross-venue source probe are present in the preserved 2024 source inventory.

## Remaining blocker — corrected 2026-10-01

The exact sweep-anchor ZIP has now been located in the historical Library, but its raw bytes are not exportable to the current runtime.

More importantly, the original sweep-event preflight receipt proves that the anchor artifact was created while:
- `replenishment_computed = false`;
- `weak_strong_labels_computed = false`;
- `forward_book_depth_read = false` in the subsequent horizon-timing preflight.

Therefore recovering the anchor CSV alone is **not sufficient** to execute the intended WEAK-vs-STRONG cross-venue contrast unless that CSV contains enough event-state fields to reconstruct the frozen replenishment ratio; its exact schema has not been recovered and must not be guessed.

The preserved 2024 Discovery evidence consists only of aggregate outputs:
- cell summary;
- daily cell statistics;
- side diagnostics;
- aggregate receipt.

Those outputs prove that replenishment was computed in the parent Discovery, but they do not preserve an event-level mapping from each sweep timestamp to its R-horizon WEAK/STRONG classification. Aggregate group statistics cannot be causally joined to Binance event responses.

The actual remaining source requirement is therefore one of:

1. **event-level parent state artifact** with byte-authoritative identity and enough fields to reproduce, per sweep and frozen R horizon, at minimum:
   - anchor timestamp;
   - consumed-side direction;
   - immediately pre-sweep same-side top-5 depth;
   - selected R observation timestamp/state or an already frozen WEAK/STRONG label for R=1s/5s/15s;
   - segment identity / timing-gate status;

or

2. **exact 2024 Hyperliquid RAW bodies** (canonical manifest SHA256 `59e16ce8ea41658c2ea0fc6f2489d4deafbdc676e008d0b93f95ee6e3864913d`) so the event state and RR labels can be deterministically replayed under the already-frozen parent rules.

The anchor CSV remains useful and its expected SHA256 remains:
`be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`

but it must not be treated as sufficient until its schema is byte-authoritatively inspected.

This is a **parent event-state materialization blocker**, not NO_EDGE.

## Firewalls

- Binance returns opened: false
- cross-venue responses computed: false
- 2025 cross-venue outcomes opened: false
- 2026 access: false
- scientific rules changed: false
- main merge: false


## 2026-10-01 source-timing advance

A source-only Binance cadence preflight was completed without parsing price values or computing returns.

Evidence:
- GitHub Actions run `36816039423` = PASS;
- artifact ID `11141960210`;
- artifact digest `sha256:22de1277f5b87da2c1ff0bb8c6a89b75170d6830bee9eca469880956cdc3a336`;
- 20/20 frozen 2024 daily aggTrades ZIPs passed official SHA256 checksums;
- 26,709,512 inter-aggTrade gaps measured;
- global p99 = 946 ms;
- global p99.9 = 1,947 ms.

External timing is now prospectively frozen:
- first Binance aggTrade at-or-after target;
- no interpolation;
- no backward fill;
- maximum lateness = 2,000 ms;
- derivation = ceil(global timestamp-only p99.9 / 100 ms) × 100 ms.

The exact parent anchor ZIP was also located in the user's historical Library:
`/Crypto/L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.zip`
(size 200,205,120 bytes).

However, the current runtime cannot export its raw bytes. This is a transport/materialization blocker only. No 2024 cross-venue outcome may be opened until the inner CSV verifies exactly to:
`be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`.


## Event-state archaeology audit — 2026-10-01

A full Library search found no separate event-level replenishment/WEAK-STRONG ledger. The preserved Discovery receipt explicitly names only three evidence outputs: cell summary, daily cell stats and side diagnostics. The Library contains those three aggregate files and no identified event-level observation ledger.

The native Library was also searched for 2024 `BTC.lz4` / `HL_L2R_2024_BTC_RAW` objects and no materializable RAW corpus was found.

No requester-pays Hyperliquid reacquisition was attempted.
No Binance price response was opened.
