# MEV-001 — MACRO EXPECTATION VIOLATION
## NEW-MECHANISM GATE V0.1

Date: 2026-09-27  
LAB_ID: MACRO-EXPECTATION-VIOLATION-001  
Short ID: MEV-001  
Status: NEW_MECHANISM_GATE_PASS__PRE_SOURCE_ONLY  
Authority: research-only / no target outcomes / no trading

## 1. Research question

When a scheduled U.S. macro announcement causes a clear, same-direction reaction in
two independent traditional-market channels, but BTC or ETH moves materially in the
opposite direction during the same first 180 seconds, does that crypto-side violation
persist over the next 15 minutes rather than catch up to the traditional-market move?

This asks whether failure of cross-asset transmission contains information.

It does NOT ask:
- whether CPI/NFP/FOMC direction alone predicts crypto;
- whether actual-minus-consensus predicts crypto;
- whether contemporaneous crypto aggressive flow continues;
- whether a failed auction reverses;
- whether a daily cross-market fair-value residual mean-reverts.

## 2. Material causal novelty

Closest prior lineages:

### MARKET-REVEAL-CONFIRMATION-REACTION-001 / MRCR-H02
MRCR asks whether post-macro crypto microstructure ACCEPTANCE vs REJECTION predicts
subsequent direction-aligned crypto return. Its state is built from crypto flow,
displacement, retracement, spread and depth across Binance/Coinbase.

MEV-001 instead requires an EXTERNAL traditional-market directional complex first,
then studies a crypto response that contradicts that external direction.

Overlap: event calendar and crypto source infrastructure only.
Causal object: different.

### ABSORPTION-FAILED-AUCTION-001
AFA asks whether extreme Binance aggressor flow is efficiently accepted or fails.
It is not macro-conditioned and does not use a traditional-market reference state.

Overlap: acceptance/rejection intuition only.
Causal object: different.

### MACRO-TRANSMISSION-001 / MT-2Y-NASDAQ-001
MT-2Y-NASDAQ-001 used DAILY Nasdaq and 2Y yield direction to predict next-day BTC.
It failed Discovery and is immutable.

MEV-001 does not reuse that daily rule. It studies 180-second event-time disagreement
after exogenous scheduled announcements and a 15-minute post-decision horizon.

Overlap: macro/rates/equity information family.
Time scale, event conditioning, observable and mechanism: materially different.

### CMM-PR-001 — CROSS-MARKET PRICE RESIDUAL
CMM-PR-001 fit a daily causal BTC fair-value residual from options/rates/stablecoin
states and tested 24h mean reversion. It failed with the wrong aggregate sign.

MEV-001 does not estimate fair value, does not aggregate the CMM state vector, and
does not test generic convergence. It conditions only on scheduled macro events and
the contemporaneous directional response of independent traditional markets.

Overlap: cross-market disagreement concept.
Economic observable and causal mechanism: materially different.

## 3. Frozen causal statement

Scheduled macro information is first incorporated by deep traditional markets.
If independent traditional channels agree on the direction of the repricing but
crypto moves materially the other way, the contradiction can represent crypto-specific
demand/supply strong enough to override the common macro impulse. If that pressure is
real rather than noise, the crypto-side violation should persist beyond the initial
180-second decision window.

Primary mechanism family: MACRO / cross-asset information transmission.
Secondary family: LEADLAG / relative response.
Mathematical engine: conditional continuation after cross-market sign violation.

## 4. Failure mode frozen in advance

The hypothesis should fail when:
- traditional channels do not agree;
- traditional reaction is too small to establish an external direction;
- crypto disagreement is noise rather than state-specific pressure;
- macro transmission catches up quickly after the first 180 seconds;
- the relationship is unstable across CPI, Employment Situation and FOMC events;
- source latency prevents reconstruction of information actually available by decision time.

A failure must remain failure. No threshold, event-family, asset, direction, horizon
or source substitution may rescue the exact experiment after target outcomes open.

## 5. Contamination map

Already-seen internal evidence is CONTAMINATED for outcome selection:
- NEWS_SHOCK_LAB_V0.2 event-time returns/volume/flow;
- historical CPI/NFP surprise work;
- MSM-H01 2026 holdout;
- CMM-PR-001 development 2021-2025;
- MACRO-TRANSMISSION-001 daily Discovery;
- AFA/MRCR implementation diagnostics.

Allowed reuse:
- official event identity and T0 provenance;
- non-outcome source semantics;
- timestamp/arrival guards;
- Binance/Coinbase reconstruction code;
- fail-closed evidence infrastructure.

Forbidden reuse:
- selecting MEV thresholds from previously seen returns;
- claiming prior positive subgroups as MEV evidence;
- historical backtest promotion from contaminated periods.

Independent target policy: 2027 prospective only.

## 6. Frozen high-level target design

Event families:
- US_CPI
- US_EMPLOYMENT_SITUATION
- FOMC_STATEMENT

T0:
official scheduled release timestamp from BLS/Federal Reserve authority.

Decision clock:
T0 + 180 seconds.

Traditional reference channels required:
- CME Nasdaq-100 futures family;
- CME U.S. 2-Year Treasury futures family.

Economic sign convention:
- Nasdaq futures price up = risk-on contribution;
- 2Y Treasury futures price up = yields down = risk-on contribution;
- both down = risk-off contribution.

A traditional direction exists only when both channels independently pass the
future pre-target materiality rule and agree in sign. Otherwise ABSTAIN.

Crypto scope:
- BTC and ETH;
- Binance Spot plus Coinbase Advanced Spot;
- cross-venue direction agreement required;
- no USD/USDT price-level merge.

Primary violation concept:
traditional complex has a valid direction, while crypto has a valid material move
in the opposite direction at T0+180s.

Frozen future horizon:
decision + 900 seconds.

The exact scale-normalization/materiality rule is NOT selected at this pre-source
stage. It may be frozen only after a defensible source path passes, using source
semantics only and before any 2027 target observation. No target outcome may inform it.

## 7. Promotion credit

None.

A source PASS would authorize only a separate pre-target protocol freeze.
A future mechanism PASS would still not be a trading strategy, Tier promotion,
micro-live authority, execution rule or production rule.

## 8. Governance boundary

No 2027 target observation.
No protected outcome inspection.
No historical rescue.
No live trading.
No paper trading.
No orders.
No exchange mutation.
No wallets.
No paid-data purchase.
No Render deployment.
No merge to main.

END STATE:
NEW CAUSAL MECHANISM ACCEPTED FOR SOURCE FEASIBILITY ONLY.
