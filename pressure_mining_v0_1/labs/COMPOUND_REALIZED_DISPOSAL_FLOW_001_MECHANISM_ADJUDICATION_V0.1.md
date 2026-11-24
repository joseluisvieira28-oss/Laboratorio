# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — MECHANISM ADJUDICATION V0.1

Date: 2026-09-27
Status: SOURCE_REALIZED_FLOW_PASS / MECHANISM_ESTABLISHED / ECONOMIC_FREEZE_JUSTIFIED — NO EDGE CLAIM

## 1. Question adjudicated

Can Compound III's realized seized-collateral disposal flow be reconstructed reproducibly from public point-in-time on-chain evidence strongly enough to justify a separately frozen economic experiment?

**Decision: YES for source/mechanism advancement. NO edge claim.**

## 2. Frozen source result

Canonical successful run:
- GitHub Actions run: 36347379578
- artifact: 10940652459
- artifact digest: sha256:69a44dc3c51f67e895fe0c29e2636a03064e7ab07a1820c6a1e4a06ca19b4a30
- receipt pre-self SHA256: e081b77cdeb6bef1a21fb1d6be2a5b4d5e9fb016fd2872eaf35eb823d6ccf707
- source status: SOURCE_REALIZED_FLOW_PASS

Historical source corpus, 2023-2024:
- 999 BuyCollateral logs;
- 899 unique transactions;
- 47 unique event buyers;
- 7 collateral assets.

Frozen deterministic receipt sample:
- 64/64 selected transactions usable = 100%;
- 68 BuyCollateral events in the selected transactions;
- 68/68 recipient paths inferred under the exact-amount collateral Transfer-from-Comet rule = 100%;
- 59/68 inferred recipients subsequently transferred the same collateral again in the same transaction = 86.7647%;
- event buyer == transaction sender: 0/68.

The onward-transfer statistic is source/mechanism evidence only. It is **not** automatically a DEX sale and carries no economic PASS threshold.

## 3. Why this is materially different from the terminal sibling

COMPOUND-INVENTORY-PERSISTENCE-001 tested:
> residual known protocol inventory after a liquidation block -> bearish collateral-vs-BTC response over exactly 24h.

It failed and remains terminal with no rescue.

COMPOUND-REALIZED-DISPOSAL-FLOW-001 measures:
> the protocol's actual BuyCollateral disposal event plus the recipient/routing path during that transaction.

This is a different state variable and different causal moment:
- inventory state versus realized disposal flow;
- hours/day-scale overhang hypothesis versus transaction/short-horizon flow;
- protocol inventory persistence versus buyer/recipient routing.

The new lab receives zero statistical credit from the sibling.

## 4. Contract-level semantic support

Compound Comet's official buyCollateral implementation:
1. transfers base token in from msg.sender;
2. quotes discounted collateral;
3. transfers collateral out to an explicit recipient;
4. emits BuyCollateral(msg.sender, asset, baseAmount, collateralAmount).

Therefore:
- the event buyer is the caller, not necessarily the ultimate collateral recipient;
- reconstructing the exact outbound collateral Transfer from Comet is the correct way to recover recipient routing;
- buyer != transaction sender or recipient is not by itself a data defect in composed/router transactions.

Compound's official liquidation-bot implementation also documents an operational path that purchases protocol collateral and may attempt an external sale, supporting the economic plausibility of buyer/arbitrage routing without proving any market-return edge.

## 5. Competing explanations that remain alive

1. Immediate onward transfer can be custody/router movement rather than market sale.
2. Arbitrageurs may warehouse or hedge elsewhere instead of creating net directional pressure at the observed venue.
3. BuyCollateral can be reactive to a price move that already occurred.
4. Any effect can be completed inside the Ethereum transaction/block before a post-block trade can enter.
5. Event size can be too small relative to CEX/DEX depth.
6. Cross-venue arbitrage can neutralize pressure quickly.
7. Wrapper assets can map imperfectly to liquid CEX underlyings.

These are economic-test questions, not source-gate failures.

## 6. Advancement decision

**ECONOMIC_FREEZE_JUSTIFIED**, subject to:
- source-only census of untouched 2025 predictor events;
- a prospectively frozen, short-horizon economic contract;
- explicit authority before opening protected 2025 market outcomes.

No direction or horizon is selected by this adjudication.

## 7. Firewall

market_prices_opened=false
returns_computed=false
pnl_computed=false
protected_2025_market_outcomes_opened=false
edge_claim=false
promotion_claim=false
tier_claim=false
live_trading=false
orders=false
capital=false
main_merge=false
post_outcome_tuning=false
inverse_rescue=false
