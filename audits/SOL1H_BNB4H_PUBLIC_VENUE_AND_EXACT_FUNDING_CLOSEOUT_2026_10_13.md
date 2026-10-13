# SOL 1H / BNB 4H — PUBLIC EXECUTION FEASIBILITY & EXACT FUNDING SOURCE CLOSEOUT
**Date 2026-10-13 UTC; trading_authority NONE.** Protocol `research/convex_sol_bnb_gates_v01/PRE_OUTCOME_GATES_FREEZE.md` commit `8463289b7eb9cb601e344197ee47c9e25814ab9d`, frozen before any current-source outcome.
Reference historical parent is immutable run 38432883246; research-only 2023–25 SOL1h +59.39% BASE / +58.30% STRESS, BNB4h +27.38% BASE / +27.06% STRESS, NOT independent OOS and not live executable.

## GitHub Action receipts
Run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38435238482. 16/16 synthetic technical/public-only/forward-gate tests PASS. Four independent sensor jobs: **MEXC public SOL and BNB PASS**, **Binance exact funding-rate mark SOL and BNB SOURCE_BLOCKED** due HTTP 451 from `https://fapi.binance.com/fapi/v1/fundingRate`. Overall Action FAILURE is source-correct fail-closed, not a trading-strategy failure. DO NOT change DNS/hosts, location, user account or restricted endpoint to bypass 451. Actual Binance exact settlement funding remains UNKNOWN.

## MEXC public venue one-shot, 2026-10-13 ~17:01 UTC
Public endpoints used: GET `https://contract.mexc.com/api/v1/contract/detail/country?symbol={...}`, GET `.../api/v1/contract/depth/{...}?limit=20`, GET `.../api/v1/contract/funding_rate/{...}` only. No auth, private API, user/account/balance, order or exchange mutation. Raw response SHA256 and timestamps preserved in immutable GitHub Actions artifacts.
| Public observation | SOL_USDT | BNB_USDT |
|---|---:|---:|
| Contract size base asset / contract | 0.1 SOL | 0.01 BNB |
| Min volume and step | 1 contract | 1 contract |
| Best ask | 107.25 USDT | 744.00 USDT |
| Best bid | 107.24 USDT | 743.90 USDT |
| Observed spread | 0.93244 bps | 1.34418 bps |
| Public first snapshot age | 345 ms | 277 ms |
| Public book volume across first 20 levels | 47 contracts | 51 contracts |
| Minimum one-contract notional at best ask | 10.725 USDT | 7.44 USDT |
| Paper order for ~100 USDT notional | 10 contracts ≈107.25 USDT | 14 contracts ≈104.16 USDT |
| Does 20-level ask book show that quantity? | YES, **NOT a fill** | YES, **NOT a fill** |
| Paper order for ~2,000 USDT notional | 187 contracts ≈2,005.58 USDT | 269 contracts ≈2,001.36 USDT |
| Does 20-level ask book show that quantity? | **NO** | **NO** |
| Public fundingRate current | +0.000025 | 0.0 |
| Public fair price | 107.26 | 743.8 |
| Public index price | 107.29 | 743.5 |

Important contract book arithmetic: MEXC depth array [price, NUMBER_OF_ORDERS, CONTRACT_QUANTITY]; using second element as quantity is wrong. Validated with strict source timestamps and quantity-step/min checks. Public snapshot could be stale in milliseconds, market depth can vanish, available depth does not guarantee execution; MEXC may impose min notional/max regional restrictions, account margin/leverage/risk. Isolated paper 500 USDT capital x20%=100 USDT trade exposure could be source-size feasible at one instant; 10,000 USDT x20%=2,000 USDT not covered in first 20 ask levels for either snapshot, not proof market as a whole lacks liquidity. No actual execution depth/fill OOS proof.

## Fee schedule mismatch — do NOT lower frozen cost assumption!
Public contract `takerFeeRate` surfaced 0.0002 (0.02%) and `makerFeeRate` 0 (0%) for BOTH symbols at time of capture. Published MEXC API Futures announcement effective 2026-06-01 says API-specific **taker 0.08%/side (8bps), maker 0.06%/side (6bps)** for applicable contracts, takes precedence over web promotions; regional eligibility can differ:
https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742
Therefore **frozen 8bps taker per side stays the only economically conservative assumption**; visible public contract-rate is NOT account/API-specific authenticated reality. Full cost also includes slippage, spread, impact, stop gap, funding and venue access. Real authenticated fee tier is UNKNOWN and not accessed under this mission.

## Why Binance exact funding BLOCKED
Documented official `GET /fapi/v1/fundingRate` contains a `markPrice` associated with actual funding charge, which is superior to a 5m market-open proxy, but it returned **HTTP 451 legal restriction** from GitHub hosted runner for both symbols at first request for 2023–25 data. No 3y funding mark samples were opened and **no exact-funding-mark replay was executed**. Retain SOURCE_BLOCKED not a zero funding assumption, and do not imply a substitute market/mark candle is exact settlement.

## Distinct source sensitivity F1B
Separate pre-outcome source-only extension in `research/convex_sol_bnb_gates_v01/F1B_MARK_1M_PROXY_SOURCE_FREEZE.md`: full publisher-SHA-verified 2023–25 **markPriceKlines 1-minute candle OPEN** at each original 3288 historical funding timestamps, rerun Parent unchanged, label `MARK_1M_OPEN_PROXY` and not exact settlement, no independent OOS or practical venue parity. The original F1 blocked status remains even if F1B succeeds; do not conflate.

## Forward readiness and remaining blockers
Pure offline `forward_custody_gate.py` implements >=2026-10-15T00:00Z eligible closed bar and immutable witness checks for SOL1h and BNB4h; it rejects postfactum samples and stale public quotes. **This is a validator, not an operational collector**. No branch-only GitHub scheduled workflow persists with scientific append-only custody without deployment/host/default-branch merge; main merge and Render prohibited. No contemporaneous forward entries/outcomes yet. No automatic profit collection, live trades, orders or independent OOS GO. At least 60 truly nonoverlapping episodes and 12 UTC weeks, likely far slower than desired for a 4h infrequent Parent strategy, plus funding/mark/executable sources and outcome-independent receipts; insufficient observations = FORWARD_INSUFFICIENT.

**Verdict: PUBLIC_MEXC_FEASIBILITY_SOURCE_PASS (one-shot 100 USDT depth only), F1 EXACT FUNDING SOURCE_BLOCKED (HTTP451), F1B SEPARATE PROXY NOT EXACT, FORWARD_NOT_ACTIVATED, TRADING_AUTHORITY NONE.**
