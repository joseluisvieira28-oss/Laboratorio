# CRYPTO LAB — CONVEX DIAMOND V02: ECONOMIC & OPERATIONAL EVIDENCE FINAL CLOSEOUT
Date: 17 October 2026 UTC. Research-only, no trading or money spent, main untouched.

## Work delivered and actual executions

1. **Historical-source catalogue gate** (GitHub Actions [39023059551](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39023059551), SUCCESS): EXACT six anonymous predeclared OKX `GET /api/v5/public/market-data-history` requests. SOL/BNB × 2023-12-03 / 2024-06-03 public 400-level L2 module-4 catalogue = **4/4 HTTP200/code 0 and nonempty one-item list**, 0 verified download files or source orderbook observations. SOL June 2024 funding catalog 1/1 HTTP200/code 0/one-item; BNB funding 1/1 HTTP429 SOURCE_BLOCKED. Returned public item links were NOT verified, no authenticated account, no market-price access; no inference of executable fill or funding price.
2. **Schema follow-up bounded before any re-query**: [39023403588](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39023403588), engineering SUCCESS, one frozen SOL 2024-06-03 module-4 public GET returned HTTP403 (0 response bytes), hence **SOURCE_SCHEMA_BLOCKED on follow-up**. 403 is not proof that the original catalogue records were invalid, nor a source PASS. No bypass, rotation, retry or new API.
3. **Stop proposal vs verified ACK contract**: [39023059551](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39023059551), 23 synthetic unit tests PASS on Linux and Windows: reject weakening LONG/SHORT stops; missing/wrong broker ACK, quantity/position mismatch, stale/crossed/offtick quote, lost ACK, uncertain timeout, blind resends. Pure model, not a real MEXC/Kraken/OKX stop roundtrip; `BROKER_ATTACHED_SL_ROUNDTRIP_NOT_CERTIFIED` remains.
4. **Pre-outcome-frozen MONOTONIC-ONLY V5 child**: full source-verified Binance USD-M 2023–25 replays [39023293246](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39023293246), SUCCESS both SOL/BNB matrix jobs. A one-line modification of original `matrix.py` makes stop = max(previous, original conditional stop) for LONG. Original 2023-25 BASE/STRESS result parity was asserted **before any child outcome**, and official source 333216 5m, 27768 1h, 3288 funding + 112 original publisher-checked file manifests each verified. Two assets × two costs = 4 original+4 child full ledger outcomes with complete CSV artifacts. 2026 holdout unopened.

## Exact historical economic results — CUMULATIVE 2023–25 percent of separate paper 10k portfolio, NOT future alpha

| Model | SOL1h BASE | SOL1h STRESS | BNB4h BASE | BNB4h STRESS |
|---|---:|---:|---:|---:|
| Original V5 | +59.38828758% | +58.29547408% | +27.37792782% | +27.05530671% |
| New monotonic-only stop child | +54.86119135% | +53.72830903% | +26.79950990% | +26.44879415% |
| Child minus parent (percentage points) | **-4.52709623** | **-4.56716505** | **-0.57841793** | **-0.60651255** |

BASE source details:
- SOL original 84 closed, PF 1.82399984, max model 5m-low DD -12.26737%; child 87 closed, PF 1.75865740, DD **still -12.26737%**, 2025 child closed PnL -883.59 USDT versus original -577.72. New child is NOT a simple reduction of original 84 cashflows; it fully changes exits and re-entries.
- BNB original 28 closed, PF 2.89417932, DD -7.95943%; child 29 closed, PF 2.93314544, DD **worsens to -8.10029%**, though PF rises slightly. Child 2023 remains negative.
- Positive child historical return is in-sample descriptive only; no real stop brokerage state or capital risk proof.
- The distinct already completed PR #224 early-half + monotonic model lost return versus Parent too, but it is NOT the same rule, never aggregate economic claims.

## What today's attack ACTUALLY proves

- We can build a deterministic, source-pinned, risk-proposal **monotonic-only child** that never decreases its computed stop. Synthetic broker-state readback test code refuses to count an unacknowledged stop as protection.
- This child **does not improve total return or maximum modeled drawdown** on the only two original best historical hypotheses; BNB PF improves slightly, but return and DD do not.
- OKX has an identified anonymous historical market-catalogue API, and original 4/4 frozen SOL/BNB L2 date-family queries had nonempty catalog entries. There is still **no verified quote/timestamp/source file usable for a historical executed PnL test**; subsequent fixed schema-only query 403, and historical licensing/contract-level semantics unresolved.
- No strong grounds to call a cross-venue improvement or a safe all-weather money machine. The 2023-driven SOL regime, missing independent OOS, SOL time overlap and BNB low sample from PR #244 remain intact.

## Two gates still necessary before a real system

A. **Venue exact historical execution gate**: actual published L2 downloadable raw historical files, publisher hash and contract-size/tick/fee/funding provenance; the same original SOL1h/BNB4h Binance signals mapped to venue ASK entry and BID exit at the causal timestamp, a valid conservative stop fill engine through gaps and orderbook depletion, all expected missing episodes accounted for. Different venue book history != real broker fills, and not a free new untouched OOS.
B. **Stop deployment proof**: instrument-specific signed API sandbox/test environment confirmation of a native active protective stop returned by authoritative broker readback; position, direction, contracts, trigger type, tick & correlation, cancellation/restart/timeout idempotence, broker reject/liquidation and gap stress. No first real order without future distinct authorization and independent economics. Original V5 nonlatched policy remains NO LIVE GO, newly monotonic child's economic performance is not independently validated.

## Final classification per science line

- SOL1h original: **HISTORICAL_CANDIDATE / ORIGINAL_TRAILING_LIVE_UNSAFE / INDEPENDENT_OOS_MISSING**.
- BNB4h original: **HISTORICAL_CANDIDATE / SMALL_SAMPLE / HISTORICAL_KRAKEN_2023_COVERAGE_INCOMPLETE / SOURCE/EXECUTION UNKNOWN**.
- SOL5m: separate **HISTORICAL_CANDIDATE_SECONDARY**, 2023 concentration & correlated with SOL1h, not retested economically in this V02.
- Monotonic-only child SOL1h/BNB4h: **DESCRIPTIVE_HISTORICAL_POSITIVE / NOT BETTER ECONOMICALLY THAN PARENT / NO DD BENEFIT / NOT OOS**. Do not promote.
- Kraken fixed prior 16 analytics source route: **SOURCE_DATE_COVERAGE_NOT_PROVEN** (PR #245).
- OKX 400-level historic catalogue: **CATALOGUE_CANDIDATE / HISTORICAL_L2_NOT_VERIFIED**, source follow-up 403, no net exchange venue conclusion.
- Broker native protective stop: **NOT CERTIFIED**.
- **NO LIVE_GO / NO LIVE TRADING AUTHORITY / NO MONEY MACHINE CERTIFIED.**

## Governance and resource hygiene

Scientific freezes: `PRE_SOURCE_AND_STOP_FREEZE_2026_10_17.md`, `MONOTONIC_ONLY_CHILD_PRE_RESULT_FREEZE_2026_10_17.md`, `OKX_ONE_SCHEMA_INSPECTION_PRE_FREEZE_2026_10_17.md`. Original V5 model and main untouched. Historic 2026 holdout LOCKED. GitHub Actions for initial 6-source matrix was accidentally triggered after unrelated commits; switched to manual-only to prevent duplicate source checks and energy loss. No historical replay repeats after full child success, no private data, no wallets, no orders, no Render/Windows watcher changes, no costs.
