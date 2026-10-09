# CRYPTO LAB — DUAL MINE ECONOMIC ATTACK: BTC CONVEX vs LICP, 2026-10-09

## Authority and scope
Operator approved scientific historical testing without mandatory waiting for future events. This closeout is a research audit of **previously opened 2021–2025** material, with one new, separately frozen counterfactual portfolio-risk replay on 13 assets, NOT a new untouched OOS. No original freeze modified. No real orders, accounts, private exchange requests, wallets, main merge or new capital/trading authority.

## A. BTC Convex V5 — actual new historical test, 13 assets
Source: archived **canonical** original Parent trade ledgers from Actions runs 35918769969 (ETH/SOL/BNB), 35921780080 (XRP/DOGE/ADA/LINK/AVAX), 35956632021 (original Parent benchmark LTC/BCH/TRX/DOT/UNI). Every original trade originally costed at 10 bps commission per side, BASE 2 bps adverse slip per side, or original STRESS 5 bps adverse slip per side, plus historical futures funding. **Different BASE/STRESS stops and trade paths retained**, not force-joined.

Prospectively published *for this new already-exposed-sample diagnostic*:
- freeze `RISK_NORMALIZED_PRE_REPLAY_FREEZE_2026_10_09.md`, commit `45dc735d4231fbb93c306a322f91a97dd21ba195`;
- original trade net-return normalized by archived `return_pct/100` (the original code defines exactly `return_pct=100*net_pnl/(qty*entry)`); qty itself is NOT archived;
- planned per-position risk 0.25% OR 0.50% of a **shared 10,000-USDT model equity**, using 4% original price stop + 24bps base fee/slippage risk-planning allowance (4.24% assumed loss/notional; NOT a guaranteed stop);
- max 3 simultaneous positions, max 1% aggregate *planned* risk, deterministic timestamp ordering and alphabetical simultaneous signals; skip any entry violating limits;
- original BASE, original STRESS, +20bps roundtrip adverse friction applied additionally to BASE;
- adversarial removal of exactly top 3 historical BASE net winners per asset and full chronological replay (BASE paths only);
- compare FIRST, SECOND, THIRD and ALL13, no favorable after-test coin dropping;
- same-hour entry + low-based stop path retained via deterministic subbar priority (exits from existing positions, new OPEN fills, same-bar STOP), without invented 1h intrabar quote chronology.

Technical fail-closed attempts and transparent corrections (no science changes): 
- run 37896476055: original archived trade receipt has `return_pct` not `qty`;
- run 37896637419: BASE/STRESS legitimate divergent stop/timestamp paths, cannot false-match by index;
- run 37896763252: original engine permits OPEN/STOP same 1h bar, dual event timestamp needs explicit subbar ordering;
- successful canonical corrected run **37896908699**, commit `e3ec876a0e7a058fd1a2c6a8caae00f21f777c33`, artifact **11600701586** (convex-risk-v01-13-assets-economic-replay), 9 synthetic invariants PASS and all original trade artifacts downloaded.

### Shared-account cumulative 2021–2025 results, from the new replay

| Original fixed portfolio | BASE risk .25% | Original STRESS .25% | BASE +extra20bps .25% | BASE risk .50% | Original STRESS .50% | BASE +extra20bps .50% |
|---|---:|---:|---:|---:|---:|---:|
| FIRST ETH/SOL/BNB | +34.5961% | +33.6847% | +28.9609% | +20.0803% | +16.9500% | +13.9948% |
| SECOND XRP/DOGE/ADA/LINK/AVAX | -25.6025% | -27.7075% | -31.0778% | -41.0605% | -42.7089% | -46.7378% |
| THIRD LTC/BCH/TRX/DOT/UNI, original Parent, not H2 | -5.7024% | -6.9613% | -11.2607% | +7.4741% | +6.6699% | -1.6198% |
| **ALL13** | **-4.1129%** | **-6.8088%** | **-12.4193%** | **-15.9287%** | **-18.0875%** | **-25.2891%** |

Cumulative 5-year simulated returns, NOT yearly percentages. FIRST .25% case: 365 taken /0 skipped, +34.5961% total, 19 consecutive losing exits, PF 1.4207, win rate 24.11%, average winning scaled PnL / avg losing 4.472, **realized closed-trade DD -6.9035%**; 2022 realized year -554.57 USDT. FIRST .50% case: 221 taken /144 deliberately missed due risk budget, +20.0803% cumulative, 20 consecutive losing exits, realized-only DD -13.4996%. Equity/risk management affects trade count substantially.
FIRST .25% adverse DROP_TOP3_PER_ASSET: 356 trades, +2.83143% total and PF 1.0393, realized-only DD -7.2150%, 24-loss streak; .50% +1.5279%/PF1.0173. **These near-break-even artificial tests are NOT adequate safety margins**, especially 5 years and missing execution/capital costs.
SECOND .25% original BASE: -25.6025% and realized-only DD -29.3266%. ALL13 .25% original BASE: 771 taken /1057 skipped, -4.1129%, PF 0.9743, realized-only DD -22.5626%. At .50% all13 -15.9287%, realized-only DD -32.8014%.
Note historical **per-asset** additive original top3 subtraction was previously negative all 3; this new full portfolio +2.83% counterfactual is not contradictory: re-capitalization, shared timing, and replacing the removed winning trades change later position sizes and compounding. It does not mean that the first 3 winners could have been predicted or safely skipped.

**Critical**: These calculated DDs are only after *closed* trades, not 1h mark-to-market. Original Parent high-exposure bar mark-to-market DD was -54% to -59% in first basket. We cannot claim true risk-sized MTM max DD or price gap risk from archived trades. Risks for lower-size account remain unknown until intratrade marks/fill records are modeled.
**Historical decision: FIRST BASKET RISK_SCENARIO_POSITIVE_IN_SIMULATION; SECOND/ALL13 FAIL; local PASS previously opened and NOT transferable/universal.** Lower risk sizing improves exposure but cannot create directional edge. In particular, +34.6% over FIVE years is not a reliable high income stream.

### Material improvements from this attack
1. Preserve the Parent signal exactly and all 13 original coins in generalization tests. Static code shows that original z-score < -2 and Bollinger lower-band checks are (away from floating-point boundary) the same condition, so the "4-factor" count includes one redundant measurement; prove any logic simplification equivalence in full candle data before using it.
2. For any new distinct strategy freeze, prefer **lower predeclared risk per trade** with aggregate correlated risk budget rather than 95% notional, and do not force increased risk when it loses opportunities. .25% appears more favorable in the **already-seen** first basket but this is NOT evidence it was ex-ante optimal.
3. Rebuild bar-level marked-to-market portfolio replay and exact 1-hour intrabar stop sequencing from historical high/low and then quote/tick if available, including physical min lot, funding, path gaps and realistic fill delay. Do NOT call this completed in V01.
4. Verify executable fee+spread/slip tiers from candidate venue using public timestamped quote archives. Original Binance parent historic results are not MEXC executable net returns; don't claim source transfer.
5. Enforce negative generalization verdict and don't rescue failed baskets or 2026 losing early sample by selecting symbols after seeing outcomes. We have no independent new OOS in this session.

## B. LICP BTC-liquidation → SOL short, exact transfer constraints and economics
Existing historical locked holdout XALT-003: 35 valid Nov/Dec2025 BTC ignition episodes from pinned Hyperliquid event archive, target Binance Vision SOLUSDT **1-minute OPEN proxy**; SHORT entry `t0 + 6 minutes`, exit +60m; pooled gross +25.071392bps and proxy ceiling after a *fixed* 16bps transfer hurdle **+9.071392bps**. November gross +2.707481bps (n15); December +41.844325bps (n20). This original scientific result is HISTORICAL_HOLDOUT_SURVIVES **WITH PROCEDURAL DEVIATION** documented: a duplicate canonical rerun occurred with byte-identical science, zero extra independent evidence. It is NOT a MEXC fill ledger.

New linear **sensitivity only**, re-arithmetized from *documented averages*, not event-by-event market-data test. Additional slippage/other expense above the already assumed 16bps modeled hurdle:

| Total roundtrip friction | Pool average after cost | Nov average after cost | Dec average after cost |
|---|---:|---:|---:|
| 16bps (original proxy hurdle) | +9.0714bps | -13.2925bps | +25.8443bps |
| 21bps (+5) | +4.0714bps | -18.2925bps | +20.8443bps |
| 26bps (+10) | -0.9286bps | -23.2925bps | +15.8443bps |
| 36bps (+20) | -10.9286bps | -33.2925bps | +5.8443bps |

**Break-even** historical proxy total friction ~25.0714bps, i.e. only ~9.0714bps *unmodeled* cost headroom beyond 16bps. November does NOT pay the original fixed cost, December sustains the pooled positive net. Not proof of after-cost profitable execution.

Forward XALT-004 uses a DIFFERENT sensor: Bybit BTCUSDT allLiquidation, Binance BTCUSDT forceOrder confirmation, MEXC SOL_USDT public executable BBO. Forward signal observes confirmation then waits **60 seconds** and enters SHORT at MEXC BID, exits at MEXC ASK 60 minutes later. **Not historical Hyperliquid event + six-minute Binance proxy timing.**
Existing 4 forward outcomes net after 16bps: +23.1504, +10.7782, -5.0994, -74.0124bps; mean -11.2958bps, gross mean +4.7042bps before 16bps fee hurdle. It could only break even in this tiny set if total friction were less than ~4.7042bps, which is not what the frozen source supports. A -74bps event contradicts the assumption that one can guarantee "small spoon losses".
**Transfer historic scientific verdict**: positive coarse proxy **cannot** establish profit or equivalent latency/detector execution on MEXC. Data-only historical reconstruction of both causal source event streams with point-in-time MEXC BBO and matched timestamp logic is the legitimate distinct next experiment, not the original sealed holdout reopening. Historical 35 event-level cash and quote data are NOT retrievable from the original canonical Actions artifact listing through the available connector, so no new independent LICP event distribution/median/PF/stop test was done here.

## Operator decision / economic shortlist
**1 — BTC Convex**: choose it for *scientific executable feasibility work*, not paid deployment. Fixed initial candidate ETH/SOL/BNB already known from historical outcome and therefore must be labeled scope-limited; 0.25% risk and +20bps historical scenario are positive but 5-year CAGR, realistic marked DD, missed-winner tail and present exchange executions remain inadequate to call it a live money machine.
**2 — LICP**: source transfer and economic-cost headroom are the critical blockers. No time-delay re-selection on the already opened XALT-003 holdout. Its 16bps historical proxy is fragile to another 10bps of adverse costs and the Nov/Dec regime difference.

Neither has proven robust future executable net edge. Historical science approved for the original local/historical scope; real trading NOT authorized by this report. Preserve unchanged 2026 losses and original closeouts.

## Exact source URLs
- New all 13 historical risk replay (SUCCESS) https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37896908699
- Frozen original BTC first basket https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35918769969
- Expansion FAIL https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35921780080
- Third basket H2 original https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35956632021
- LICP canonical historical https://github.com/joseluisvieira28-oss/Laboratorio/blob/liquidation-cascade-propagation-v0.1/research/liquidation_cascade/LICP_HIST_XALT_003_CANONICAL_HOLDOUT_RESULT_V0_1.md
- LICP procedural deviation https://github.com/joseluisvieira28-oss/Laboratorio/blob/liquidation-cascade-propagation-v0.1/research/liquidation_cascade/LICP_HIST_XALT_003_HOLDOUT_INTEGRITY_AUDIT_V0_1.md
- LICP forward baseline https://github.com/joseluisvieira28-oss/Laboratorio/blob/licp-canonical-continuation-2026-10-08/research/liquidation_cascade/LICP_FWD_XALT_004_FORWARD_BASELINE_V0_1.md
- BTC Convex Oct9 current 2026 read-only https://github.com/joseluisvieira28-oss/Laboratorio/blob/ops/btc-convex-v02-readonly-verdict-2026-10-09/audits/BTC_CONVEX_V02_READONLY_VERDICT_2026_10_09.md
