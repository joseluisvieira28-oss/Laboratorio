# PREDICTION-SETTLEMENT-RV-001 — POLYMARKET FEE SOURCE RECEIPT V0.1

Date: 2026-09-27
Status: SOURCE_PROVENANCE / RESEARCH_ONLY
Lab: PREDICTION-SETTLEMENT-RV-001

## Deterministic market probe

Source-readiness run:
36339649202

Artifact:
10938113181

Artifact ZIP SHA256:
7b8048bd901458229892f5e43d9874426671e77705b34417ef362450449e949f

Receipt JSON SHA256:
d5dbcc7f0bcbe0d27dcbd3bd4a03311ce234a8459d08495cac1d1267cabce176

Deterministic matched pair used for fee metadata only:
- resolution: 2026-09-27T19:00:00Z
- nominal strike: 82600
- Polymarket market ID: 5043339
- Kalshi ticker: KXBTCD-26SEP2715-T82599.99

## Polymarket market metadata

Exact market metadata exposed:
- feesEnabled = true
- feeType = crypto_fees_v2
- feeSchedule.rate = 0.07
- feeSchedule.exponent = 1
- feeSchedule.rebateRate = 0.2
- feeSchedule.takerOnly = true
- makerBaseFee = 1000
- takerBaseFee = 1000

Market metadata SHA256:
9891c9dd9d5157ce329fab01280fb5b36c5a50c1618b36778ef979856d8f0447

## External documentation cross-check

Current Polymarket Trading Fees documentation describes crypto markets as fee-enabled for takers under:
fee = C × feeRate × p × (1-p)

and states makers are not charged trading fees.

The later economic protocol must use the exact per-market fee metadata captured at each observation, not assume every future market has the same schedule.

## Fail-closed rule

Any missing or changed fee metadata at an eligible matched market blocks that observation from later economics unless the change is prospectively reconciled.

No PnL or package economics are authorized by this receipt.
