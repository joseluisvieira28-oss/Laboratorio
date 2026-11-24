# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — NEGATIVE MAP / DIAMOND DNA PRECHECK V0.1

Date: 2026-09-27
Status: NEW_ID / PRE-OUTCOME PRECHECK PASS / ZERO INHERITED CREDIT
Primary family: CREDIT
Secondary family: MICRO / FLOW
Parent source lineage: COMPOUND-INVENTORY-LIQUIDATION-001
Closed sibling: COMPOUND-INVENTORY-PERSISTENCE-001

## 1. Exact novelty claim

This lab does **not** retest whether residual Compound inventory predicts a later 24h bearish move.

The new primitive is the **realized disposal transaction itself**:
a `BuyCollateral` event in which Compound receives base token and releases previously seized collateral at the protocol storefront discount.

The causal actor chain is:
1. Compound protocol is the forced inventory seller;
2. a buyer/arbitrageur pays base token and receives discounted collateral;
3. the buyer/recipient may immediately route, hedge or resell that collateral.

Signal identity is therefore realized protocol disposal flow, not borrower distress, liquidation intensity, residual inventory state, or a reversed interpretation of the failed persistence child.

## 2. Negative Edge Map gate

Relevant exhausted/dense zones were checked.

- Generic price-only technical mining: not applicable.
- Generic BTC→ALT lead-lag: not applicable.
- Generic liquidation-event direction: duplicate-risk; this lab is narrower and requires the protocol's realized `BuyCollateral` sale event.
- COMPOUND-INVENTORY-PERSISTENCE-001: terminal exact 24h inventory-overhang child; no direction/horizon/subgroup rescue is inherited.
- DEFI-LIQUIDATION-SHOCK-001 / Historical Liquidations / Aave-style borrower stress: related family, but different observable and actor chain.

Verdict:
**MATERIALLY_NEW_MECHANISM_PASS**, conditional on source verification of the realized-disposal event and transaction path.

## 3. Diamond DNA precheck

Who pays / acts:
- protocol sells seized collateral to replenish reserves;
- buyer/arbitrageur supplies base token for discounted collateral;
- any downstream hedge/resale is performed by the buyer/recipient.

Direct point-in-time pressure observable:
- `BuyCollateral` block/tx/log position;
- buyer;
- collateral asset;
- base amount paid;
- collateral amount released;
- transaction/receipt path sufficient to infer the recipient where possible;
- same-transaction onward collateral transfer where observable.

Causal horizon:
- intentionally **not** selected from market outcomes.
- if a future economic contract is justified, it must use a short mechanism-matched horizon frozen after source-only adjudication and before protected prices are opened.

Friction headroom:
- unknown at M1/M2; no promotion credit.

Independent validation path:
- untouched 2025 market outcomes are reserved for a separately authorized protected test.
- 2023–2024 market outcomes from the failed sibling provide zero credit.

Execution/capacity route:
- not yet established; future work would require executable spot/perp quotes/depth independently of source evidence.

Strongest competing explanations:
1. discounted collateral can be absorbed by arbitrage inventory without immediate external selling;
2. same-transaction transfers may be routing/custody rather than market sale;
3. `BuyCollateral` may be reactive to already-realized price moves rather than predictive;
4. protocol sale size may be too small relative to market depth;
5. buyers may hedge on venues not visible in the Ethereum receipt.

## 4. Anti-rescue firewall

Forbidden:
- infer a long edge from the sibling's positive diagnostic;
- reuse the sibling's 24h horizon because it was already opened;
- choose assets after returns;
- lower costs after outcomes;
- use 2023–2024 sibling returns as confirmation;
- inspect protected 2025 market returns before a separate frozen economic protocol and explicit outcome-opening authority.

## 5. Advancement rule

Only source/mechanism work is authorized now.

A source PASS may justify a separate pre-outcome economic freeze.
It does not establish edge, direction, PnL, tier, capital authority or live-trading authority.
