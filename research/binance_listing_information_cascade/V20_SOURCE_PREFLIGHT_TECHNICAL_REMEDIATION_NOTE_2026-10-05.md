# V2.0 SOURCE-PREFLIGHT TECHNICAL REMEDIATION NOTE
Date: 2026-10-05
Status: PRE-OUTCOME / SOURCE-ONLY

The first all-binding source preflight (run 37360838284) found:
- asset-side required bars present for all KuCoin-bound assets;
- BTC-side exact required bars absent for all KuCoin-bound observations;
- BANK/Bitget raised HTTPError;
- SYRUP/LBank passed.

No 2025 prices, returns, PnL, MFE, MAE or cost-adjusted outcomes were emitted or inspected.

The repeated KuCoin/BTC pattern and the isolated Bitget HTTP error require transport-only diagnostics before any holdout outcome is opened.

Permitted remediation:
- inspect HTTP status/error bodies, returned timestamp counts and timestamp alignment only;
- repair pagination/request-window mechanics, retries/rate limiting, endpoint parameterization, or exact timestamp retrieval;
- preserve all fixed V2.0 events, T0s, venues, source-usability meaning, entry/exit timestamps, costs and gates.

Forbidden:
- venue substitution;
- event/T0/horizon/cost/gate changes;
- price/return/PnL inspection;
- outcome-dependent selection.

If the frozen venues genuinely cannot supply the mandatory bars after technical remediation, V2.0 closes SOURCE_BLOCKED.
