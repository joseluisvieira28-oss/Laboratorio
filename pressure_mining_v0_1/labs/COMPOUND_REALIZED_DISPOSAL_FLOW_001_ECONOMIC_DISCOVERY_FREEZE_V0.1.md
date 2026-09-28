# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — ECONOMIC DISCOVERY FREEZE V0.1

Date: 2026-09-28
Status: FROZEN PRE-OUTCOME / 2025 MARKET OUTCOMES LOCKED
Primary family: CREDIT
Secondary family: MICRO / FLOW

## 1. Scientific question

After a confirmed Compound III `BuyCollateral` disposal block, does the affected liquid collateral proxy continue to underperform BTC over the next five tradable minutes?

This is a **post-confirmation residual-pressure** test.

It is deliberately harder than measuring the in-block swap itself:
the signal may be acted on only after the Ethereum block containing BuyCollateral is already known.

## 2. Ex-ante causal rationale

Source-only evidence established:
- 999 historical BuyCollateral logs in 2023-2024;
- exact recipient reconstruction on 68/68 sampled events;
- same-transaction onward collateral transfer on 59/68;
- corrected route classification found recognized DEX swap evidence on all 59/59 onward-transfer events.

The economic hypothesis is therefore:
realized discounted collateral disposal plus exchange routing may leave a short-lived residual sell-pressure footprint after block confirmation.

Expected primary sign:
**negative** collateral-proxy return relative to BTC.

This direction is frozen from the disposal-pressure mechanism.
It receives zero credit from the previously opened positive 24h diagnostic in COMPOUND-INVENTORY-PERSISTENCE-001.

## 3. Protected outcome window

Discovery market outcomes:
calendar year 2025 only.

2026 remains sealed for exact-rule independent OOS if and only if 2025 Discovery passes.

This document does NOT authorize opening 2025 market outcomes.

## 4. Frozen primary asset/proxy population

Primary response population uses only collateral addresses with a prospectively fixed liquid proxy and a non-BTC benchmarkable response:

- WETH `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` -> ETHUSDT
- wstETH `0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0` -> ETHUSDT
- LINK `0x514910771af9ca656af840dff83e8264ecf986ca` -> LINKUSDT
- UNI `0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` -> UNIUSDT
- COMP `0xc00e94cb662c3520282e6f5717214004a7f26888` -> COMPUSDT

Benchmark:
BTCUSDT.

BTC-backed collateral wrappers are excluded from the **primary** test because a BTC-relative response would be mechanically degenerate.
Other collateral addresses are excluded unless a separate new LAB_ID / freeze defines their economic proxy before outcomes.

No asset may be added or removed after 2025 returns are opened.

## 5. Frozen predictor clustering

Raw BuyCollateral logs are not treated as independent observations.

Cluster key:
`(proxy_symbol, ethereum_block_number)`.

For each cluster:
- cluster timestamp = Ethereum block timestamp;
- FLOW_USDC = sum(baseAmount) / 1e6 over all eligible BuyCollateral logs in that proxy/block;
- no minimum-flow threshold;
- no top-tail filter;
- no buyer filter;
- no route filter;
- no volatility filter;
- no regime filter.

wstETH and WETH map to the same ETHUSDT proxy, therefore they collapse into the same ETH/block cluster when they occur in one block.

## 6. Frozen market data and execution boundary

Market data source for Discovery:
public Binance Vision Spot 1-minute klines.

Required symbols:
BTCUSDT, ETHUSDT, LINKUSDT, UNIUSDT, COMPUSDT.

Signal becomes observable only after the Ethereum block is confirmed.

Entry:
the OPEN of the first Binance 1-minute bar whose open timestamp is strictly greater than the Ethereum block timestamp.

Exit:
the CLOSE of the fifth complete 1-minute bar beginning at the entry bar.

Thus the event block itself and the partial Binance minute containing the block are never traded.

## 7. Frozen response

For each cluster:

`R_PROXY_5M = exit_close_proxy / entry_open_proxy - 1`

`R_BTC_5M = exit_close_BTC / entry_open_BTC - 1`

`REL_5M = R_PROXY_5M - R_BTC_5M`

Expected sign:
`REL_5M < 0`.

A short-proxy / long-BTC gross spread return is:
`GROSS_SPREAD_5M = -REL_5M`.

This Discovery tests gross residual market response.
It does not claim executable net PnL and does not select a live venue or cost model.

## 8. Frozen independence and inference

Primary independence unit:
UTC ISO week.

Within each ISO week:
- equal-weight all eligible proxy/block cluster REL_5M observations;
- compute one weekly mean.

Primary statistic:
equal-weight mean of weekly means.

Bootstrap:
- resample ISO weeks with replacement;
- 10,000 iterations;
- seed 20260928;
- two-sided percentile 95% CI.

Leave-one-week-out:
recompute primary mean after dropping each ISO week once.

## 9. Frozen primary PASS gate

Discovery PASS requires all:

1. >= 12 eligible ISO weeks;
2. >= 100 eligible proxy/block clusters;
3. primary mean weekly REL_5M < 0;
4. bootstrap 95% CI upper bound < 0;
5. >= 60% of eligible ISO weeks have negative weekly mean REL_5M;
6. every leave-one-week-out primary mean remains < 0.

Any failed condition => `DISCOVERY_FAIL_NO_SUPPORT`.

## 10. Frozen diagnostics — zero rescue power

Report but do not use to rescue:
- raw cluster-level mean / median REL_5M;
- results by proxy;
- results by calendar quarter;
- Spearman rank correlation between log1p(FLOW_USDC) and -REL_5M;
- top-1%, top-5% and top-10% flow contribution diagnostics;
- buyer concentration from predictor source;
- contemporaneous event-minute movement if available only as a non-tradable diagnostic.

Diagnostics cannot change the primary decision.

## 11. Anti-rescue firewall

If 2025 fails:
- no inverse-long rescue;
- no 1m / 3m / 10m / 15m / 30m horizon rescue;
- no COMP-only / ETH-only / LINK-only / UNI-only rescue;
- no minimum-flow threshold rescue;
- no top-buyer exclusion rescue;
- no volatility/regime filter rescue;
- no route-only subgroup rescue;
- no alternative benchmark rescue;
- no fee/cost reinterpretation rescue.

A failed exact 5-minute child is terminal.

## 12. Advancement if 2025 passes

A 2025 PASS gives Discovery credit only.

Before any promotion:
- preserve this exact contract;
- open a separate exact-rule 2026 OOS only under explicit protected-outcome authority;
- then perform separately frozen execution/cost/capacity translation.

No Tier, capital or live-trading authority is implied.

## 13. Current firewall

market_prices_opened=false
2025_market_outcomes_opened=false
2026_market_outcomes_opened=false
returns_computed=false
pnl_computed=false
live_trading=false
orders=false
exchange_mutation=false
capital=false
paid_data=false
main_merge=false
post_outcome_tuning=false
