# MRCR H02 — Scientific Design Rationale V0.1
Status: FROZEN DESIGN RATIONALE / TARGET OUTCOMES LOCKED
Date: 2026-09-25
LAB_ID: MARKET-REVEAL-CONFIRMATION-REACTION-001
H02_ID: MRCR-H02-ACCEPTANCE-REJECTION-V01

## Causal question

After a scheduled exogenous U.S. macro announcement, does a market state showing
aligned aggressive flow, material price displacement, limited retracement,
spread normalization and incomplete replenishment of resistance-side near-touch
depth carry more subsequent direction-aligned return than a state showing
rejection/absorption?

The object is response-conditioned price discovery, not raw announcement
direction and not actual-versus-consensus surprise.

## External rationale available before target observation

1. Cont, Kukanov & Stoikov, "The Price Impact of Order Book Events".
   Short-horizon price changes are strongly linked to order-flow imbalance and
   the impact slope varies inversely with market depth.
   Source: https://arxiv.org/abs/1011.6402

2. "The probability of informed trading measured with price impact, price
   reversal, and volatility", Journal of International Financial Markets,
   Institutions and Money 42 (2016), 77-90.
   The paper motivates the combination of meaningful price impact with little
   subsequent reversal as a price-discovery state.
   DOI: 10.1016/j.intfin.2016.02.001

3. Anastasopoulos, Gradojevic, Liu, Maynard & Tsiakas, "Order flow and
   cryptocurrency returns", Journal of Financial Markets 79 (2026), 101047.
   The paper supports order flow as informative for crypto returns and discusses
   permanent versus transitory effects.
   DOI: 10.1016/j.finmar.2026.101047

4. Kroner, Mohammed & Vega, "How Do Cryptocurrencies Price Economic News?"
   (Federal Reserve Board authors, March 2026).
   The paper studies U.S. monetary-policy, inflation and labor-market
   announcements and reports announcement-time jumps in volatility, volume and
   bid-ask spreads, with elevated conditions lasting up to roughly 30 minutes;
   order flow is implicated in price discovery.
   SSRN: 6447644 / DOI: 10.2139/ssrn.6447644

These sources justify the mechanism families and macro-event families. They do
not determine the target result.

## Frozen design choices and why

Event families:
- US_CPI
- US_EMPLOYMENT_SITUATION
- FOMC_STATEMENT

Reason: they map directly to inflation, labor-market and monetary-policy
announcements in the independent macro/crypto literature. No consensus input is
needed.

Assets and venues:
- BTC: Binance Spot BTCUSDT + Coinbase Advanced Spot BTC-USD
- ETH: Binance Spot ETHUSDT + Coinbase Advanced Spot ETH-USD

Reason: two liquid crypto assets and two independently reconstructed public spot
venues already passed pre-target source/provenance work. Prices are never merged
and USD/USDT conversion is forbidden.

Event anchor:
- T0 = official scheduled release timestamp.
- pre-anchor book = latest valid book state strictly before T0.
- feature interval = [T0, T0+180 seconds].
- primary decision timestamp = T0+180 seconds.

The 180-second clock is frozen before target data. It is deliberately distinct
from the previously inspected 5/15/60-minute internal outcome windows. It sits
well inside the external literature's approximately 30-minute elevated
announcement regime while allowing immediate microstructure response to settle.

Depth:
- symmetric BPS_BAND = 10 basis points around each venue-native mid.
- resistance-side depth = ask depth for positive flow direction, bid depth for
  negative flow direction.

Reason: a basis-point band is scale-normalized across BTC/ETH and USD/USDT native
symbols. Ten basis points is an ex-ante round near-touch band and is not selected
from target outcomes.

Classifier natural boundaries:
- displacement must be at least one pre-event spread;
- current spread must recover to no more than one-half of the maximum spread
  observed by the decision timestamp;
- acceptance requires less than one-half retracement and resistance-side depth
  below its pre-event baseline;
- rejection is flow/price opposition, or aligned flow with at-least-half
  retracement and resistance-side depth replenished to at least baseline;
- all mixed states abstain.

The boundaries 0, 0.5 and 1.0 are scale-free neutral/halfway/baseline reference
points. They are frozen ex ante and may not be relaxed after outcomes.

Cross-venue confirmation:
- Binance and Coinbase must independently produce the same classified state and
  the same aggressive-flow direction for the asset.
- disagreement or missing venue evidence => ABSTAIN.
- no price-level merging is permitted.

## Primary outcome

For each cross-venue-confirmed event-asset unit:

signed_forward_return_bps =
direction * log(mid_at_decision_plus_900s / mid_at_decision) * 10,000

The asset-level value is the equal-weight arithmetic mean of the two
venue-specific dimensionless signed returns. This is outcome aggregation, not
price-level merging.

Primary contrast:
mean(signed return | ACCEPTANCE)
minus
mean(signed return | REJECTION)

Inference:
- event-cluster bootstrap;
- 10,000 replicates;
- deterministic seed 1729;
- two-sided 95% percentile confidence interval.

Classification:
- lower CI > 0 => H02_SUPPORTED
- upper CI < 0 => H02_WRONG_SIGN
- otherwise => H02_NO_EDGE

No alternative horizon, threshold, subgroup or direction may rescue a failed
primary result.

## Sample gate and blind stopping rule

First outcome-reveal checkpoint requires:
- at least 10 eligible US_CPI events;
- at least 10 eligible US_EMPLOYMENT_SITUATION events;
- at least 6 eligible FOMC_STATEMENT events;
- at least 10 ACCEPTANCE event-asset units;
- at least 10 REJECTION event-asset units;
- at least 20 distinct official events contributing classified units.

State labels may be counted before outcome reveal because they use decision-time
information only.

If the family minima are reached but state minima are not, outcomes remain
unopened and collection continues through the remaining official 2027 events.
At the end of the frozen 2027 calendar:
- if state minima are satisfied, reveal once and run the frozen primary test;
- otherwise close as INSUFFICIENT_SAMPLE without threshold relaxation.

No repeated outcome looks are authorized.

## Economics

Economics tested = false for H02.

This phase tests the response-conditioned mechanism only. Fees, slippage,
latency, entries, exits, stops, sizing, PnL, paper trading and live trading are
outside this authority.

## Hard boundary

Historical internal macro outcomes already inspected are contaminated and cannot
select or validate this rule.

Target observation remains locked until:
1. complete official calendar manifest exists;
2. exact protocol and implementation fingerprints exist;
3. separate TARGET_OBSERVATION_OPEN authority binds them.

**FREEZE THE RULE -> OPEN THE TARGET -> OBSERVE ONCE.**
