# ONCHAIN-CAPFLOW-001 — V0.1A

Status: `FROZEN_PRE_DISCOVERY_AMENDED_001`

Protocol SHA256:

`1c6c66b7188694bcc2d62cb83ee050a023fba7f97388bc87933ed668d3392b65`

This directory implements only the **data-source gate, acquisition and data-audit gate** for the frozen On-Chain / Capital Flow MVE.

It does **not**:
- access 2025 or 2026 outcome data;
- calculate trading returns;
- tune thresholds;
- place orders;
- call exchange mutation endpoints;
- alter Dream Account OS live/shadow logic.

## Frozen data inputs

Capital-flow proxy:
- Coin Metrics Community API
- assets: `usdt,usdc`
- metric: `SplyCur`
- frequency: `1d`
- explicit `start_time=2020-01-01`
- explicit `end_time=2024-12-31`

**Fail-closed data gate:** if the Community API does not return both USDT and USDC with the required historical coverage, the run stops as `DATA_BLOCKED`. It must not fall back to an endpoint that exposes the 2025 holdout or 2026 locked period.

**Environment classification:** DNS failures, connection failures and timeouts are written as `EXECUTION_ENVIRONMENT_BLOCKED` and return exit code `12`. That status is operational only and must never be interpreted as a scientific `DATA_BLOCKED` result. Re-run the same frozen code after connectivity is restored.

Market data:
- Binance Vision Spot monthly `1d` klines
- `BTCUSDT`
- `ETHUSDT`
- January 2020 through December 2024 only

The acquisition code rejects 2025+ timestamps and validates that Coin Metrics pagination retains the frozen end date. The source gate is marked `PASS` only after **both** Coin Metrics and all frozen Binance Vision archives are acquired and hashed.

## Run

Preferred one-click Windows gate:

```powershell
run_data_gate_windows.bat
```

Manual equivalent from this directory:

```powershell
python acquire_data.py --output .\data
python audit_data.py --data .\data
```

Expected outputs:
- `data/data_gate_status.json`
- `data/raw/...`
- `data/raw_manifest.json`
- `data/data_audit_report.json`

Only if `data_audit_report.json` says `"status": "PASS"` may a separate Discovery implementation be created and run.

## Amendment 001

The first frozen draft referenced DefiLlama individual stablecoin endpoints. Before any acquisition or outcome inspection, we identified that those endpoints return the complete historical series through the present and would therefore expose locked 2025/2026 observations. The source was amended prospectively to the Coin Metrics Community timeseries endpoint with an explicit 2024-12-31 cutoff. Signal, assets, thresholds, costs, Discovery period and holdout rules were not changed.

## Implementation hardening — 2026-09-13

Before the first local data-gate execution, the acquisition implementation was hardened without changing the frozen research hypothesis:
- transport/DNS/timeouts are now separated from scientific data failure;
- the source gate can no longer remain `PASS` if Binance Vision acquisition fails after Coin Metrics succeeds;
- equivalent Coin Metrics pagination timestamps on the frozen final day are accepted only while remaining strictly before the 2025 holdout boundary.

These are implementation-safety corrections only. No signal rule, asset, threshold, cost assumption, Discovery period or holdout rule changed.

## Governance

Authority is the Google Drive document:

`ON-CHAIN / CAPITAL FLOW LAB V0.1A — PRE-DISCOVERY PROTOCOL`

If this code conflicts with that authority, the Drive protocol wins.
