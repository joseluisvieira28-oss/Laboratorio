# MEXC-NVDA-SOURCE-GATE-002 — CLOSEOUT

Date: 2026-10-05

## Verdict table

| Gate | Verdict | Decision |
|---|---|---|
| A — historical MEXC NVDA index architecture | SOURCE_PARTIAL | Broad regimes proven; exact ONDO-to-current transition, weights and instrument mapping unresolved |
| B — free/public timestamped Nasdaq NVDA reference | SOURCE_BLOCKED | Official scientifically adequate feeds are premium/subscription/authorized; no defensible free/public equivalent established |
| C — NVDA share ↔ NVDAON/NVDAX mapping | SOURCE_PARTIAL | Economic mechanics proven; NVDAX has public multiplier/corporate-action API, but full historical NVDAon adjustment-factor reconstruction not established |
| Global H1 causal chain | SOURCE_BLOCKED_FINAL | Do not start the 30-day H1 collector under current public/free rules |

## Key findings

1. A real historical MEXC source transition is proven:
   - launch: stock-price anchored;
   - from 2025-09-20: ONDO U.S. stock-token spot prices adopted as Stock Futures index components.

2. The current archived public MEXC contract/detail snapshot is no longer simply the 2025 ONDO description. It reports a multi-source indexOrigin list (BINANCE_FUTURE, BITGET_FUTURE, BINANCETICKER, PYTH, KAIKO). The exact transition date and weights were not found in official public documentation.

3. Nasdaq has exactly the data needed scientifically:
   - Basic for real-time BBO/Last Sale;
   - Historical TotalView-ITCH for tick-by-tick historical order/trade data.
   But these are commercial/entitled products, not a defensible free/public source under this mission.

4. Token normalization is not raw-price equality:
   - NVDAon is total-return exposure with reinvested dividends and corporate-action adjustments;
   - NVDAx/xStocks uses rebasing/multiplier mechanics and exposes public corporate-action/multiplier endpoints.

## Scientific decision

Do NOT:
- substitute an unverified free web chart for Nasdaq timestamps;
- infer the missing MEXC transition date;
- assume NVDAON == one raw NVDA share through time;
- launch 30 days of MEXC/token collection and pretend it resolves the missing upstream Nasdaq source;
- reopen or retune Last↔Fair / Last↔Index thresholds from MEXC_NVDA_001.

The forward collector from MEXC_NVDA_001 may remain as dormant infrastructure, but H1/H3 causal forward activation is not authorized by this source gate.

## What would reopen the mine

Any one of the following could justify a new source-gate revision:
1. a public/official MEXC record identifying the current NVDA index-source migration date and constituent mapping/weights;
2. legitimate access to Nasdaq Basic/Historical TotalView-ITCH or another provenance-verified feed with equivalent timing semantics;
3. a public historical NVDAon Shares-Per-Token / adjustment-factor series covering the intended test window.

Until then:

**MEXC-NVDA causal stock-to-token-to-future mine = SOURCE_BLOCKED_FINAL under public/free constraints.**
