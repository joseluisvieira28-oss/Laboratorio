# V02E — INVERSE BTC-USD-SWAP MONTHLY FUNDING SOURCE FILE HEADER/TRANSPORT FREEZE

19 Oct 2026 UTC, before first V02 inverse market ZIP bytes requested/read. Following success of original required three-source-family metadata run 39228295401, test **one** exact original OKX 2025-06 BTC-USD perpetual inverse funding file, without touching market values or payout rows.

- One unsigned metadata GET to official `www.okx.com/api/v5/public/market-data-history`, module3, `instType=SWAP`, `instFamilyList=BTC-USD,ETH-USD,SOL-USD`, monthly begin=end 2025-06-01T00:00:00Z. Select ONE link only when associated by family and filename with BTC-USD, excluding BTC-USDT, exact month.
- At most one HTTPS source archive GET `static.okx.com`, compressed max 10MiB, timeout <=25s, no alternate hosts/proxies/access workaround. Read local ZIP central directory and **only the first CSV header line**; no rates, market prices, funding payouts or simulations. Do not expose signed link or redistribute raw file. Hash compressed file as local custody, not official signed checksum. Missing/403 => DOWNLOAD_SOURCE_BLOCKED not economic NO-GO.
- No 2026, user account, orders, wallets, currencies, secrets, private endpoints, POST, live GO. No market data outcome read: source format only.
- Binary pass is NOT exact 2025 settlement markPx, cost/funding PnL, or complete BTC/ETH/SOL date coverage. Historical inverse mark/contract specifications, collateral FX, basis, margin/risk must be source-proven before any economic freeze.
