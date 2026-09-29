# INFORMATION-PROPAGATION-GRAPH-001

Status: SOURCE GATE / PRE-OUTCOME FREEZE
Date opened: 2026-09-24
Branch: information-propagation-graph-001-source-gate-v0.1

## Mission

Test whether information propagates across crypto market surfaces in a reproducible sequence before the target price fully reprices.

This is NOT an indicator-combination exercise and NOT a live-trading strategy. The research object is the temporal graph itself:

OPTIONS -> DERIVATIVES -> MICROSTRUCTURE -> SPOT -> DEFI/ONCHAIN/EXPECTATIONS

## Governance

- Research-only.
- No live trading, order submission, exchange mutation, wallet mutation or capital deployment.
- No merge to main without explicit operator authorization.
- No post-outcome feature invention or threshold tuning.
- Sources must be classified before outcomes are inspected.
- Every event MUST preserve source-native timestamp when supplied, local receive timestamp, source identity, instrument/entity identity, and sequence/gap evidence when available.
- Missing or ambiguous timestamp provenance => FAIL_CLOSED for causal/lead-lag claims.
- Live-only sources are labelled FORWARD_ONLY and may not be silently backfilled with post-hoc snapshots.
- Historical data with mutable semantics must carry version/provenance evidence.

## Initial research questions (frozen before outcomes)

1. Do changes in BTC option volatility/skew/greeks systematically lead changes in perp basis/funding/OI and then spot?
2. Do perp/microstructure shocks lead spot only in specific state combinations, rather than unconditionally?
3. Does a cross-source state transition contain incremental information beyond each constituent stream alone?
4. Are there reproducible propagation paths on 1s-15m horizons that survive costs and out-of-sample testing?
5. Are there forward-only information surfaces (mempool, oracle stress, cross-chain transfer, prediction-market repricing) that justify dedicated child labs?

## First-stage scope

Core, historically testable candidate:
- Binance BTC spot/perp market microstructure.
- Binance funding/basis/open-interest where timestamp provenance is defensible.
- Deribit BTC options ticker/IV/greeks/DVOL/trades.
- Optional Polymarket expectation streams only when a market can be mapped ex ante to a crypto-relevant event.

Forward-only child gates:
- Ethereum mempool.
- Aave liquidation convexity / health-factor distribution.
- Cross-chain USDC CCTP flow.
- Oracle / sequencer divergence.

## Outcome labels

- SOURCE_PASS
- SOURCE_PARTIAL
- SOURCE_BLOCKED
- FORWARD_ONLY
- NO_EDGE
- SURVIVES_DISCOVERY
- SURVIVES_OOS
- BLOCKED

No "diamond" or promotion language is valid until the applicable scientific gates are actually passed.
