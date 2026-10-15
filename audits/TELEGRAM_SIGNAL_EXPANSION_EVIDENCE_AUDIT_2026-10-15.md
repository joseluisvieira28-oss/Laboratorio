# Telegram signal expansion audit — 2026-10-15

Decision: **3 V07 signal lanes implemented; 0 additional independently proven profitable or operational signal lanes activated.** Historical model PASS is not prospective net executable evidence.

## ACTIVE (existing V07, unchanged on operator Windows)
- SOL_CONVEX_NATIVE_5M — SOL LONG signal observations
- SOL_CONVEX_1H — SOL LONG signal observations
- BNB_CONVEX_4H — BNB LONG signal observations
Only after completed-bar source checks; messages explicitly say signals are NOT ORDERS. Public feed V07 supports SOL and BNB; no proven original Binance archive parity or MEXC execution edge.

## Historical-only Convex expansion candidates — NOT APPROVED ACTIVE
Source: CONVEX_8ALT_4TF_COMMON_2023_25_FINAL_CLOSEOUT_2026_10_13.md; 8 assets x 4 timeframes (32 strategy combinations, 64 BASE/STRESS results), fully source-validated 2023-25 historical simulation, not independent OOS.
- SOL 4H: +35.90% BASE / +35.42% STRESS; PF 2.025; top-3-winner-removed closed net -526.02 USDT (tail dependency).
- ETH 1H: +18.77% / +18.34%; PF 1.5396; top-3-winner-removed closed net -975.14 USDT (tail dependency).
- BNB 30M: +19.67% / +18.17%; PF 1.6009; top-3-winner-removed closed net +61.77 USDT (weak residual).
- DOGE 4H: +15.66% / +15.26%; top-3-removed -757.13 USDT (tail dependent; do not promote).
- XRP 15M: +18.43% / +14.95%; PF 1.1924; drawdown -22.76%; top-3-removed -2867.81 USDT (do not promote).
All LINK timeframes negative in this retrospective. No additional live or robust edge proved. Implementing these would require new frozen signal adapters, public source custody, 5m bar parity, dedupe/collision testing and separate clearly experimental Telegram labels.

## 8 RETIRED RADAR motors: not silently reactivated
October 13 zero-palha operation retired OPTIONS V2.1, TFG DONCHIAN, ETF-CME, BNB-LAUNCHPOOL, HTF-DH03, CED1D-0031, EMA6H, CIRV; 0 had account-fee-inclusive robust forward net executable edge. This is an operational retirement, not a scientific rejection of all future research in each family.
OPTIONS V2.1: Oct10 forward 19 cases mean gross -15.24882bps, mean base net -25.22966bps; current MEXC market/market fork economic NO-GO.
TFG: 12/12 forward observations -1R. ETF: Q4 holdout sealed until 2027-01-01, fragile OOS. CED: 14/60 with missing archives; BNB Launchpool: 0/25 prospective eligible. HTF-DH03, EMA6H and CIRV lack requisite evidence.

## Other research mechanisms: NOT alert-ready
LICP-HIST-XALT-003: 35-event protected historical net model +9.07bps, but forward XALT-004 first four mean -11.2958bps and needs 20 independent dates-qualified episodes. BTC-CONVEX v0.2: forward insufficient, 3 closed losses in Oct9 snapshot. BTC options VRP phenomenon exists without trade economics/source proof. BTC early-profit child historically worsened parent. Funding cash carry 24h, L2 passive and BOX USDC routes economically rejected or blocked.

## Future architecture (not deployed)
Keep main channel only for 3 existing V07 SIGNAL_NOT_ORDER notices. An experimental research-only secondary section could later cover SOL4H, ETH1H, BNB30M, but only after a separate deterministic source/parity implementation and explicit clear EXPERIMENTAL_NOT_VALIDATED labeling. Health notices separate from trade signals. No brokerage orders, no live entries, no change to Telegram V07 task, no merge main.

## Sources read
- cleanup/radar-zero-palha-retire-all-eight-2026-10-13/audits/RADAR_ZERO_PALHA_OPERATIONAL_RETIREMENT_2026-10-13.md
- audit/radar-continuity-net-edge-2026-10-10/audits/RADAR_CONTINUITY_NET_EDGE_TRIAGE_2026-10-10.md
- audit/options-v21-10x-final-truth-gate-2026-10-13/audits/OPTIONS_V21_10X_FINAL_EXECUTION_VERDICT_2026-10-13.md
- research/convex-sol1h-bnb4h-economic-source-gates-2026-10-13/audits/CONVEX_8ALT_4TF_COMMON_2023_25_FINAL_CLOSEOUT_2026_10_13.md
- audit/crypto-lab-net-edge-verdicts-2026-10-09/audits/CRYPTO_LAB_GLOBAL_NET_EDGE_VERDICTS_2026-10-09.md
- audit/three-convex-v09-real-live-go-gate-2026-10-15/audits/BTC_CONVEX_EARLY_PROFIT_001_CANONICAL_HISTORICAL_VERDICT_2026-10-14.md

Scope limit: evidence-led review of selected canonical closeouts, not exhaustive review of hundreds of research branches. No new backtest or Windows deployment.