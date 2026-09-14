# BTC-FEE-PRESSURE-001 — SOURCE-REMEDIATION V0.4 CLOSEOUT

Status: TERMINAL — `SOURCE_DATA_PASS`  
Date: 2026-09-14 UTC  
Run: `34886378068`  
Job: `104117948275`  
Branch: `btc-fee-pressure-v0.4-boundary-normalization`  
Head tested: `945b57823fb91e767fd42c79ed2d362fce85d19f`

## Verdict
`SOURCE_DATA_PASS`.

This is a source/data/provenance result only. It is not an edge verdict and does not authorize Discovery by itself. V0.3 remains permanently `PROVENANCE_FAILURE`; V0.4 is a separately frozen prospective boundary-normalization remediation.

## Frozen lineage
- immutable MVE: `BFP-TOTALFEES-7D-001`
- source: mempool.space source bytes previously acquired under V0.3 run `34880810011`
- source reuse only; V0.4 performed no new external source acquisition
- V0.3 tested source HEAD: `41fbbd23bbf0de3bc39965c9532c57febacb4a53`
- all four V0.3 chunk artifacts re-downloaded successfully
- all artifact ZIP digests verified by GitHub
- all four TAR SHA256 receipts verified `OK`
- all four `commit.txt` receipts matched the frozen V0.3 source HEAD

## Boundary normalization result
- raw start height: `663912`
- normalized start height: `663913`
- raw end height: `877258`
- normalized end height: `877258`
- raw blocks reconstructed: `213347`
- in-window canonical blocks: `213346`
- permitted outside context blocks: `1`
- illegal outside-window blocks inside normalized interval: `0`
- raw missing heights: `0`
- normalized missing heights: `0`
- malformed rows: `0`
- missing UTC days: `0`
- daily observations: `1461`
- first day: `2021-01-01`
- last day: `2024-12-31`

The sole V0.3 predecessor context block at height `663912` is below the normalized start height and is not included in the canonical daily fee series. No outside-window block exists inside the normalized canonical height interval.

## Evidence
- V0.4 authority Drive ID: `1cgaqmcxXT6t9R1MMrzTcqQeQEFbIDp-yb3rkOK88egA`
- V0.4 run: `34886378068`
- final artifact ID: `10365390379`
- final artifact ZIP SHA256: `4d6b3a0a5738d8daf36b416a7e3ba83c5d8a647cf11eae734a0499a5edf2fca8`
- final TAR SHA256: `e6035feabed44cffbf3fbfeeaf9cf19aac26dfbed097d7216041eff8f958dc89`
- manifest SHA256: `4af2e98ac18aaf28686f7f80580ece5a7a34461f20e1955ad562e0a7328c9093`
- Drive evidence ZIP: `1f_iG_eYyYnLagjvchO-cUwpzm1N3JiPU`

## Firewalls
The final manifest records all of the following as false: BTC price values opened, ETH price values opened, returns computed, PnL computed, performance statistics computed, 2025 accessed, 2026 accessed, live trading, exchange mutation, Discovery.

## Governance consequence
The source/data gate for `BTC-FEE-PRESSURE-001 / BFP-TOTALFEES-7D-001` is now passed under V0.4. Stop here. Opening BTC price outcomes or Discovery requires a separate prospective Discovery authority/explicit authorization. No 2025/2026 access is authorized.
