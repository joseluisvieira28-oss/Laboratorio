# L2R-CROSSVENUE-001 — PRE-DISCOVERY AUTHORITY V0.1

Date: 2026-09-30
Status: **FROZEN_PRE_OUTCOME / SOURCE-AND-PARENT-MATERIALIZATION ONLY**

Parent mechanism: `L2-RESILIENCY-001` = independently validated mechanism.
This is a materially new child. It does not reopen or rescue any closed standalone execution child or ETF-CME overlay.

## Scientific question

Does a Hyperliquid BTC L2 sweep/replenishment state contain short-horizon information that is subsequently expressed in **Binance BTCUSDT spot executed trades**?

This is specifically an event-conditioned cross-venue information-transmission test. It is distinct from `CROSS-VENUE-PRICE-DISCOVERY-001`, which tests symmetric venue-level price innovation leadership on a fixed 1-second grid.

## Discovery / holdout boundary

- Discovery: calendar 2024 only.
- 2025: protected holdout for this LAB_ID; do not access Binance 2025 outcomes or construct cross-venue 2025 responses before a 2024 Discovery verdict.
- 2026: forbidden.
- No live data is required.

The underlying 2024 L2 parent outcomes are already historically exposed. Therefore any result must be labeled **new-mechanism / previously-exposed-parent-source**, not virgin-source Discovery.

## Frozen parent construction

Inherit without modification from `L2-RESILIENCY-001`:
- BTC Hyperliquid l2Book source;
- canonical envelope/payload clock normalization;
- ambiguous both-side sweeps excluded;
- ASK-consumed direction = +1;
- BID-consumed direction = -1;
- same six cells:
  - R1_Y5
  - R1_Y15
  - R1_Y60
  - R5_Y15
  - R5_Y60
  - R15_Y60
- replenishment ratio = same-side top5 depth at R / immediately pre-sweep same-side top5 depth;
- WEAK iff RR < 1.0;
- STRONG iff RR >= 1.0;
- no cross-segment lookup.

No parent cell, direction, threshold or horizon may be changed using Binance outcomes.

## External venue / source

External venue is frozen to:
- Binance spot
- BTCUSDT
- official historical `aggTrades` archive from `data.binance.vision`.

Do not substitute futures, Coinbase, Bybit, MEXC or another venue under this LAB_ID.

## Outcome construction — not yet authorized

Actual price-response construction is not authorized by this source/materialization authority.

Before Discovery outcomes may be opened:
1. parent event anchors required by the six cells must be materialized from a byte-authoritative parent artifact or regenerated from the exact preserved 2024 Hyperliquid corpus;
2. a Binance timestamp/cadence preflight must be run without computing returns or signed responses;
3. the external lookup tolerance must then be frozen prospectively from source cadence only;
4. exact runner bytes and support gates must be hash-locked;
5. a separate one-shot Discovery authority must exist.

## Intended primary contrast

Subject to the future timing freeze, the scientific target is:

`BINANCE_SIGNED_RESPONSE = L2_EVENT_DIRECTION * 10000 * (P_external_Y / P_external_R - 1)`

Primary information contrast per frozen cell:
`mean(BINANCE_SIGNED_RESPONSE | WEAK) - mean(BINANCE_SIGNED_RESPONSE | STRONG)`

This is an information-transmission diagnostic, not PnL.

## Support structure to freeze before outcome opening

The later one-shot protocol must use the same robustness philosophy as the parent:
- six fixed cells;
- global contrast > 0;
- bootstrap 95% lower bound > 0;
- >=4/6 positive cells;
- each R family has >=1 positive cell;
- no best-cell selection after outcomes.

Exact minimum sample and source timing coverage requirements must be frozen before Binance price values are used for responses.

## Firewalls

No:
- Binance 2025/2026 cross-venue outcomes;
- trading PnL, fees, Sharpe, leverage or position sizing in Discovery;
- orders;
- live trading;
- wallets;
- exchange mutation;
- main merge;
- threshold/cell/horizon rescue;
- use of the old symmetric CVPD-001 result as an outcome for this lab.

