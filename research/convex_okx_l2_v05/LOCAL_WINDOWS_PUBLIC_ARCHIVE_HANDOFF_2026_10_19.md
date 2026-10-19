# CONVEX V05C — WINDOWS / PERSONAL OFFLINE OKX HISTORICAL 400-L2 HANDOFF

**No exchange accounts, API key, trading authorization, capital or wallets needed.** The frozen V05 source [run 39202147739](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39202147739) established authentic OKX **public catalogue download-link candidates** hosted at `static.okx.com` for EXACT 2023-05-29 SOL and 2023-11-01 BNB. The bounded raw-read runner [39202571193](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39202571193) returned **HTTP 403** for both historical archive attempts; the current logs do NOT isolate whether the 403 happened during renewed catalogue fetch or archive download. We do not bypass with VPN, proxies or alternate region endpoints.

## Manual path (personal strategy research under OKX historical data license)

1. Open the publisher's [official OKX Historical Market Data](https://www.okx.com/historical-data) using your own normal browser. Choose **Order book**, **Perpetual SWAP / USDT-margined (NOT Spot)**, **400-level L2** if the choice is shown.
2. Retrieve the archive for instrument **SOL-USDT-SWAP** on **2023-05-29 UTC**; and separately **BNB-USDT-SWAP** on **2023-11-01 UTC**. These exact historical dates were frozen BEFORE looking at OKX. They represent original Binance V5 SOL1H and BNB4H paper entry UTC times **16:05:00.000** on the respective days.
3. Expect official files resembling `SOL-USDT-SWAP_..._2023-05-29.tar.gz` and `BNB-USDT-SWAP_..._2023-11-01.tar.gz`. Exact filenames are set by OKX; do not rename a different symbol/date/archive into a matching name. If the archive uses a different archive format, report it without converting/pretending. Do NOT upload raw market files to public GitHub/Telegram.
4. If OKX prompts for a user account or shows an availability/region error, **do not provide any password or trading key** to the assistant. Share only a redacted screenshot or a brief text of the product/date and error; stop if terms/restrictions prohibit download.
5. On a Windows local clone or downloaded ZIP of branch `research/convex-okx-l2-custody-and-sweep-v05-2026-10-19`, from repository root use Python 3.11 or later:

```powershell
py -3 -m research.convex_okx_l2_v05.local_archive_importer `
  --sol-archive "C:\Users\Public\Downloads\SOL-USDT-SWAP_l2_orderbook_2023-05-29.tar.gz" `
  --bnb-archive "C:\Users\Public\Downloads\BNB-USDT-SWAP_l2_orderbook_2023-11-01.tar.gz" `
  --out ".\local-only-source-receipts"
```

Replace the two paths with the ACTUAL publisher download filenames and your download location. You may omit one `--*-archive` while you only have the other; missing one is reported SOURCE_BLOCKED, never synthesized.

6. Inspect `local-only-source-receipts\V05C_LOCAL_TWO_ARCHIVE_SOURCE_REPORT.json` and paste **only the sanitized JSON report** back into our chat. It contains SHA256, source structure/status and UTC event age but **no raw bid/ask prices**, no API key or wallet details. Do not publicly commit the two raw `.tar.gz` source files. Official terms permit personal use for your own strategy development but restrict redistribution: https://www.okx.com/en-ae/help/historicaldata-terms-and-conditions

## What the local tool DOES and DOESN'T prove

- Checks filename instrument/day, local file bounded <=190MB, SHA256 transport custody, TAR/NDJSON structural integrity, chronological original T0, mandatory full snapshot and sequential delta continuity when available, no future/stale book accepted.
- If a file is >190MB, the source gate fails closed. Do not change caps post-outcome inside this frozen experiment.
- A local file SHA is NOT a vendor-signed checksum. Additional publisher custody (if available), historic contract `ctVal`, tick/lot rules, L2 depth and bid-side exit are needed before exact historical taker VWA price and FULL net simulated economics.
- Even if source structure passes, no real broker fills, stops, independent OOS, permission to trade, strategy profitability or guaranteed money machine follows from it.

No user action required to keep original shadow signals working. Nothing touches `main`/Windows watchers/MEXC account.
