# TOKEN-MIGRATION-FORCED-CONVERSION-BASIS-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-06
Status: FROZEN BEFORE ANY MARKET OUTCOME

### 1. Scientific question
For mandatory or economically binding token migrations / redenominations with a known deterministic OLD -> NEW conversion rule, does the legacy token's conversion-adjusted basis converge toward zero between the first immutable public signal and the frozen end boundary?

Primary mechanism:
legacy/new conversion-adjusted basis -> 0

This is NOT a directional token-return study.

### 2. Governance
- Research-only, fail-closed.
- Do not alter or merge main.
- No trading, orders, wallets, account reads, private/authenticated endpoints, exchange mutation, or spending.
- No post-outcome tuning.
- 2026 remains closed for possible later confirmation.
- This family must not rescue, reinterpret, or reuse results from other mines.
- AAVE-GOV-LT-FORCED-DELEVERAGING-001 is strictly separate and must not be modified or used here.
- One project / migration programme counts as one independent shock even if it spans several chains or exchanges.

### 3. Eligible calendar universe
Candidate migration programmes with effective migration mechanics during 2022-01-01 through 2025-12-31.

### 4. Required mechanism evidence for an eligible event
Each independent programme must have defensible public provenance for ALL of:
1. OLD token identity.
2. NEW token identity.
3. Fixed conversion ratio or deterministic conversion formula.
4. Identifiable migration / redemption mechanism, preferably an on-chain contract.
5. Immutable activation evidence: transaction hash and/or block number + timestamp when applicable.
6. Demonstrable retirement, deprecation, redemption, mandatory conversion, or another economically binding consequence for OLD.
7. A frozen end condition: on-chain deadline, contract termination boundary, protocol-effective boundary, or another immutable temporal condition.
8. Public source chronology sufficient to define the first immutable public moment at which ratio + mechanism were definitively known.
9. No candidate selection based on later price behaviour.

Reject:
- simple rebrands;
- ticker-only changes;
- cosmetic contract replacements;
- optional swaps with no demonstrated economic consequence;
- migrations whose OLD/NEW relationship or conversion economics cannot be proven.

### 5. Sample gate
Initial requirement: >=12 independent fully defensible migration programmes.

If the complete defensible 2022-2025 universe is demonstrated to contain fewer than 12:
VERDICT = INSUFFICIENT_SAMPLE.

If universe coverage / mechanism provenance cannot be demonstrated sufficiently to know whether the sample gate is met:
VERDICT = SOURCE_BLOCKED.

### 6. Source-gate market-data rule
During SOURCE GATE:
- DO NOT open, inspect, calculate, compare, or preview market outcome values.
- Only test historical-data availability, schema, venue identity, quote identity, timestamp coverage, and provenance.
- Prefer OLD and NEW historical prices from the same public venue and same quote asset over a contemporaneous interval.
- Venue / quote must be chosen before outcomes.
- Do not substitute venue, quote, token representation, or calendar window after observing outcomes.

A source probe may establish only:
- endpoint/file exists;
- requested symbol/pair exists;
- time coverage exists;
- granularity/schema is adequate;
- provenance is public and reproducible.

### 7. Source hierarchy
Preferred order:
1. on-chain contracts/events/transactions and verified source code;
2. official project/governance migration documentation;
3. official foundation / protocol announcements with immutable timestamps;
4. official exchange notices only as supplementary evidence for venue lifecycle / public historical-data availability.

Secondary aggregators may assist discovery but cannot by themselves prove eligibility.

### 8. No outcomes before second freeze
If and only if SOURCE_GATE_PASS is reached with >=12 fully defensible independent programmes and historical-data capability is proven for the frozen venue/quote policy, create a separate committed PRE-OUTCOME ANALYSIS FREEZE BEFORE opening any price values.

That second freeze must pre-specify:
- T_signal = first immutable public instant when ratio + mechanism are definitively public;
- T_end = frozen deadline / termination / effective boundary;
- exact conversion-adjusted basis formula;
- primary horizon;
- treatment/control logic;
- liquidity minimums;
- event clustering;
- fees/slippage;
- missingness;
- minimum sample;
- leave-one-out;
- calendar/project concentration;
- exact decision gates.

No horizon, venue, tokens, magnitude, sign, filters, or rules may be selected after outcome inspection.

### 9. Development rule
Development may be executed ONCE after the PRE-OUTCOME ANALYSIS FREEZE.

If the primary test fails:
- close immediately;
- no rescue;
- no subsets;
- no secondary resurrection.

### 10. Verdict taxonomy
Exclusive allowed verdicts:
- SOURCE_BLOCKED
- INSUFFICIENT_SAMPLE
- NO_EDGE_DISCOVERY
- SURVIVES_CONVERSION_DISCOVERY

If SURVIVES_CONVERSION_DISCOVERY:
- do not call it a diamond;
- do not open 2026;
- do not trade;
- stop and require a new confirmatory freeze.

### 11. Evidence retention
Persist:
- freeze documents and commit SHAs;
- candidate census and rejection reasons;
- contract addresses;
- transaction hashes;
- block numbers and timestamps;
- source URLs / source identity;
- source-coverage receipts;
- market-data schema/coverage probes without outcome values;
- workflow run IDs;
- exact metrics only after lawful outcome opening.

### 12. Frozen source-gate objective
Build the complete defensible 2022-2025 candidate census source-only and determine whether:
A) >=12 programmes pass all mechanism + provenance + historical-data-capability requirements => SOURCE_GATE_PASS and proceed to separate PRE-OUTCOME ANALYSIS FREEZE; or
B) complete defensible universe <12 => INSUFFICIENT_SAMPLE; or
C) completeness/provenance cannot be demonstrated => SOURCE_BLOCKED.

No market outcomes have been opened in this freeze.
