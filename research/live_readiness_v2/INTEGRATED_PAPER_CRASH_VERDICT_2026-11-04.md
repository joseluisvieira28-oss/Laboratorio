# CRYPTO LAB LIVE READINESS V2 — INTEGRATED PAPER CRASH BOUNDARY VERDICT
**Date:** 2026-11-04 UTC · **PR #334** · **MODE: PAPER ONLY, HARD LIVE DISABLED**  
**Scientific verdict:** `PAPER_INTEGRATION_FAULT_INJECTION_PASS_LIMITED / LIVE_BROKER_RECOVERY_UNPROVEN / INDEPENDENT_ECONOMIC_EDGE_UNPROVEN / NO_LIVE_GO`.

## A. Preconditions / frozen scope
- This implementation follows the pretest [INTEGRATED_PAPER_CRASH_GATE_FREEZE_2026-11-04.md](./INTEGRATED_PAPER_CRASH_GATE_FREEZE_2026-11-04.md), source freeze commit `3d8d0edcec274fb6f59c060056e1c9234824ce32`.
- Prior `risk_firewall.py` 69/69 synthetic tests, `single_writer_recovery.py` 48/48 prior Linux/Windows tests, PR #334 architecture freeze. The old risk signal/financial gates are unchanged.
- Original scientific PR #333 Liquidation Exhaustion forward remains `ECONOMIC_FORWARD_INSUFFICIENT` with ZERO qualifying decisions; original LICP PR #107 NO_EDGE remains unchanged. No original protected holdout or `main` touched.
- This is an engineered mock **without** MEXC SDK, trading API calls, live orders, real account access, funded account, Telegram authority, or paid data.

## B. Actually implemented
1. [`integrated_paper_executor.py`](./integrated_paper_executor.py) imports the EXISTING independent `Policy`, `Quote`, `Account`, `Intent`, `Firewall` risk preflight and `PaperFencedStore` transactional epoch/fencing. All instruments restricted to one physical `BTC_USDT` paper exposure; synthetic accounts only.
2. A *separate*, durable SQLite `mock_broker.sqlite` models a broker **outside** the custody transaction; `custody.sqlite` is the authoritative durable paper reservation and idempotency ledger. No atomic commit across them, *intentionally*, so post-fill crashes can create unmatched paper state.
3. Full guarded PAPER path: simulated operator arm (boolean only) → stale/fee/slip/contract/stop/risk preflight → persisted duplicate-proof `client_id` → independent simulated broker acceptance → custody fill receipt → independent simulated broker stop ACK → custody protected state. All broker outcomes are MOCK labels.
4. Real subprocess `os._exit` after **local reservation but before broker**, **after mock broker fill but before local ACK**, and **after mock broker stop ACK but before local protected state**. On restart, previous authority cannot resume; new owner enters `FROZEN_RECOVERY_REQUIRED`, reconciles the two durable stores, and blocks automatic repeat of the same order ID.
5. A broker-reported active simulated position or server stop, or an orphan broker ID absent from custody, refuses reconciliation even when synthetic human approval boolean is true. A simulated human can explicitly flatten in the separate broker before the frozen custody state is reconciled. Local receipts distinguish canceled-unsent from independently mock-filled-and-flat (`CLOSED`) IDs.
6. The underlying single-writer store now persists daily/weekly modeled cash-loss **high-water marks** and latches a durable `FROZEN_PAPER_LOSS` hard lock atomically before mirroring the in-process firewall. A lower subsequent loss snapshot cannot clear it. An equity fall can trigger the lock without a new trade loss. Simulated human recovery cannot bypass a hard loss lock.
7. [`test_integrated_paper_executor.py`](./test_integrated_paper_executor.py): **26** additional integration cases. Both existing 69 risk firewall and 48 single-writer cases are included in the aggregate **143-case** test matrix.
8. [`.github/workflows/live-readiness-v2-integrated-paper-ci.yml`](../../.github/workflows/live-readiness-v2-integrated-paper-ci.yml): no-live static guards, negative `pipefail` proof against GitHub false green, Linux + Windows GitHub-hosted isolated tests, full raw test evidence artifacts.

## C. Real evidence and code chronology
### First attempt (historical failure, deliberately preserved)
[GitHub run #41911141971](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41911141971) produced **143 tests, one failing assertion on Linux and Windows**. The mocked stop rejection **correctly** caused the risk firewall to return explicit `REJECT_RISK:NOT_PAPER_ARMED`, but the test fixture had incorrectly required a `GuardError` exception. Code already blocked the new entry; the assertion was fixed to require the specific rejection and prove mock broker order count remains one. The original failed CI was NOT relabeled PASS.

### Canonical final rerun
**[GitHub Actions #41911263408](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41911263408)**, code head SHA **`8ebd43a23933bba368f44decaf1ce821387b0dc0`**:
- **Linux Ubuntu:** `Ran 143 tests in 2.084s` → `OK`. Original artifact **#13362966185**, independently downloaded ZIP SHA256 **`a41bc185e44abc470c50f32763e7df078fd0df51408acccac7cc127c2a5684bf`**, exact GitHub-published digest.
- **Windows:** `Ran 143 tests in 11.824s` → `OK`. Original artifact **#13362592269**, independently downloaded ZIP SHA256 **`96c7901fb5e4e56af64a22257aa47f3674db8328eff9a9e1b4cc2ab0a0e65ad5`**, exact GitHub-published digest.
- Both original ZIPs were independently read: terminal `OK`, **zero FAIL or ERROR**. GitHub jobs both `completed / success`; no real network trading.
- `69+48+26=143` per OS; aggregate **286 passing test executions**, with independent two-platform coverage. This is a regression count, not independent profitable trading episodes.

## D. Explicit adversarial outcomes
- A paper order locally RESERVED, then crash BEFORE broker acceptance: broker has no order; restart freezes, independent broker flat inspection and test human confirmation allow paper reconciliation as CANCELLED; old client ID cannot be retried.
- Mock broker FILLED, then crash BEFORE local receipt: local PENDING + external mock FILLED_NO_STOP, restart stays FROZEN. Even `human_approval=True` cannot clear it while broker reports exposure. Only after explicit simulated flatten and reinspection may it be CLOSED, never RESUBMITTED.
- Mock broker STOP_ACK, then crash BEFORE local protected receipt: local FILLED_UNPROTECTED + mock broker STOP_ACTIVE; restart stays FROZEN and the stop is not inferred absent/present from custody alone. Verified mock close before ledger reconciliation.
- Mock stop rejection: custody enters FROZEN, broker retains simulated unprotected exposure. Second signal is explicitly risk rejected; mock broker order count stays 1.
- Persistent daily/weekly loss caps: if hit, store latches hard lock and no subsequent process/epoch can acquire trading authority. A lower loss reading cannot unfreeze or reset loss highwater.
- Stale quotes, stale synthetic account, too-large planned loss, incorrect stop qty, duplicate IDs and orphan broker entries are independently blocked or detected.

## E. IMPORTANT PRODUCTION LIMITATIONS — this is *not* a live-go proof
1. **No exchange-side order or stop is fenced by SQLite.** A real order already on the network might reach MEXC after its local owner's lease expires; two local SQLite files and Python PIDs cannot guarantee exactly-once cross-network execution. The mock broker is on the same host, under same test code, with no latency, broker exchange latency, unreliable receipt IDs, account netting, liquidation or rate limits.
2. An accepted native MEXC stop, partial fill, cancel/replace and actual flatten would need **broker-confirmed** read-only reconciliation (positions + open orders + conditional stops + fills) and a separately engineered production-grade handshake. No broker API connection is present and no real protective-stop ACK has been shown.
3. `human_approval=True` and `mock_flat_confirmed=True` are **boolean test fixtures**, not identity authentication or broker evidence. A malicious process with local DB write privileges could fabricate records; these tests prove resistance to faults in modeled co-operating processes, not hostile takeover.
4. `Firewall._preflight` is called as an existing (private) risk interface in this isolated paper adapter; no production-stable interface or integrated durable order transport has been certified. The risk limits are **illustrative**, not user-approved live settings, and stop losses cannot cap gap/slippage losses.
5. The new persistent loss highwater is intentionally **conservative and has no reset/rollover procedure**. This prevents accidental rearm but is not a production day/week risk accounting design: a future audited time-bucket/accounting protocol is required.
6. True power removal, disk corruption, filesystem failure, cloud split-brain, remote distributed leases, operational Windows scheduled service crashes, missed pings, and actual live account uncertainty are NOT proved by these subprocess simulations.
7. All fees, available equity, contract specs, price quotes and stop receipt correctness are PAPER fixtures. No net after-cost live strategy, real shadow position tracking or independently positive edge exists yet. This mock integration cannot promote PR #333 or other older signals to LIVE GO.

## F. Binding next verdict
`PAPER_INTEGRATION_FAULT_INJECTION_PASS_LIMITED` (demonstrably reproducible in Linux and Windows with original raw receipts).
`NO_LIVE_GO` for MEXC real orders and financial risk. PR remains isolated DRAFT, no merge main, no account calls, no paid infrastructure, no automatic recurring monitoring or scheduled job.

**Next smallest legitimate gate:** independent real-source PAPER shadow using frozen strategy and actual executable quotes, with signed source/reconciliation evidence *without* changing any broker account. Separately, specify broker-native stop/partial-fill/cancel semantics and least-privilege read-only account checks under future explicit authorization. Never infer net economic edge from mock CI passes.
