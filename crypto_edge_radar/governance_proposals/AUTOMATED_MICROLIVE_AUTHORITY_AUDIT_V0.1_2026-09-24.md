# CRYPTO EDGE RADAR — AUTOMATED EXECUTION AUTHORITY AUDIT V0.1

**Date:** 2026-09-24  
**Scope:** audit + design + authority proposal only  
**Canonical runtime:** `crypto-edge-radar-v05-canary` / Render service `srv-dalqkpu1egvs73fhiehg`  
**Canonical audited deploy:** `8173796c580b759829898e42a27889f4051f83fb`  
**Branch:** `automated-microlive-authority-audit-v0.1-2026-09-24`  
**Live execution:** DISABLED  
**Exchange mutation:** DISABLED  
**Capital:** DISABLED  
**Main merge:** NOT AUTHORIZED

## 1. CURRENT AUTHORITY MAP

Controlling precedence follows Governance V4:

1. exact frozen protocol + canonical execution + terminal closeout;
2. pre-outcome candidate-specific amendment;
3. frozen global policy;
4. current classification board/registry;
5. archive/roadmap/census;
6. branch names/chat shorthand.

Relevant controlling authorities audited:

- `CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN`
- `ND-PROMOTION-POLICY-V3.0-FROZEN`
- `DIAMOND-TEST-V1-FROZEN-2026-09-24`
- current Edge Classification Board
- current Diamond Board V0.1
- `MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1`
- `MEXC_FUTURES_MICROLIVE_FISHING_REGISTRY_V0.1`
- candidate-specific forward / Diamond / activation freezes surfaced by the current runtime

Current Render truth at audit time:

- deploy: `8173796c580b759829898e42a27889f4051f83fb`
- deploy state: LIVE
- runtime health: OK
- evidence backend: Postgres
- evidence chain: verified 748 events
- deployment drift: IN_SYNC
- mode: PUBLIC_SHADOW_ONLY
- authenticated exchange API used: false
- live capital enabled: false
- orders created: false
- exchange mutation performed: false
- Diamond Board capital authority: false

The Standing Operator Authority removes per-trade human reconfirmation for its covered MEXC Futures routes, but explicitly does NOT remove candidate-specific activation authority, risk, capital, source, timing or identity gates.

## 2. SCIENTIFIC EVIDENCE MAP

### BNB-LAUNCHPOOL-DEMAND-001
Historical/V3 science already earned:
- Tier 2 / Quase Diamante under Promotion Policy V3.
- Three disjoint evidence blocks; 66 total events in the V3 rare-event corpus.
- Historical verdicts remain immutable.

New 24 Sep Diamond V0.2:
- stronger prospective causal fingerprint only;
- first-25 gate is preserved for Diamond-strength evidence;
- it is NOT a Tier-2 prerequisite;
- it does NOT itself create micro-live or capital authority.
- runtime: 0/25, waiting genuinely prospective event.

Conclusion: historical science does not need repetition for a micro-live research authority review. A stronger Diamond/Tier-1 claim still needs the frozen prospective gate.

### ETF-CME-INSTFLOW-001
Science already earned:
- Tier 2 / fragile after prospectively frozen independent 2025 OOS.
- No need to repeat Discovery/OOS.

Controlling forward authority:
- Q4 V0.1A no-peek authority predates the 24 Sep Diamond proposal and has precedence.
- no BTC forward outcomes may be opened before 2027-01-01T00:00:00Z;
- exactly one final evaluation after frozen exits mature;
- minimum evaluable observations = 12.
- one missed 23 Sep exact-time observation is immutable and cannot be reconstructed.

Runtime:
- source OK;
- watcher = MISSED_EXPECTED_OBSERVATION_NO_CHASE;
- current CFTC-derived signal_direction = LONG;
- standing MEXC route = SHORT BTC_USDT only.

Conclusion: no historical retest is needed. Current signal/route direction mismatch is an execution-authority mismatch and must fail closed. The Q4 evidence gate remains controlling.

### OPTIONS-SPOTPERP-001-V2.1
Science already earned:
- exact 2025 independent OOS preserved;
- current board classifies Tier 2 / Quase Diamante / high-risk fragility.

Controlling forward gate:
- first 50 resolved forward trades;
- no early verdict;
- operational/execution audit still required.

Runtime:
- source OK;
- 5 signal days;
- 4 resolved forward trades;
- 4/50;
- descriptive BASE10 mean -106.154 bps and PF 0.3566;
- these interim numbers cannot create an early verdict.
- micro_live_authorized = false.

Conclusion: historical science does not need repetition, but the frozen prospective gate is still required before activation under current authority.

### TFG-DONCHIAN-REGIME-ADAPTATION-V1
Science state:
- separate post-parent-failure hypothesis;
- Tier 3 / forward-only;
- pre-2026 positive W1/W2 evidence exists but is not pristine independent post-freeze confirmation.

Runtime:
- 7/10 resolved forward trades;
- 4 unresolved execution paths, all maturing within frozen max hold;
- no missed eligible signals;
- readiness gate false;
- current resolved aggregate is negative, but the gate is not yet terminal.

Conclusion: this candidate still needs new scientific/forward evidence. It is not a micro-live candidate.

### HTF-DH03-12H-STANDALONE-FORWARD-V1
Science state:
- historical 12H sibling evidence survived;
- sibling evidence is supporting family evidence only;
- post-outcome substitution from 6H to 12H is prohibited;
- standalone 12H identity requires genuinely independent prospective evidence.

Runtime:
- external collector freshness = FRESH;
- latest source success 2026-09-24T00:01:42Z;
- public GitHub primary call is rate-limited, fallback is being used;
- outcome/count visibility unavailable from the public fallback;
- no outcomes are imported by that fallback.

Conclusion: needs new scientific evidence for the standalone identity; no capital mapping exists.

### CED1D-0031
Science already earned:
- Tier 2 / Quase Diamante;
- independent 2025 OOS positive;
- prospectively frozen execution-capacity corroboration passed at exactly 100 USDT/leg;
- earlier strict confirmation failure is preserved and not rewritten.

Controlling prospective gate:
- >=60 completed prospective events;
- >=8 complete UTC signal weeks;
- execution-readiness/integrity gates remain controlling.

Runtime:
- 0/60;
- 0/8;
- WAITING_SOURCE_READINESS;
- no current MEXC Futures micro-live mapping.

Conclusion: historical science does not need repetition; activation remains blocked by candidate-specific prospective evidence/readiness authority.

## 3. CANDIDATE MIGRATION MATRIX

| Candidate | Class | Current scientific state | Exact current blocker | Classification |
|---|---|---|---|---|
| BNB-LAUNCHPOOL-DEMAND-001 | A + C | Tier 2 | No candidate-specific automated spot execution authority/mapping; current MEXC standing authority is Futures-only; no event now | operational/governance |
| ETF-CME-INSTFLOW-001 | A + B + C | Tier 2 fragile | Q4 no-peek forward authority; current LONG signal does not match SHORT-only MEXC route; fresh capital/account state absent | scientific-forward + authority + capital |
| OPTIONS-SPOTPERP-001-V2.1 | A + B | Tier 2 high fragility | Frozen first-50 forward gate at 4/50; no candidate-specific active authority | scientific-forward + governance |
| TFG-DONCHIAN-REGIME-ADAPTATION-V1 | B | Tier 3 forward-only | Independent post-freeze validation incomplete; readiness 7/10 and not passed | scientific |
| HTF-DH03-12H-STANDALONE-FORWARD-V1 | B | standalone prospective shadow | Separate identity lacks independent prospective validation | scientific |
| CED1D-0031 | A + B + C | Tier 2 | Frozen 60-event/8-week prospective gate; source readiness 0/60,0/8; no MEXC Futures mapping | scientific-forward + operational |

Legend:
- A = scientifically eligible for authority review
- B = still needs scientific/forward evidence before activation
- C = operational blocker
- D = source blocker
- E = negative/failed evidence
- F = not applicable for automated micro-live under current route

No candidate is automatically promoted or activated by this matrix.

## 4. EXACT BLOCKERS

### Global blockers
1. Current canonical Render runtime is deliberately `PUBLIC_SHADOW_ONLY`.
2. `capital_authority=false`.
3. No authenticated exchange transport exists in canonical cloud runtime.
4. No automatic candidate allowlist authority exists.
5. No end-to-end exactly-once order-intent ledger exists in canonical Radar.
6. No current account-state receipt was collected in this mission because exchange credentials were explicitly out of scope. Any 22 Sep account/capital receipt is stale for a live decision.
7. Current MEXC standing authority is operator authorization, not automated execution authority.
8. Candidate-specific `ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY` instantiation is still required under the standing authority.

### Candidate blockers
- BNB: venue/product mismatch with current Futures authority; no spot executor authority; no current event.
- ETF: Q4 no-peek gate + direction mismatch + stale/no current capital receipt.
- OPTIONS: first-50 gate incomplete (4/50).
- TFG: Tier 3 / 7/10 forward readiness incomplete.
- DH03 standalone: independent prospective evidence incomplete.
- CED1D: 60/8 gate incomplete + WAITING_SOURCE_READINESS + no MEXC Futures mapping.

## 5. PROPOSED AUTOMATED_MICROLIVE_EXECUTION_AUTHORITY_V0.1

Canonical proposal file:
`crypto_edge_radar/governance_proposals/AUTOMATED_MICROLIVE_EXECUTION_AUTHORITY_V0.1.json`

Mandatory characteristics:
- proposal status = `PROPOSED_DRY_RUN_ONLY`;
- live transport disabled;
- every candidate explicitly allowlisted;
- no candidate inherits execution merely from Radar membership;
- every missing field fails closed;
- candidate identity, symbol, direction, venue, leverage, margin mode, notional and loss limits are immutable before the signal is transportable;
- no order if source, market, evidence or account freshness is stale;
- separate future activation authority is mandatory.

The current proposal intentionally sets `eligible_for_automated_execution=false` for every candidate.

## 6. HARD RISK FIREWALL SPEC

Required decision sequence:

1. parse immutable canonical signal;
2. verify immutable `signal_key`;
3. check candidate is in active automated allowlist;
4. bind exact frozen candidate identity/fingerprint;
5. verify candidate scientific authority still valid;
6. verify current activation gate passed;
7. verify source integrity and freshness;
8. verify evidence-chain integrity and freshness;
9. verify signal TTL;
10. verify market-data freshness;
11. verify exact venue/symbol;
12. verify exact direction semantics;
13. verify margin mode;
14. verify leverage;
15. verify minimum/maximum notional and venue metadata;
16. verify candidate exposure cap;
17. verify total account exposure cap;
18. verify daily loss firewall;
19. verify weekly loss firewall;
20. verify concurrent-position cap;
21. verify no conflicting order/position;
22. verify slippage bound;
23. verify fresh account-state receipt;
24. persist PRE_ORDER_AUTHORITY_RECEIPT;
25. persist exactly-once ORDER_INTENT keyed by `signal_key`;
26. only then may a future live adapter receive the intent;
27. verify exchange acknowledgement;
28. reconcile order/fills;
29. supervise position;
30. execute governed exit;
31. reconcile final position/order state;
32. persist immutable execution closeout.

Safety invariants:
- unknown => no order;
- stale => no order;
- authority mismatch => no order;
- duplicate signal => no second order;
- lost acknowledgement => reconcile first, never resubmit blindly;
- restart => reconcile exchange/account state before any new submission;
- kill switch => blocks new entries and permits only governed risk-reducing reconciliation/exit according to future frozen policy.

## 7. FAILURE MATRIX

| Failure | Detect | Fail-closed action | Recovery / reconciliation | Evidence |
|---|---|---|---|---|
| Render restart | new instance/runtime identity | no new order until reconciliation | reload intents, query authoritative state in future activated system | RESTART_RECEIPT |
| duplicate scheduler event | same schedule/event key | suppress duplicate | return existing result | DUPLICATE_SUPPRESSED |
| network timeout pre-submit | no transport started | no order | retry only while signal TTL valid | NETWORK_PRE_SUBMIT |
| exchange timeout | submission state unknown | freeze candidate | query order by client/idempotency key before any retry | ACK_UNKNOWN |
| accepted but response lost | missing local ack + possible exchange order | no blind retry | reconcile by immutable client order id | LOST_ACK_RECONCILIATION |
| partial fill | filled_qty < requested | block new entry intents | manage remaining qty by frozen policy; supervise actual filled position | PARTIAL_FILL |
| API 5xx | HTTP 5xx | no blind retry after possible submit | reconcile first | API_5XX |
| stale balance | receipt age > limit | no order | refresh account state | STALE_BALANCE |
| stale position | receipt age > limit | no order | refresh/reconcile positions | STALE_POSITION |
| stale ticker/orderbook | market age > limit | no order | refresh within TTL | STALE_MARKET |
| source outage | source gate fail | no order | wait for canonical source | SOURCE_FAIL |
| evidence DB outage | evidence persistence unavailable | no order | restore DB then verify chain | EVIDENCE_DB_FAIL |
| Postgres unavailable | DB connection fail | no order | restore; verify chain head | POSTGRES_FAIL |
| crash after intent before submit | intent=PERSISTED, no ack | no submit until reconciliation | prove no exchange order, then resume if TTL valid | INTENT_RECOVERY |
| crash after acknowledgement | ack persisted/remote exists | no second order | reconcile fills/position | ACK_RECOVERY |
| exit scheduler failure | exit overdue | block new entries | governed risk-reducing recovery path only | EXIT_OVERDUE |
| duplicate exit | existing exit intent/order key | suppress | reconcile existing exit | DUPLICATE_EXIT |
| exchange maintenance | venue state unavailable | no new order | wait/reconcile existing positions | VENUE_MAINTENANCE |
| symbol unavailable | metadata/status invalid | no order | wait for exact authorized symbol | SYMBOL_UNAVAILABLE |
| insufficient balance | feasibility fail | no order | no risk increase; wait for valid capital state | INSUFFICIENT_BALANCE |
| minimum-notional violation | min > frozen max | no order | never increase risk to meet venue min | MIN_NOTIONAL_BLOCK |
| price moves during submission | expected slippage > cap | cancel/reject if safely possible under frozen future semantics | reconcile any partial/accepted quantity | SLIPPAGE_BREACH |

## 8. IMPLEMENTATION GAP ANALYSIS

### Existing useful components
- immutable signal-key / duplicate protection already exists in Radar research paths;
- fail-closed schedulers and no-chase semantics exist;
- Postgres immutable evidence chain exists;
- restart/deploy identity and liveness observability exist;
- current MEXC prep package has authenticated read-only preflight, risk-state tooling, a live-executor binary lineage and exit-guard lineage;
- standing operator authority exists;
- account risk firewall was previously validated;
- Windows single-instance lock is validated in V0.14.3.3.

### Missing or not authoritative for automated live
1. a single canonical automated execution authority parser/validator;
2. candidate allowlist with frozen execution envelopes;
3. a durable exactly-once `order_intent` table keyed by candidate + signal;
4. atomic state transition `SIGNAL_ELIGIBLE -> INTENT_PERSISTED -> TRANSPORTING -> ACKED -> PARTIAL/FILLED -> EXITING -> CLOSED`;
5. durable exchange client order id derived from immutable intent;
6. ack-loss reconciliation before retry;
7. orphan-position scanner;
8. open-order + position reconciliation on every restart;
9. canonical partial-fill policy;
10. canonical rejected-order policy;
11. canonical governed-exit state machine;
12. global kill-switch authority semantics;
13. current candidate-specific numerical exposure/loss/slippage limits;
14. current candidate-specific venue/product mappings for BNB and CED1D;
15. a current account-state freshness contract integrated with automatic eligibility;
16. observability for intent/ack/fill/position/exit/reconcile states;
17. deterministic dry-run adapter proving every failure path;
18. proof that live-capable adapter is physically absent/disabled in dry-run deployments.

No component capable of sending a real order is implemented by this audit branch.

## 9. TEST PLAN

Before any live activation, deterministic tests must cover at least:

- duplicate signal -> one intent only;
- duplicate scheduler invocation -> one intent only;
- restart before intent -> no order;
- restart after intent before transport -> reconcile, no blind submit;
- restart after exchange acknowledgement -> no second order;
- lost acknowledgement -> remote reconciliation first;
- partial fill -> position state equals actual fill;
- stale risk receipt -> fail closed;
- stale source -> fail closed;
- stale market data -> fail closed;
- wrong candidate -> fail closed;
- wrong symbol -> fail closed;
- wrong direction -> fail closed;
- wrong venue -> fail closed;
- wrong leverage -> fail closed;
- wrong margin mode -> fail closed;
- notional overflow -> fail closed;
- candidate exposure overflow -> fail closed;
- total account exposure overflow -> fail closed;
- daily loss breach -> fail closed;
- weekly loss breach -> fail closed;
- concurrent-position breach -> fail closed;
- kill switch active -> fail closed;
- evidence DB unavailable -> fail closed;
- Postgres unavailable -> fail closed;
- exchange 5xx pre-submit -> no intent transport;
- exchange timeout after possible acceptance -> no blind retry;
- minimum notional above frozen max -> no trade;
- account receipt stale -> no trade;
- signal TTL expired -> no trade;
- existing conflicting position/order -> no trade;
- partial exit -> continue governed reconciliation;
- duplicate exit -> one exit intent only.

Required assertion for all applicable cases: `FAIL_CLOSED`.

## 10. MIGRATION PLAN

### M0 — authority freeze
- freeze V0.1 proposal and schema;
- no live adapter;
- no credentials;
- no capital.

### M1 — deterministic dry-run arbiter
- implement authority resolver + firewall against static fixtures;
- mock/null adapter only;
- persist synthetic intents/acks/fills;
- prove exactly-once behavior.

### M2 — shadow integration
- feed real canonical Radar signals into dry-run arbiter;
- produce `WOULD_TRADE` / `BLOCKED` receipts;
- no authenticated exchange mutation;
- compare decisions across restart/redeploy cycles.

### M3 — authenticated read-only reconciliation
- separate future authority required;
- use fresh account state only;
- verify positions/orders/balance/contract metadata read-only;
- live order endpoints remain disabled.

### M4 — candidate-specific activation review
For each candidate:
- frozen scientific identity;
- exact route;
- exact direction;
- exact symbol;
- exact risk envelope;
- exact freshness limits;
- exact kill/exit semantics;
- all dry-run tests pass;
- current scientific/forward gate passes;
- current account/capital feasibility passes.

### M5 — future live activation
Explicitly outside this mission.
Requires a separate operator authorization after review of this audit and dry-run evidence.

## 11. CANDIDATES THAT MAY ENTER FUTURE AUTOMATED-MICROLIVE AUTHORITY REVIEW WITHOUT REPEATING HISTORICAL SCIENCE

1. **BNB-LAUNCHPOOL-DEMAND-001**  
   Yes for authority design/review. V3 Tier-2 science is already earned. It needs a spot execution mapping and candidate-specific risk/execution authority. The 25-event Diamond V0.2 gate is a stronger Diamond-evidence gate, not a requirement to re-earn Tier 2.

2. **ETF-CME-INSTFLOW-001**  
   Yes for authority design/review. Do not repeat Discovery/OOS. Activation is blocked by the controlling Q4 no-peek authority, current direction mismatch, and fresh capital/account requirements.

3. **OPTIONS-SPOTPERP-001-V2.1**  
   Yes for authority design/review. Do not repeat 2025 OOS. Activation remains blocked by the existing first-50 prospective gate.

4. **CED1D-0031**  
   Yes for authority design/review. Do not repeat 2025 OOS/execution-capacity work. Activation remains blocked by the current prospective 60-event/8-week authority and missing execution mapping.

## 12. BLOCKERS THAT REALLY NEED NEW SCIENTIFIC EVIDENCE

- `TFG-DONCHIAN-REGIME-ADAPTATION-V1`: independent post-freeze validation/readiness gate still incomplete.
- `HTF-DH03-12H-STANDALONE-FORWARD-V1`: standalone identity needs genuinely independent prospective evidence; historical sibling success cannot be promoted into a separate live candidate.
- `ETF-CME-INSTFLOW-001`: its existing Q4 prospective authority still demands future evidence, but this is not a request to repeat historical science.
- `OPTIONS-SPOTPERP-001-V2.1`: existing first-50 gate is still required; again, historical OOS must not be repeated.
- `CED1D-0031`: existing prospective gate is still required; historical OOS must not be repeated.

BNB Diamond V0.2 requires new prospective evidence for a Diamond-strength conclusion, but V3 explicitly does not require those 25 events merely to retain Tier 2.

# FINAL VERDICT

**AUDIT COMPLETE** for the current controlling authority graph and canonical runtime state observed on 2026-09-24.

**PROPOSED AUTHORITY: SAFE_TO_IMPLEMENT_IN_DRY_RUN**

Conditions:
- keep live order transport physically disabled;
- keep credentials unused;
- keep every candidate `eligible_for_automated_execution=false`;
- implement only mock/null transport until a separate future activation mission;
- never weaken or bypass candidate-specific scientific/forward gates;
- no merge to main in this mission.

**NOT LIVE READY. NO CAPITAL ACTIVATED. NO ORDER SENT. NO FROZEN SCIENCE CHANGED.**
