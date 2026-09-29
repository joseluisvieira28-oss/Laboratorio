# DLS — MARGINFI REALIZED SOL SELL-PRESSURE RETURN V0.1 — DEVELOPMENT FREEZE

Date: 2026-09-29
Branch: dls-marginfi-signed-return-v01
Status: FROZEN BEFORE ANY JAN-2024 SOL MARKET RETURN IS OPENED

Parent source authority:
- MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_PASS
- canonical source run 36558125697
- source artifact dls-marginfi-multihop-signed-flow-source-v02
- artifact ID 11029321249
- digest sha256:72a8fd7aa57883b1844f87ffccac46a139937b15ad1b491af4ef220ece0142e9
- source population 2,605 / 2,605 direction-proven, 0 incomplete, 0 ambiguous, 0 contradictions

## Scientific question

After a source-proven Marginfi liquidation that realizes collateral-to-liability selling through Jupiter,
does realized native SOL collateral sell pressure exhibit short-horizon continuation that is large enough
to survive realistic automated futures execution costs?

This is a new signed-return family.
It does not rescue the terminal Drift signed-return family or the terminal basis-dislocation family.

## Frozen asset rule

Use only source rows whose source-authoritative asset/collateral mint is exactly:

So11111111111111111111111111111111111111112

This is native wrapped SOL identity and maps one-to-one to SOL market exposure.

Reasons frozen before market outcomes:
- exact source identity;
- directly tradeable liquid SOL futures market;
- no proxy mapping from liquid-staking tokens or stablecoins;
- no asset chosen from observed future returns.

All other collateral mints are excluded from V0.1 and may not be added after outcomes.

Liability mint is unrestricted because the hypothesis concerns realized sell pressure on the collateral asset.

## Source event authority

Join the immutable Jan-2024 signed-flow rows to the immutable Jan-2024 membership rows by exact:

signature + canonical instructionAddress

The membership row supplies the canonical transaction timestamp.
The signed-flow row must have:
- classification = DIRECTION_PROVEN
- route_semantic = COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN
- asset_label = SIGNED_SELL_PRESSURE_PROVEN
- asset_mint = wrapped SOL mint above.

No token amount threshold is used.
No direction frequency threshold is used.
No price or return participates in event selection.

## Frozen market data

Market:
BINANCE USDT-M SOLUSDT perpetual futures.

Granularity:
1 minute.

Authority:
Binance public data archive, daily SOLUSDT 1m USDT-M futures klines.

Every downloaded archive must:
- have a published .CHECKSUM;
- match SHA256 exactly;
- contain unique monotonic minute timestamps;
- contain the required entry and exit minutes.

Any integrity failure => SOURCE_BLOCKED / fail closed.

Binance data is the historical research price authority only.
A surviving family still requires venue-specific forward validation before live execution.

## Frozen signal and execution rule

For each eligible source event in ascending canonical timestamp order:

A = first full UTC minute strictly after the source transaction timestamp.

If no position is open at A:
- enter SHORT SOLUSDT at the OPEN of minute A;
- exit at the OPEN of minute A + 5 minutes.

While a position is open:
- every later eligible Marginfi SOL sell event whose A is strictly before the existing exit time is ignored as an overlapping cascade event;
- no pyramiding;
- no position scaling;
- no extension of holding time.

A new trade may begin only when A >= previous exit time.

This collision rule is operational, deterministic, source-order based and frozen before returns.

## Funding firewall

Exclude a candidate trade if the interval [entry, exit] contains a standard Binance perpetual funding timestamp:
00:00 UTC, 08:00 UTC or 16:00 UTC.

Funding is not modeled in V0.1.

## Frozen costs

Primary automated execution model:
- MEXC Futures API taker fee: 8 bps per side;
- slippage: 2 bps per side;
- nominal round-trip modeled cost: approximately 20 bps.

Fee authority frozen on 2026-09-29:
MEXC official announcement "Updates to API Futures Trading Fees (Jun 1, 2026)" states API Futures taker fee 0.08%.

Stress model, descriptive only:
- same 8 bps taker fee per side;
- 5 bps slippage per side;
- approximately 26 bps round trip.

The primary gate uses only the 20 bps nominal model.
The stress result must be reported but cannot be used to rescue or kill the frozen primary classification.

No maker assumption.
No fee discount assumption.
No leverage benefit.
No rebate.

## Frozen development window

Source and market outcomes:
[2024-01-01T00:00:00Z, 2024-02-01T00:00:00Z)

Only Jan-2024 is authorized for Development.

Temporal robustness folds are frozen by calendar, not outcomes:
- F1: entry < 2024-01-16T00:00:00Z
- F2: entry >= 2024-01-16T00:00:00Z

## Frozen Development gates

Classification:

MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_SURVIVES

only if ALL are true:
1. analyzable non-overlapping trade count >= 40;
2. nominal net mean return > 0;
3. nominal net median return > 0;
4. nominal net profit factor > 1.10;
5. distinct UTC entry days >= 5;
6. F1 trade count >= 10;
7. F2 trade count >= 20;
8. F1 nominal net mean > 0;
9. F2 nominal net mean > 0;
10. UTC-day block-bootstrap 95% CI lower bound of nominal mean > 0.

Bootstrap:
- 20,000 replicates;
- resample complete UTC entry-day blocks with replacement;
- seed = 26092901.

If market/source integrity fails:
MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_SOURCE_BLOCKED

Otherwise if any gate fails:
MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_NO_EDGE

## Frozen future boundaries

Only if Development SURVIVES:
- OOS source window is frozen as [2024-02-01, 2024-04-01);
- OOS market outcomes remain CLOSED until the exact source population is acquired and source-authorized under the same semantics;
- a separate OOS execution artifact must use the identical 5-minute rule and identical primary cost model.

Only if OOS later survives:
- holdout source window is frozen as [2024-04-01, 2024-07-01);
- holdout market outcomes remain CLOSED until source authority is complete.

2025 and 2026 market outcomes remain protected and CLOSED.

## Forbidden rescue

After Jan-2024 Development outcomes are opened, V0.1 may NOT:
- change 5-minute hold;
- add 1m/3m/10m/15m alternatives;
- add amount thresholds;
- select only large liquidations;
- select liability token;
- add other collateral assets;
- switch long/short direction;
- change collision handling;
- change primary fees/slippage;
- remove losing days;
- optimize entry delay;
- use maker fills;
- condition on volatility, time of day, regime, hop count or route size.

Any materially distinct hypothesis requires a new family and a new pre-outcome freeze.

## Firewall

jan_2024_development_opened_after_freeze=true
feb_mar_2024_oos_opened=false
apr_jun_2024_holdout_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
