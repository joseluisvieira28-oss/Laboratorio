# ONCHAIN-CAPFLOW-001 — V0.1

Status: `FROZEN_PRE_DISCOVERY`

Protocol SHA256:

`65611c79d95e433be5dc0d9c5d4e8de19066bcbb8addc736dc875dba6d1926cf`

This directory implements only the **data acquisition and data-audit gate** for the frozen
On-Chain / Capital Flow MVE.

It does **not**:
- access 2025 or 2026 outcome data;
- calculate trading returns;
- tune thresholds;
- place orders;
- call exchange mutation endpoints;
- alter Dream Account OS live/shadow logic.

## Frozen data inputs

Capital-flow proxy:
- DefiLlama `https://stablecoins.llama.fi/stablecoin/1` (USDT)
- DefiLlama `https://stablecoins.llama.fi/stablecoin/2` (USDC)

Market data:
- Binance Vision Spot monthly `1d` klines
- `BTCUSDT`
- `ETHUSDT`
- January 2020 through December 2024 only

The acquisition script refuses to download 2025+ archives.

## Run

From this directory:

```powershell
python acquire_data.py --output .\data
python audit_data.py --data .\data
```

Expected outputs:
- `data/raw/...`
- `data/raw_manifest.json`
- `data/data_audit_report.json`

Only if `data_audit_report.json` says `"status": "PASS"` may a separate Discovery
implementation be created and run.

## Governance

Authority is the Google Drive document:

`ON-CHAIN / CAPITAL FLOW LAB V0.1 — PRE-DISCOVERY PROTOCOL`

If this code conflicts with that authority, the Drive protocol wins.
