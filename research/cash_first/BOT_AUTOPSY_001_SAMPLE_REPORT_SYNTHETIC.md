# CRYPTO BOT AUTOPSY — SAMPLE REPORT (100% SYNTHETIC)

**Customer/account:** DEMO (no real customer's positions)  
**Exchange:** MEXC Futures (illustrative only)  
**Scope:** three hypothetical completed round-trip positions, each roughly USDT 500 traded notional  
**Purpose:** show the type of deliverable, not claim audited exchange results.

## 1 — P&L ledger and cost waterfall

Signed funding: + = credit, - = debit.

| Trade (dummy ID) | Gross close P&L | Entry fee | Exit fee | Signed funding | Net P&L |
|---|---:|---:|---:|---:|---:|
| DEMO-001 | +1.20 | 0.40 | 0.40 | -0.05 | +0.35 |
| DEMO-002 | +0.50 | 0.40 | 0.40 | -0.02 | -0.32 |
| DEMO-003 | -1.00 | 0.40 | 0.40 | +0.05 | -1.75 |
| **TOTAL (USDT)** | **+0.70** | **1.20** | **1.20** | **-0.02** | **-1.72** |

**Reconciliation:** NET = Gross close P&L − entry fees − exit fees + signed funding.  
= 0.70 − 1.20 − 1.20 − 0.02 = **−1.72 USDT**.

The example is constructed only to illustrate that a positive gross P&L can correspond to negative net P&L. This cannot be interpreted as a real trade outcome or a measure of any live algorithm's profitability. Venue fees and real fills must come from the customer export.

## 2 — Three prioritized issues

| Priority | Finding | Evidence needed | Action |
|---|---|---|---|
| P0 | Gross-versus-net reconciliation difference | Exact exchange fill fee receipts, unique position IDs, UTC stamps, funding records | Reconcile once; ensure platform realized PnL does NOT already include charges before subtracting |
| P1 | Fees are large relative to small gross returns | Effective fee bps on executed entry/exit notional (not nominal fixed fee assumptions) | Evaluate a truly executable cheaper route with maker-fill probability and adverse-selection risk |
| P2 | Market orders may include invisible spread/slippage | Executable BBO snapshots stamped before both requests; order fill prices | Quantify paid spread and slippage; do not add a second slippage penalty to realized fill PnL |

## 3 — Audit quality and boundaries

- **Data integrity:** SYNTHETIC (cannot certify any real user or exchange).
- **Independent profit claim:** NONE.
- **API credentials requested:** NONE; never request secrets or wallet data.
- **Cash flow and tax returns:** not covered.
- **What client would receive:** audited net result or EVIDENCE_INCOMPLETE, exact row lineage, fee/funding breakdown and prioritized practical actions.
- **Nothing sold, no customers acquired, no outreach performed** by creating this sample.
