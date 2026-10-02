# MEXC EVENT FUTURES — FORWARD REPLICATION V0.2 FREEZE

Date: 2026-10-02
Status: FROZEN BEFORE NEW FORWARD OUTCOMES
Mode: RESEARCH ONLY — NO ORDERS — NO LIVE TRADING

## Authority lineage

This freeze follows:
- MEXC_EVENT_FUTURES_MULTI_ASSET_SOURCE_GATE_FREEZE_V0.1
- MEXC_EVENT_FUTURES_DIRECTIONAL_PREOUTCOME_FREEZE_V0.1
- MEXC_EVENT_FUTURES_DIRECTIONAL_TRANSPORT_AMENDMENT_01
- MEXC_EVENT_FUTURES_DIRECTIONAL_V01A_CLOSEOUT

V0.1A produced protected directional holdout survivors.
V0.2 is a replication experiment, not a tuning pass.

## Forward boundary

The forward dataset begins at the first complete 5-minute MEXC index candle whose timestamp is strictly AFTER the Git commit that creates this freeze.

No candle whose close timestamp precedes this freeze commit may enter V0.2.

The exact resolved first timestamp must be written into the first forward receipt.

## Confirmatory candidates

Exactly four 24h candidates are frozen:

C1:
- display asset: MUUSDT
- source symbol: MUSTOCK_USDT
- settlement horizon: 30m
- lookback: 5m
- signal: MOMENTUM

C2:
- display asset: MUUSDT
- source symbol: MUSTOCK_USDT
- settlement horizon: 10m
- lookback: 15m
- signal: MOMENTUM

C3:
- display asset: SPCXUSDT
- source symbol: SPCXSTOCK_USDT
- settlement horizon: 10m
- lookback: 15m
- signal: MOMENTUM

C4:
- display asset: MUUSDT
- source symbol: MUSTOCK_USDT
- settlement horizon: 10m
- lookback: 5m
- signal: MOMENTUM

No additional candidate may be added to the confirmatory family after forward collection starts.

## New preregistered session hypothesis

V0.1A post-hoc diagnostics suggested the stock-like momentum effect was concentrated outside US regular cash-market hours.

That observation is NOT confirmatory evidence.

V0.2 freezes a new secondary hypothesis before forward outcomes:

OFF_US_RTH variants of C1-C4.

For October 2026 while US daylight saving time remains active:

US_RTH = Monday-Friday 13:30 inclusive through 20:00 exclusive UTC.

OFF_US_RTH = all other UTC minutes.

This definition is frozen only for the V0.2 collection window. If V0.2 extends across a DST transition, the experiment must stop or a separately frozen calendar mapping must be introduced before the transition.

The 24h versions remain primary.
The OFF_US_RTH versions are secondary confirmatory hypotheses, not replacements.

## Base source and clock

Primary:
- MEXC public index-price Min5.

Forward exploratory source:
- MEXC public index-price Min1, captured prospectively where available.

All decisions are timestamped in UTC.

No forward fill across missing source bars.

## Entry grids

For 10m candidates:
- entry only at UTC minute divisible by 10.

For 30m candidates:
- entry only at UTC minute divisible by 30.

Signal uses only completed information available at entry timestamp.

For MOMENTUM:
- UP if index(t) > index(t-lookback)
- DOWN if index(t) < index(t-lookback)
- no prediction if equal or either observation is missing.

Outcome:
- UP if index(t+H) > index(t)
- DOWN if index(t+H) < index(t)
- TIE if equal.

Ties are returned/refunded in product mechanics and are reported separately. Directional accuracy excludes ties from win/loss denominator.

## Primary replication window

Minimum forward duration:
- 14 complete UTC days after the resolved forward boundary.

Do not stop early because results look good or bad.

If source availability prevents 14 complete days, status is:
FORWARD_SOURCE_INCOMPLETE

not NO_EDGE.

## Confirmatory metrics

Per C1-C4 and per 24h / OFF_US_RTH variant:

- eligible N
- wins
- losses
- ties
- accuracy
- Wilson 95% confidence interval
- day-block bootstrap 95% confidence interval
- exact two-sided binomial p-value versus 50%
- actual UP/DOWN target balance
- prediction UP/DOWN balance

The four 24h candidates form the primary multiplicity family.
Holm correction at alpha=0.05 is applied across C1-C4.

The four OFF_US_RTH variants form a separate secondary family.
Holm correction at alpha=0.05 is applied across those four.

## Directional replication pass

A primary 24h candidate receives FORWARD_DIRECTIONAL_REPLICATION_PASS only if:

- its full frozen 14-day window completed;
- n >= 500 for 10m horizon or n >= 150 for 30m horizon;
- accuracy > 50%;
- Wilson lower 95% bound > 50%;
- day-block bootstrap lower 95% bound > 50%;
- Holm-adjusted p <= 0.05;
- no source-integrity failure;
- no rule changed after the boundary.

OFF_US_RTH uses the same rule but is reported separately.

No 24h failure may be rescued by the OFF_US_RTH variant.
They are distinct predeclared hypotheses.

## Economic validation firewall

A directional replication pass is not an Event Futures product-edge pass.

For each timestamped payout r actually observed from a defensible public payout snapshot:

breakeven(r) = 1 / (1 + r)

Economic observations may only be evaluated when:
- payout provenance is public and timestamped;
- payout corresponds to the same asset, side and cycle;
- snapshot existed before the prediction entry;
- no private/account/order endpoint was used.

Until a defensible public payout collector is proven:

PRODUCT_ECONOMIC_STATUS = PAYOUT_PROVENANCE_BLOCKED

No constant 80% payout may be substituted for missing historical/forward payout observations.

The 70/75/80/85/90% table may be shown only as sensitivity analysis.

## Forward 1-minute research

Because retrospective Min1 coverage was insufficient, V0.2 may collect public Min1 index observations prospectively for:

- BTC_USDT
- ETH_USDT
- NVIDIA_USDT
- MUSTOCK_USDT
- SPCXSTOCK_USDT

This collector is DATA ACQUISITION ONLY.

No 1m strategy promotion is allowed under V0.2.

After enough forward 1m corpus exists, a separate V0.3 science freeze is required before 1m hypotheses are tested.

## Payout/source reverse engineering boundary

Allowed:
- public Event Futures HTML/JS inspection;
- public unauthenticated product API discovery;
- public websocket product feed inspection;
- schema parsing;
- timestamped public payout snapshot storage.

Forbidden:
- private position history;
- balances;
- account state;
- authenticated endpoint;
- private websocket;
- order/place endpoint;
- any Event Futures trade.

If a route is ambiguous as private/authenticated, do not call it.

## No-tuning rules

After the forward boundary:
- no lookback changes;
- no horizon changes;
- no polarity flip;
- no threshold introduction;
- no session-time adjustment;
- no asset substitution;
- no early stopping;
- no selective deletion of losing days;
- no candidate ranking rule changes.

Any new idea becomes a separate future freeze.

## Promotion taxonomy

Possible V0.2 outcomes:

FORWARD_DIRECTIONAL_REPLICATION_PASS
- directional result replicated under frozen rules.

FORWARD_DIRECTIONAL_REPLICATION_FAIL
- complete source/window but directional rule failed frozen gates.

FORWARD_SOURCE_INCOMPLETE
- required forward source/window did not complete.

PAYOUT_PROVENANCE_BLOCKED
- directional test may be valid, but product economics cannot be validated.

PRODUCT_ECONOMIC_REPLICATION_PASS
- may be used only if real timestamped public payouts were captured prospectively and a separately specified economic gate passes.

V0.2 by itself never authorizes real-money trading.

## Governance

- no main merge;
- no live trading;
- no orders;
- no authenticated account access;
- no private endpoint;
- no post-outcome rescue;
- no inference that a directional survivor equals a profitable Event Futures strategy.
