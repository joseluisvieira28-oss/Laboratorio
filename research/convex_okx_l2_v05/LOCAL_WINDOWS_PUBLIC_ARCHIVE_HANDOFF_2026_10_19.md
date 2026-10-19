# CONVEX V05D — OFFLINE WINDOWS TWO-ARCHIVE REAL `.data` OPERATOR GUIDE

**CURRENT CORRECT GUIDE, 19 Oct 2026. This supersedes V05C's experimental `local_archive_importer.py`**: that older V05C prototype incorrectly assumed `.ndjson` TAR members and exchange-provided `seqId` fields; the real original OKX portal files have one `.data` member with JSON lines and **no sequence metadata**. Do not use V05C to claim these official portal files are invalid.

## Two original files already downloaded by operator

1. `SOL-USDT-SWAP-L2orderbook-400lv-2023-05-29.tar.gz`
2. `BNB-USDT-SWAP-L2orderbook-400lv-2023-11-01.tar.gz`

Do not rename/convert/redistribute; terms restrict raw historical market data redistribution. The V05D source review was pre-frozen in `V05D_REAL_UPLOADED_ARCHIVE_PRE_T0_FREEZE_2026_10_19.md`.

### Execute **locally without internet** (Windows PowerShell)

From the root of branch `research/convex-okx-l2-custody-and-sweep-v05-2026-10-19` with Python 3.11+:

```powershell
py -3 -m research.convex_okx_l2_v05.operator_uploaded_l2_v05d `
  --sol "C:\Users\Public\Downloads\SOL-USDT-SWAP-L2orderbook-400lv-2023-05-29.tar.gz" `
  --bnb "C:\Users\Public\Downloads\BNB-USDT-SWAP-L2orderbook-400lv-2023-11-01.tar.gz" `
  --out ".\local-private-okx-v05d"
```

Replace `C:\Users\Public\Downloads` with the files' actual directory. The tool has **no network calls or trading methods** and never sends any private orderbook file to GitHub. It reads tar.gz incrementally, requires exact original filename, one `.data` member, source UTC date/instrument, first snapshot, nondecreasing updates, 400 levels on each side and causal prior price <= frozen V5 entry T0.

Optional `orjson` speeds up parsing but Python stdlib JSON works without it. A result JSON is created at `local-private-okx-v05d\V05D_LOCAL_TWO_UPLOADED_ORDERBOOK_CAUSAL_RECEIPT.json`. You may share the **derived sanitized summary** only, not the raw archive. For verification, check the local archive SHA256 values against the uploaded-file receipts stored privately:
- SOL compressed raw `330bfc2eb74a926cf6525cbadc70a16345330b14814f93d05a61c5cc185b1289`.
- BNB compressed raw `5eb76eac5e930086b3068528379d8fb0ec1373aa523fbb46640042d2d22afdbe`.

These are local-file SHA256 hashes, **not official OKX signed checksums**.

## Frozen economic limitations

T0 original SOL1h signal: `2023-05-29 16:05:00.000Z`, original frozen Binance-model base qty `104.79202011433037 SOL`. Original BNB4h signal: `2023-11-01 16:05:00.000Z`, base qty `8.822493532731512 BNB`. Four tiers of EXACT 0.25/0.50/0.75/1.00 of those base quantities; no hindsight ratio selection. The analysis applies OKX official listing announcements as **provisional 2023 contract sizes**: SOL `1 SOL /contract` announced 2021 and BNB `0.01 BNB /contract` announced 2022. Actual 2023 dates' contract size and lot/increments are not individually verified; so output quantities may be unorderable fractions of a contract.

No sequence identifiers in actual 2023 `.data` files: timestamp order and repeated snapshots are observed but losslessness of updates is NOT provable. Book state at T0 and hypothetical ASK-level walk are **descriptive source observations, not actual broker fills**. No funding, exits, gaps, venue commissions, stop execution or 2026 independent holdout analyzed. No LIVE GO. Nothing needs access to any trading account or keys.

Official original notices:
- SOL: https://www.okx.com/en-eu/help/okx-to-enable-margin-trading-savings-and-list-perpetual-for-sol-lon
- BNB: https://www.okx.com/de/help/okx-to-enable-margin-trading-savings-and-list-perpetual-for-bnb
