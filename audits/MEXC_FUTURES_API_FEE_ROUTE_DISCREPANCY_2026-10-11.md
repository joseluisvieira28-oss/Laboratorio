# CRYPTO LAB — MEXC FUTURES PUBLIC FEE DISCREPANCY — 2026-10-11
Status: PUBLIC_SOURCE_VERIFIED / API_EXECUTION_FEE_UNVERIFIED / NO SCIENTIFIC REJUDGMENT
Research branch: research/asymmetric-shock-breakout-2026-10-11

## Immutable live-public source evidence
GitHub Actions: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38137360314
Artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38137360314/artifacts/11701546456
Result: 27/27 synthetic tests PASS, job SUCCESS, public metadata contract/clock probe PASS with **fee reconciliation open**.

Observed 2026-10-11 11:58 UTC on MEXC public GET /api/v1/contract/detail/country:
- BTC_USDT: `takerFeeRate=0.0002` = 2bps per side / 4bps taker+taker round trip;
  `feeRateMode=NORMAL`; `apiAllowed=true`, `state=0`, `futureType=1`.
  `contractSize=0.0001 BTC`, `minVol=1`, `volUnit=1`, `priceUnit=0.1`.
  Indicative minimum 1-contract notional at public ask: **8.31276 USDT**.
- SOL_USDT: `takerFeeRate=0.0002` = 2bps per side / 4bps taker+taker round trip;
  `feeRateMode=NORMAL`; `apiAllowed=true`, `state=0`, `futureType=1`.
  `contractSize=0.1 SOL`, `minVol=1`, `volUnit=1`, `priceUnit=0.01`.
  Indicative minimum 1-contract notional at public ask: **10.965 USDT**.
- Public server clock offset ~ -120ms (observation minus exchange).
- Both BBO inputs were fresh and noncrossed for that single source point.

Separately, MEXC's official 2026-05-28 announcement applies **API taker 0.08% per side = 16bps round-trip** effective June 1 2026, explicitly says API fee schedule overrides lower displayed web/app fees and promotions and warns some regions lack API:
https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742

MEXC documents `takerFeeRate`, `feeRateMode`, `apiAllowed`, `contractSize`, `minVol` as fields:
https://www.mexc.com/api-docs/futures/market-endpoints/get-contract-info

## SCIENTIFIC CONSEQUENCES

**CONFLICT CONFIRMED**, not lower API costs confirmed:
- Public instrument-specific metadata suggests 4bp RT; explicit product notice says 16bp API RT.
- These may refer to different execution channels, rate overrides, or account/region.
  Do not assert WHICH explanation is true without trusted evidence.
- `apiAllowed=true` is an instrument flag, NOT authority that the operator's
  account or jurisdiction can place MEXC Futures API orders.

For reproducibility, report all three scenarios without erasing any:
A. PUBLIC-QUOTE-ONLY: 4bps RT taker/taker (not an authenticated API fee)
B. OFFICIAL API-ANNOUNCED: 16bps RT taker/taker (frozen baseline)
C. API STRESS: 32bps RT taker/taker (frozen stress), each PLUS actual
   crossed BBO, slippage, funding, market impact, execution limitations.

No historical NO_EDGE or FORWARD_SURVIVES can be reversed by an AFTER-OUTCOME
fee haircut. Historical freezes apply unchanged to their original identity.
If an account-route fee receipt from actual reconciled order history can be
obtained under separate read-only permission, it can be used prospectively to
bind NEW execution studies; this source-only task does not access it.

## Frozen illustrative HURDLE (NOT A MARKET TEST)
For gross stop=40bps, target=4R:
- PUBLIC-QUOTE-ONLY 4bps => cost 0.1R; breakeven p=22%.
- API-ANNOUNCED 16bps => cost 0.4R; breakeven p=28%.
- API STRESS 32bps => cost 0.8R; breakeven p=36%.
- Actual gaps, funding, size-dependent spread and slippage increase the hurdle.
No signal success rate is measured; edge remains UNPROVEN.

Verdict: `SOURCE_FEE_DISCREPANCY_CONFIRMED_API_ROUTE_UNVERIFIED`.
NO orders, wallets, account reads, API credentials, money, main merge, economic
outcome opening, retuning or trading.
