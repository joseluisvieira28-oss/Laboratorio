# CEX-TRANSFER-RAIL-RECOVERY-BASIS-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-06
Status: FROZEN BEFORE ANY MARKET OUTCOME

### 1. Economic question
When a centralized exchange temporarily loses transfer functionality for a cryptoasset/network while spot trading on that exchange remains available, does restoration of the transfer rail cause the affected venue's price basis versus unaffected reference venues to converge toward zero?

Primary mechanism:
transfer rail constrained -> cross-venue arbitrage physically impaired -> venue-specific basis can persist
transfer rail restored -> arbitrage channel restored -> |affected/reference basis| should contract

This is NOT a directional return study.

### 2. Governance
- Research-only; fail-closed.
- Do not alter or merge main.
- No trading, orders, wallets, account reads, private/authenticated endpoints, exchange mutation, or spending.
- No post-outcome tuning.
- 2026 remains closed.
- Do not reuse/rescue results from other mines.
- One exchange status incident/outage = one independent shock even if multiple assets/networks are listed.
- Planned maintenance and unplanned incidents are distinct strata; primary analysis uses only unplanned incidents unless both are frozen separately before outcomes.
- During SOURCE GATE do not open, inspect, calculate, compare, or preview any historical price, return, spread, basis, volume, or liquidity value.

### 3. Initial source frame
Primary affected venue for V0.1: Coinbase / Coinbase Exchange, because:
- public status incident archive exposes incident creation/update/resolution timestamps;
- incidents can explicitly state sends/receives or blockchain transfers are degraded while buys/sells/trading remain available;
- Coinbase Exchange exposes public historical candle endpoints suitable for outcome-blind schema/coverage probing.

Reference venues to be tested outcome-blind for data availability:
- Binance spot public historical data;
- OKX public market-history endpoint or downloadable public history if adequate.

If a reference venue cannot be proven before outcomes, it is removed now and not substituted after outcomes.

### 4. Calendar universe
Incident start/resolution dates from 2022-01-01 through 2025-12-31.
2026 is locked and excluded.

### 5. Eligible incident requirements
An incident qualifies only if ALL are supported by public contemporaneous/archived sources:
1. affected asset/network identity is explicit or mechanically enumerable from the incident;
2. transfer rail (send/receive, deposit/withdrawal, blockchain transfer) is degraded or unavailable;
3. spot trading/buys/sells on affected venue remained available, either explicitly stated in incident updates or demonstrably operational in the venue component status without relying on price outcomes;
4. public immutable/archived incident timestamp for disruption;
5. public immutable/archived incident timestamp for recovery/resolution;
6. transfer functionality is explicitly stated to be restored/operational at recovery;
7. no contemporaneous delisting, token migration, chain swap, trading halt, or market-wide venue outage that destroys the transfer-rail interpretation;
8. affected asset has a frozen, same-quote spot market on Coinbase and on at least one pre-specified unaffected reference venue over the event window;
9. historical data schema/coverage can be proven without opening outcome values.

Reject:
- trading outages;
- whole-site outages where trading status is ambiguous;
- wallet maintenance with no proof that trading remained available;
- pure fiat-payment incidents;
- incidents with no resolved timestamp;
- incidents where the affected chain/token identity is ambiguous;
- planned maintenance from the primary unplanned-incidents analysis;
- any event selected because its later basis looked large.

### 6. Sample gate
SOURCE_GATE_PASS requires:
- >=12 independent eligible unplanned incidents;
- spanning >=4 unique cryptoassets/networks;
- no single asset/network >40% of incidents;
- all with outcome-blind historical-data capability proven on affected venue and at least one frozen reference venue.

If the complete Coinbase status archive in 2022-2025 yields <12 eligible incidents under these frozen rules:
VERDICT = INSUFFICIENT_SAMPLE.

If the archive cannot be enumerated/retrieved sufficiently to establish the eligible universe or provenance:
VERDICT = SOURCE_BLOCKED.

### 7. Outcome-blind market-data capability test
Allowed during SOURCE GATE:
- endpoint/file existence;
- symbol existence;
- quote identity;
- timestamp availability;
- documented granularity;
- schema/field names;
- response metadata/counts only if they do not reveal market values;
- ability to query the event window.

Forbidden:
- OHLC/price fields;
- returns;
- volumes;
- spreads;
- basis values;
- any statistics derived from market values.

Frozen affected pair policy:
- USD quote on Coinbase where available.
- If the affected asset does not have Coinbase-USD, event is excluded rather than switching quote after outcomes.

Frozen reference policy:
1. Binance USDT spot if same base asset exists and historical public data is available.
2. OKX USDT spot as second reference if pre-outcome source capability passes.
Reference composite, if both pass, will be median of synchronized reference returns/basis-normalized prices under the later pre-outcome analysis freeze.
No reference substitution after prices are opened.

### 8. Source hierarchy
1. official Coinbase status incident pages / status API;
2. official Coinbase Exchange market-data documentation;
3. official Binance historical public-data documentation / data portal;
4. official OKX public market-data documentation;
5. secondary sources only for discovery, never for eligibility.

### 9. Next gate
If SOURCE_GATE_PASS:
create and commit a separate PRE-OUTCOME ANALYSIS FREEZE BEFORE opening any market values.

That freeze must pre-specify:
- exact T_isolation and T_recovery;
- exact basis formula;
- synchronization rule;
- primary horizon;
- pre-recovery baseline window;
- treatment/control design;
- reference-composite rule;
- event exclusion rules;
- minimum liquidity rule using only pre-frozen metadata or pre-event values if allowed by that freeze;
- fees/slippage assumptions;
- missingness;
- clustering;
- leave-one-out;
- concentration checks;
- exact decision gates.

Development may run ONCE only after that second freeze.

### 10. Development verdict taxonomy
Allowed final taxonomy:
- SOURCE_BLOCKED
- INSUFFICIENT_SAMPLE
- NO_EDGE_DISCOVERY
- SURVIVES_RAIL_RECOVERY_DISCOVERY

Primary failure closes the family: no rescue subsets, no secondary resurrection, no post-outcome changes.

If SURVIVES_RAIL_RECOVERY_DISCOVERY:
- do not call it a diamond;
- do not open 2026;
- do not trade;
- stop and require a new confirmatory freeze.

### 11. Evidence retention
Persist freeze commits, incident IDs, status URLs, timestamps, affected assets/networks, rejection reasons, source-coverage receipts, endpoint/schema evidence, workflow runs, and exact metrics only after lawful outcome opening.

### 12. Outcome access declaration
No market outcomes have been opened in this freeze.
