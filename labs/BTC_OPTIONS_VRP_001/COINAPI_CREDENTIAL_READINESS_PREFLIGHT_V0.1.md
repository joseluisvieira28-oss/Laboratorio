# BTC-OPTIONS-VRP-001 — COINAPI CREDENTIAL READINESS PREFLIGHT V0.1

Date: 2026-09-19
Branch: `btc-options-vrp-coinapi-source-probe-v0.1`
Status: **FROZEN / ZERO-NETWORK / SOURCE-READINESS ONLY**

Purpose: determine whether the GitHub Actions runtime already contains the existing `COINAPI_KEY` secret required by the frozen CoinAPI BBO source probe.

This preflight:
- makes zero network requests;
- does not print, hash, transform or persist the key;
- checks only whether the secret is empty/non-empty;
- authorizes no purchase or paid overage;
- opens no quote values, market outcomes, returns or PnL;
- opens no 2025/2026 data;
- performs no live trading, exchange mutation, wallet access or main merge.

Terminal states:
- `COINAPI_CREDENTIAL_PRESENT`
- `COINAPI_CREDENTIAL_ABSENT`

A PRESENT result would authorize only the already-frozen eight-contract source probe under `COINAPI_SOURCE_PROBE_AUTHORITY_V0.1.json`, subject to its no-purchase/no-overage rules.
