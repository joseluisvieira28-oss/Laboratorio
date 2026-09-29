# DEFI-LIQUIDATION-SHOCK-001 — SIGNED FLOW ROUTE TRIAGE CLOSEOUT V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Scope: SOURCE-ONLY TRIAGE / NO MARKET OUTCOMES

## Purpose

Prevent source-negative protocol/classes from remaining operationally ambiguous while prioritizing the
routes that actually show evidence of external market execution.

## Kamino — November 2023 partition

Canonical source:
- run 36525352386
- artifact dls-signed-flow-kamino-same-tx-census-v01
- artifact ID 11013848904
- digest sha256:e6bb0c3f7eb62a301c104fad00ccfba5e7647288dec8e322bcbefde82d96c447

Result:
- classification KAMINO_SAME_TX_PROGRAM_PARTITION_PASS
- population = 49
- complete = 49
- identity conflicts = 0
- market_direction_proven = false

Programs observed after liquidation across the full frozen partition:
- Token Program
- Kamino Lending
- Kamino Farms

No post-liquidation Jupiter/DEX market route was observed in this full 49-event partition.

Triage classification:
KAMINO_202311_POST_LIQ_MARKET_ROUTE_NEGATIVE

Meaning:
this exact partition is not authorized for signed external-market-flow labeling.

This is not a claim that all Kamino history is globally route-negative.

## Save11 — July 2024 frozen sample

Canonical source:
- run 36525225230
- artifact dls-signed-flow-save11-same-tx-sample-v01
- artifact ID 11013823848
- digest sha256:24323d1a8e72d649ece05d958e99808087daa451f030c0b73346c8dfcd9a03a5

Result:
- classification SAVE11_SAME_TX_PROGRAM_SAMPLE_PASS
- frozen sample = 64 / population 1,572
- complete = 64
- identity conflicts = 0
- market_direction_proven = false

Programs observed after liquidation in the frozen sample:
- Token Program: 320 occurrences
- System Program: 1 occurrence

No post-liquidation DEX/Jupiter route was observed in the frozen sample.

Triage classification:
SAVE11_202407_SAMPLE_POST_LIQ_MARKET_ROUTE_NEGATIVE

Meaning:
deprioritize this route for signed-flow work.

Because this is a 64-event sample, it is NOT a global source block for all 1,572 events or all Save11 history.

## Active source priorities

### Priority 1 — Marginfi + Jupiter

December-2023 source-only discovery sample:
- run 36531548552
- 64 / 64 exact transactions complete
- identity conflicts = 0
- 45 / 64 contain Jupiter V6 after the canonical Marginfi liquidation instruction

This is the strongest current candidate for a source-proven post-liquidation external market route.

Active validation:
MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_V0_1

### Priority 2 — Drift liquidate_perp_with_fill

Temporal source semantics:
DRIFT_WITH_FILL_TEMPORAL_SOURCE_AUTHORITY_PASS

The source implementation contains explicit realized market fills and a pre-frozen decoder/counterparty rule.

Active source census:
public 2024-07-30 through 2024-12-31 window, transport-sharded V0.2.

## Firewall

prices=false
returns=false
pnl=false
market_direction_outcomes=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
