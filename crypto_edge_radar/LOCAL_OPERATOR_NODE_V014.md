# LOCAL OPERATOR NODE V0.14 — SEVEN-MOTOR FORWARD SHADOW

Status: **RESEARCH / PUBLIC SHADOW ONLY — NO CAPITAL — NO ORDERS**

Build identity: `v0.14-win-seven-motor-forward-shadow`

Registry authority: **3.6**

## Seven active/gated motors

1. ETF-CME-INSTFLOW-001 — Tier 2 retained fragile
2. BNB-LAUNCHPOOL-DEMAND-001 — Tier 2 / Quase Diamante / tail-fragile
3. OPTIONS-SPOTPERP-001-V2.1 — Tier 2 / Quase Diamante / high-risk fragility
4. TFG-DONCHIAN-REGIME-ADAPTATION-V1 — Tier 3 forward-only
5. HTF-DH03-12H-STANDALONE-FORWARD-V1 — prospective standalone forward
6. CED1D-0031 — Tier 2 / Quase Diamante / forward-fragile; external T+3 collector
7. EMA6H-50X200-REGIME-DEPENDENCY-001 — Tier 3 high watchlist / prospective regime forward only

## What changed from V0.13.2

V0.14 is built from the later canonical Postgres Radar authority after the 19 Sep 2026 operational hardening.

It adds:
- EMA6H 50x200 regime forward watcher to the local forward runtime;
- registry 3.6 / seven-motor control plane;
- ETF-CME public signal watcher;
- persistent runtime-liveness buckets and recovered-gap receipts;
- BNB late-first-observation fail-closed / NO CHASE semantics;
- bounded Binance CMS rate-limit retry/cooldown;
- rate-limit-resistant external freshness fallback for DH03 and CED1D;
- all previous DH03 clock and runtime-truth hardening.

## EMA6H scientific boundary

EMA6H is **not a Quase Diamante**.

Protected Binance OOS classification: `TIER3_WATCHLIST`.
Observed aggregate OOS:
- BASE mean about +4.35 bps
- BASE PF about 1.035
- STRESS mean about +0.35 bps
- 2025 negative
- 2026 Jan-Aug positive

Historical regime analysis was diagnostic only and has no promotion authority.

The separate prospective regime experiment was frozen before forward observation.
First eligible forward signal close:
`2026-09-20T00:00:00Z`

Automatic promotion: **NO**.

## Local engine topology

Local forward supervisor runs public-data shadow logic for:
- BNB Launchpool
- TFG Donchian Regime
- OPTIONS-SPOTPERP V2.1
- ETF-CME Institutional Flow
- EMA6H 50x200 Regime

DH03 runs in its dedicated local minute-path collector thread.

CED1D remains externally collected by the dedicated GitHub T+3 archive-shadow workflow and is represented in the control plane / freshness state.

## PC 24/7 Render Sentinel

V0.14 also runs a read-only sentinel every 5 minutes against the canonical Render public health endpoint.

Purpose:
- keep the free Render canary warm while the PC is online;
- detect remote health/evidence-chain/safety anomalies;
- detect recovered liveness gaps instead of silently treating them as healthy;
- persist local append-only sentinel receipts for later reconciliation.

Sentinel states:
- OK = Render health OK, Postgres evidence chain OK, safety flags all false.
- REMOTE_REVIEW_REQUIRED = a recovered runtime gap requires review.
- REMOTE_FAIL_CLOSED = remote health/evidence/safety state is inconsistent.
- REMOTE_UNREACHABLE = public canary could not be reached after bounded retries.

The sentinel is public/read-only. It uses no credentials and can never create orders or mutate an exchange. A remote sentinel failure does not fabricate a scientific failure and does not rewrite candidate evidence.

## DH03 integrity

Before DH03 can persist a prospective activation boundary:
- Binance USD-M public clock check must pass;
- absolute local-vs-Binance midpoint offset <= 500 ms;
- public RTT <= 1000 ms.

Runtime truth:
- MISSING / BOOTSTRAPPING => GATED
- COLLECTING => SHADOW
- FAIL_CLOSED => BLOCKED

Minute-path integrity:
- exact entry minute required;
- missing minute / gap => unresolved fail-closed;
- same-minute stop + target => STOP-FIRST;
- strictly ordered funding timestamps;
- no reconstruction of missed execution paths.

## Runtime safety

- no API keys required
- no authenticated exchange API
- no order creation
- no exchange mutation
- no wallets
- no capital
- no live trading
- no automatic micro-live
- no merge to main
- no tuning of scientific rules

## Startup

1. Close any older CryptoEdgeRadarNode.exe.
2. Preserve `%LOCALAPPDATA%\CryptoEdgeRadar`; do not delete existing DH03 persistence.
3. Extract V0.14 into a fresh directory.
4. Verify the release SHA256 values against the immutable release receipt.
5. Keep Windows clock sync enabled.
6. Disable sleep and hibernation while the node is required.
7. Prefer a stable wired/Ethernet connection.
8. Start `CryptoEdgeRadarNode.exe`.
9. Open `http://127.0.0.1:8787`.
10. Confirm registry 3.6 and 7/7 focus motors.
11. DH03 may move BOOTSTRAPPING -> COLLECTING.
12. EMA6H must remain prospective forward-only and must not fabricate any pre-boundary evidence.

V0.14 is a research observation node. Passing backtests or forward gates does not itself create execution authority.
