# CONVEX V05E — EXACT ORIGINAL SOL1h / BNB4h EXIT DAYS (source-only)

Immutable original closed-trade ledgers extracted by [GitHub Actions #39210167738](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39210167738) SUCCESS, from original untouched 2023–25 science run 38432883246. Exact entries and quantities were frozen *before* reading exit dates in `V05E_TWO_EXACT_ORIGINAL_EXIT_DATE_SOURCE_FREEZE_2026_10_19.md`.

| Candidate | Original V5 LONG entry UTC | Original V5 recorded exit UTC | Original exit type |
|---|---|---|---|
| SOLUSDT 1h | 2023-05-29 16:05:00 | **2023-06-05 16:05:00** | **STOP_INTRABAR** |
| BNBUSDT 4h | 2023-11-01 16:05:00 | **2023-11-21 17:45:00** | **STOP_INTRABAR** |

**Next two exact official OKX Futures SWAP 400-level L2 archived UTC calendar days needed:**
1. **SOL-USDT-SWAP 2023-06-05**, NOT Spot, not the original entry date.
2. **BNB-USDT-SWAP 2023-11-21**, NOT Spot.

IMPORTANT: `STOP_INTRABAR` means the original Binance model only establishes a 5-minute bar at which the assumed stop was crossed, **not an actual exchange stop acknowledgement or fill timestamp**. To evaluate exposure under historical OKX books, preserve the ENTIRE relevant 5-minute intrabar window and consider gaps/trigger source, not a falsely precise exit quote at the recorded `close_t`. Model's exit signal cannot be ported to OKX without a frozen trigger policy. No historical OKX contract `lotSz`, actual broker stop, funding, fees, exits or future net profit are proven.

History remains in-sample retrospective. Read-only, no order, protected 2026 holdout closed, no trading authority.
