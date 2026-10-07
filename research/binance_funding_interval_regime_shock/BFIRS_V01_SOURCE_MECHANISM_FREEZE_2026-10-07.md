# BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY NEW-FAMILY MARKET OUTCOME

### 1. Economic question
When Binance Futures increases the funding settlement frequency of an already-live USDⓈ-M USDT perpetual contract at a pre-announced effective timestamp, does the predictable change in carry cadence create a reproducible premium/basis normalization pattern around the regime transition?

This family is about a funding-interval regime change on existing contracts. It is NOT:
- a generic extreme-funding fade;
- a margin-tier shock;
- a delisting/listing event;
- a directional price-return hypothesis chosen from later outcomes.

### 2. Distinction from prior funding research
This family is scientifically distinct from FUNDING-SHOCK-RESET-001.

FUNDING-SHOCK-RESET-001:
- signal = extreme settled funding + aligned pre-settlement price momentum;
- BTCUSDT/ETHUSDT only;
- event = ordinary funding settlement;
- hypothesis = post-settlement fade.

BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001:
- event = official Binance rule/specification change to settlement cadence on existing contracts;
- multi-asset;
- exact announcement and effective timestamps required;
- hypothesis concerns premium/basis behavior around a known regime transition.

Opened outcomes from FUNDING-SHOCK-RESET-001 MUST NOT be used to choose thresholds, horizons, controls, signs, or subsets here.

### 3. Governance
- Research-only; fail-closed.
- Do not alter or merge main.
- No trading, orders, wallets, account reads, private/authenticated endpoints, exchange mutation, or spending.
- No post-outcome tuning.
- 2026 outcomes remain CLOSED.
- Source gate must complete before any premium, funding, price, return, volume, liquidation, OI or PnL value is opened.

### 4. Frozen source universe
Official announcement calendar:
- 2023-01-01 through 2025-12-31 inclusive.
- 2026 excluded and locked.

Authority:
- official Binance Support/Announcement article pages;
- official Binance public Data Vision archive capability.

Discovery may use Binance public announcement catalog endpoints only.
Eligibility requires the official article content itself.

### 5. Eligible event definition
An independent shock cluster is:
official article code + one exact effective UTC timestamp + one interval transition.

An asset-event qualifies only if ALL are true before market outcomes:
1. USDⓈ-M USDT perpetual contract is explicitly identified;
2. contract was already live before the announced regime change;
3. article publication timestamp precedes the effective timestamp;
4. exact effective UTC timestamp is explicit;
5. old settlement interval and new settlement interval are both explicit;
6. new interval is SHORTER than old interval (for example 8h -> 4h, 4h -> 2h, 8h -> 2h);
7. the change applies to that named contract, not merely to a future automatic rule with no fixed per-contract effective event;
8. event is not an initial listing/launch specification;
9. event is not a delisting/automatic-settlement bundle;
10. public Binance Data Vision capability exists for BOTH:
   - monthly USDⓈ-M 1-minute premiumIndexKlines for the event month;
   - monthly USDⓈ-M fundingRate archive for the event month.

Multiple affected contracts sharing one article/effective timestamp/transition belong to one shock cluster.

### 6. Explicit exclusions
Reject:
- new perpetual listings where the interval is merely part of launch terms;
- interval lengthening/reversion events (e.g. 1h -> 4h) in V0.1;
- generic dynamic-rule announcements with no fixed named-contract transition timestamp;
- 2026 events/outcomes;
- COIN-M only;
- BUSD-only contracts;
- delisting/settlement bundles;
- events selected because later premium/funding/returns looked large.

### 7. Source sample gate
SOURCE_GATE_PASS requires ALL:
- >=12 independent eligible shock clusters;
- >=20 eligible asset-events;
- >=8 unique contracts;
- >=2 calendar years represented;
- no single shock cluster >35% of eligible asset-events;
- premiumIndexKlines capability proven for every eligible asset-event;
- fundingRate archive capability proven for every eligible asset-event.

If mechanically enumerated official universe is complete but fails minimums:
VERDICT = INSUFFICIENT_SAMPLE.

If official-universe enumeration or provenance cannot be demonstrated:
VERDICT = SOURCE_BLOCKED.

### 8. Outcome-blind capability rules
Allowed now:
- article titles/codes;
- publication/effective timestamps;
- named contracts;
- old/new interval hours;
- archive URL/path existence;
- HTTP status/HEAD metadata;
- ZIP member names only if required;
- row counts only if required;
- schema/field names.

Forbidden now:
- premium index values;
- funding rate values;
- prices/returns;
- volumes;
- volatility;
- basis magnitudes;
- liquidation/OI/PnL values.

### 9. Pre-outcome analysis gate
If SOURCE_GATE_PASS, create and commit a separate PRE-OUTCOME ANALYSIS FREEZE before opening any market value.

That freeze must specify exactly:
- event alignment;
- primary premium/basis statistic;
- how funding sign is used, if used;
- primary horizon;
- pre-event baseline;
- contemporaneous controls;
- treatment aggregation at shock-cluster level;
- missingness/liquidity rules;
- concentration gates;
- exact statistical test;
- exact economic-effect floor;
- exact verdict gates.

No metric/horizon/control/sign/asset selection after outcome access.

### 10. Development rule
Development may run ONCE after the second freeze.
Purely technical deterministic bugs may be repaired only if the scientific freeze remains unchanged and the broken run is preserved.

### 11. Verdict taxonomy
Source stage:
- SOURCE_BLOCKED
- INSUFFICIENT_SAMPLE
- SOURCE_GATE_PASS

Development stage:
- NO_EDGE_DISCOVERY
- SURVIVES_FUNDING_INTERVAL_DISCOVERY

Primary failure closes the family.
No rescue subsets, alternate horizons, sign inversions, or threshold relaxation.

If SURVIVES:
- do not call it a diamond;
- do not trade;
- do not open 2026;
- require a new confirmatory freeze.

### 12. Outcome-access declaration
No market premium, funding, price, return, volume, volatility, liquidation, OI or PnL outcome from this family has been opened at the time of this freeze.
