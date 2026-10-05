# Source receipt — FUNDING-DISPERSION-DN-001

Frozen before Stage A execution on 2026-10-05.

Public sources:
- Bybit V5 `/v5/market/funding/history`, linear USDT perpetuals.
- OKX V5 `/api/v5/public/funding-rate-history`, USDT swaps.

No API keys, login, account reads, orders, wallets, private endpoints, or 2026 outcome data are used.

Important schema controls:
- Bybit funding interval is symbol-dependent.
- OKX settlement frequency may change.
- Stage A therefore normalizes realized funding by the actual elapsed interval (bps/hour), inferred independently per venue.
- Signal uses only the last already-settled pair of rates. The next common settlement is outcome only.

Authority: FUNDING_DISPERSION_DN_001_PREOUTCOME_FREEZE_V0.1.md
