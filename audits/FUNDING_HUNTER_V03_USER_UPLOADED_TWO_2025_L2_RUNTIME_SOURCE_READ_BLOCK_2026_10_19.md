# CRYPTO LAB — FUNDING HUNTER V03 EXACT TWO BTC BOOKS — SOURCE BLOCKED IN THIS CHAT RUNTIME

UTC 2026-10-19. Private operator uploads received:
- `BTC-USDT-SWAP-L2orderbook-400lv-2025-06-02.tar.gz`
- `BTC-USD-SWAP-L2orderbook-400lv-2025-06-02.tar.gz`

Both user-uploaded archive sandbox paths were provided by conversation attachment routing. The operator previously manually downloaded these archives from the official OKX historical-data portal. That does NOT mean a V03 replay was executed or the exact bytes were validated in this turn.

**Frozen before inspecting actual content:** `research/funding_hunter_v03/BEFORE_TWO_UPLOADED_2025_BTC_BOOKS_QUOTE_ONLY_FREEZE.md` commit 53f2a66. Exact UTC causal samples 2025-06-02 00:05,12:05,23:55, matching instruments, first valid snapshot, delta replay, 400 levels each side, 2s age, no lookahead; no contract quantity normalization without 2025 point-in-time specs.

## Concrete V03 technical result

- A local-only research importer exists at `research/funding_hunter_v03/dual_btc_400l2_private_replay.py`, it accepts both **unaltered** official archive names, streams tar.gz -> one .data newline-JSON member, checks chronological source, snapshots/deltas, level deletion, cross, source freshness and time-aligned nearest prior books. It writes **derived quotes and SHA-only JSON**. No HTTP, exchange/trading calls, market file uploads, fee/PnL calculations or market orders.
- Synthetic-only tests in `test_dual_btc_400l2_private_replay.py` passed on Windows AND Ubuntu in [GitHub Actions #39237735827](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39237735827). These results show only engineering behavior on synthetic dummy data, not real 2025 OKX replay.
- **HARD CURRENT BLOCKER:** Python/CaaS/container-backed sandbox fails initialization with ClientError for even minimal commands; multiple direct Python and container read attempts against the exact user-uploaded sandbox paths failed before reading even the first header byte. No file size, source SHA, first event, bids, asks, 2025 reconstruction, 2025 quotes, actual usable book, spread/impact can responsibly be claimed. Not an exchange/source HTTP 403. Do NOT claim source bytes corrupted/missing: this is a local tool/runtime failure.

## User-local confidential offline replay

From a local checkout of the research branch, save both original OKX downloads in your Downloads directory on Windows; no modification or uploads:

```powershell
py -3 -m research.funding_hunter_v03.dual_btc_400l2_private_replay `
  --linear "$env:USERPROFILE\Downloads\BTC-USDT-SWAP-L2orderbook-400lv-2025-06-02.tar.gz" `
  --inverse "$env:USERPROFILE\Downloads\BTC-USD-SWAP-L2orderbook-400lv-2025-06-02.tar.gz" `
  --out ".\V03_PRIVATE_BTC_DUAL_L2_SOURCE_ONLY.json"
```

Optional `pip install orjson` to speed up large newline-JSON; stdlib JSON works without package. Command outputs derived source-only JSON and console summaries; **never publish or send raw market archives to GitHub**. Show only the derived JSON if desired. Invalid source/age/instrument returns `SOURCE_BLOCKED` / fail-closed, not fake price.

## Economic limitations unchanged

- **V03 SOURCE BYTE RECONSTRUCTION = NOT YET RUN SUCCESSFULLY**; real historical book values unknown in this runtime.
- Even once both books pass, these three observations are NOT a 24-hour trade, since V01 00:05 next-day exit would require **2025-06-03 00:05** source books for both contracts.
- Known OKX 2025-06 funding ZIP original headers `instrument_name,funding_rate,funding_time` lack exact settlement valuation; insufficient for certifying native funding cashflows.
- Linear USDT quote vs inverse USD quote differences are not arbitrage/real profit; no contemporaneous USD/USDT FX and no proof of 2025 contract face, lot sizes, mark/margin/funding conversion.
- No actual market fills, real orders, accounts, wallets, fees, forward performance, protected 2026 holdout, main merge or economic trading GO.
- V03 verdict **RUNTIME_SOURCE_READ_BLOCKED / ECONOMIC_EDGE_UNPROVEN** until source receipts actually executed. The user should not be asked to buy market data or authorize live trading.
