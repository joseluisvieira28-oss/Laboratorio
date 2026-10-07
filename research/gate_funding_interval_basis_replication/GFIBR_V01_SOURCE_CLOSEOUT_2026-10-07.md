# GATE-FUNDING-INTERVAL-BASIS-REPLICATION-001
## V0.1 SOURCE CLOSEOUT
Date: 2026-10-07
Status: EXTERNAL_SOURCE_BLOCKED — NO MARKET OUTCOMES OPENED

### What passed
- Official Gate Fees archive endpoint was resolved and enumerated: 112 / 112 rows.
- 84 rows fall inside the 2023-2025 calendar.
- 69 official funding-interval/frequency candidates were identified.
- Candidate years represented: 2024 and 2025.
- Official announcement pages expose exact publication/effective timestamps for many candidates.
- Gate public futures funding endpoint exists and does not require authentication.
- Gate public mark/index candle endpoints exist and do not require authentication.

### Blocking facts
1. The official Fees category does not cross before 2023 under the frozen source-completeness rule.
2. The Gate historical funding endpoint rejects historical start times older than 180 days with INVALID_PARAM_VALUE: from time exceeds 180-day limit.
3. The batch funding endpoint returns only recent timestamps and does not recover the 2024-2025 settlement cadence needed by the frozen V0.1 event rule.
4. Therefore the required pre/post cadence verification for 2024-2025 cannot be demonstrated under the frozen protocol.

### Verdict
EXTERNAL_SOURCE_BLOCKED

This is not NO_EDGE.
No mark-price, index-price, funding-rate r, return, basis, or PnL value was opened.

### Governance
- no threshold relaxation;
- no source-rule substitution after seeing source census;
- no main merge;
- no trading/private endpoints/account reads;
- no post-outcome tuning.

A future Gate family would require a genuinely new pre-outcome source design, not a rescue of V0.1.
