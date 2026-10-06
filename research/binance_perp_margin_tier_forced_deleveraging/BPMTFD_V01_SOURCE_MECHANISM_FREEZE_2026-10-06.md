# BINANCE-PERP-MARGIN-TIER-FORCED-DELEVERAGING-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-06
Status: FROZEN BEFORE ANY NEW-FAMILY MARKET OUTCOME

### 1. Economic question
When Binance Futures tightens leverage/margin tiers on an existing USDⓈ-M USDT perpetual contract and explicitly states that already-open positions are affected, does the mechanically higher margin burden / lower leverage capacity create a short-lived increase in contract-specific volatility and trading activity around the effective timestamp?

Primary mechanism:
margin-tier tightening -> some existing positions require more margin / lower admissible leverage -> involuntary position adjustment or liquidation risk rises -> trading pressure/volatility around the effective time increases.

This is NOT a directional-return hypothesis. Longs and shorts can both be affected.

### 2. Distinction from prior family
This family is scientifically distinct from `BINANCE-COLLATERAL-HAIRCUT-001`.
The prior family changed Portfolio Margin collateral valuation and tested signed 24h relative returns.
This family studies USDⓈ-M perpetual leverage/maintenance-margin tier tightening and a direction-agnostic intraday volatility/activity mechanism.
No prior collateral-haircut outcome may be used to choose events, horizons, signs, assets, controls, or thresholds here.

### 3. Governance
- Research-only; fail-closed.
- Do not alter or merge main.
- No trading, orders, wallets, account reads, private/authenticated endpoints, exchange mutation, or spending.
- No post-outcome tuning.
- 2026 remains CLOSED.
- No use of results from other mines to rescue this family.
- Source gate must complete before any new-family market outcome is opened.

### 4. Calendar/source universe
Frozen official-announcement universe:
- 2023-01-01 through 2025-12-31.
- 2026 excluded and locked.
- Source authority: official Binance Support/Announcement article pages and official public Binance historical-data documentation.
- Discovery helpers (search engines/Telegram announcement mirror) may locate official article codes, but eligibility requires the official Binance article itself.

### 5. Eligible shock definition
An independent shock is one official Binance article + one effective timestamp.
Multiple affected contracts sharing that article/effective time belong to the same shock cluster.

An asset-event qualifies only if ALL are true before market outcomes:
1. USDⓈ-M USDT perpetual contract is explicitly identified;
2. article publication timestamp is before the effective timestamp;
3. exact effective UTC timestamp is explicit;
4. previous and new leverage/margin tier tables are publicly available;
5. article explicitly states that existing positions opened before the update WILL be affected, or equivalently warns pre-existing positions to adjust to avoid potential liquidation;
6. the change is a tightening for that contract: at least one economically relevant tier has higher maintenance margin rate, lower maximum leverage, or a lower notional boundary at a given leverage such that position capacity is reduced;
7. no concurrent contract delisting/automatic settlement;
8. no concurrent funding-rate settlement-frequency or capped-funding-multiplier change in the same article/event for that contract;
9. no token migration/rebrand/spot delisting contaminant at the same effective window;
10. public historical USDⓈ-M futures 1-minute market data capability can be proven without reading outcome values.

Reject:
- changes where existing positions are explicitly NOT affected;
- pure leverage loosening;
- initial listing/new-contract tier setup;
- COIN-M only;
- BUSD-only contracts;
- delisting/settlement bundles;
- funding-parameter bundles;
- events selected because later volatility/returns looked large.

### 6. Source sample gate
SOURCE_GATE_PASS requires:
- >=12 independent eligible shock clusters;
- >=20 eligible asset-events;
- >=8 unique contracts/assets;
- no single effective-date cluster >35% of eligible asset-events;
- at least two calendar years represented;
- historical 1-minute futures data capability proven outcome-blind for every eligible asset-event.

If the mechanically enumerated official universe is complete and fails these minimums:
VERDICT = INSUFFICIENT_SAMPLE.

If official-universe enumeration/provenance cannot be demonstrated:
VERDICT = SOURCE_BLOCKED.

### 7. Outcome-blind market-data capability
Allowed during source gate:
- file/endpoint existence;
- symbol identity;
- interval/granularity;
- archive path;
- HTTP status/HEAD metadata;
- ZIP member names;
- row counts only;
- schema/field names.

Forbidden:
- open/high/low/close values;
- trade prices;
- returns;
- realized volatility;
- volumes/notionals;
- basis;
- funding values;
- liquidation values;
- PnL.

Frozen market source:
- Binance Public Data / Data Vision USDⓈ-M futures for the exact contract.
- Preferred primary archive: 1-minute `klines` around event windows.
- 1-minute `trades` or `aggTrades` may be capability-probed now, but cannot become primary after outcomes unless separately frozen before opening values.

### 8. Pre-outcome analysis gate
If SOURCE_GATE_PASS, create and commit a separate PRE-OUTCOME ANALYSIS FREEZE before any market value is opened.

That freeze must specify exactly:
- event window and timestamp alignment;
- volatility statistic;
- activity statistic;
- primary horizon;
- pre-event baseline;
- unaffected-contract control construction;
- treatment aggregation at shock-cluster level;
- liquidity/missingness rules;
- clustering;
- concentration gates;
- exact statistical tests;
- fees/slippage only if a later tradeability diagnostic is scientifically justified;
- exact verdict gates.

No horizon/metric/control/asset selection after outcome access.

### 9. Development rule
Development may run ONCE after the second freeze.
A purely technical deterministic bug may be repaired only if scientific rules remain unchanged and the broken run is preserved.

### 10. Verdict taxonomy
Source stage:
- SOURCE_BLOCKED
- INSUFFICIENT_SAMPLE
- SOURCE_GATE_PASS

Development stage:
- NO_EDGE_DISCOVERY
- SURVIVES_MARGIN_TIER_DISCOVERY

Primary failure closes the family.
No rescue subsets, no alternate horizon resurrection, no directional inversion.

If SURVIVES:
- do not call it a diamond;
- do not trade;
- do not open 2026;
- stop and require a new confirmatory freeze.

### 11. Evidence retention
Persist:
- official article codes/URLs;
- publication/effective timestamps;
- contract identities;
- old/new tier evidence;
- affected-position wording;
- exclusion reason;
- source coverage receipts;
- workflow run IDs;
- artifact hashes;
- exact metrics only after lawful outcome opening.

### 12. Outcome-access declaration
No market price, return, volatility, volume, trade, basis, funding, liquidation, or PnL outcome from this new family has been opened at the time of this freeze.
