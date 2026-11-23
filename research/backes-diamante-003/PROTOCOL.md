# BACKES-DIAMANTE-003 — Forensic attribution + prospective observation (NO TRADING)

**Pre-commit:** 2026-11-23 (Europe/Zurich). Predecessor BACKES-002 frozen in source code hash b8895efb4a36c4c2c2e70fe2cab1738358eda2aa and original 384 ZIP artifact hash 735fff332994ce546f56258a01787d7f250203efa701586fa24eefd553f1ecaf.

## Historical attack
Reuse BACKES-002 source, data cutoff 2026-11-22 and exactly its pivot and 4-week relative momentum rule. No tuning. Decompose cumulative ROT/BTC return into additive weekly log excess, contiguous allocation episodes, best/worst contributing weeks, realised market regimes labelled DESCRIPTIVE ONLY, and source hash manifest. Verify that attribution reconstructs predecessor results; fail closed on data gaps.

The strategy was invented by Crypto Lab using public topics discussed by Augusto Backes. This is NOT Backes' private method, not verification of his personal trading record, nor predictive proof.

## Prospective attack
First eligible snapshot: **Monday 2026-11-30**, no earlier (Monday 2026-11-23 already started before this protocol was frozen). Capture one historical-data snapshot of fully closed ETHBTC 1w weekly candles from Binance public REST and subsequent executable bid/ask for BTCUSDT and ETHUSDT. Keep timestamped raw source hashes, weekly cutoffs, frozen signal, market mid/ask, and timestamp of each API read. Outcome is **not** an exchange fill and no user wallet is touched.

The prospective position decision is timestamped at the ACTUAL observation instant **after Monday 00:00** and must NEVER claim that an earlier Monday-open execution was feasible. It is an independent delayed-observation implementation of the same analytical signal, not an exact replication of BACKES-002's Monday-open fill. A change from daily-aggregated to native 1w Binance bars is explicitly tracked as SOURCE_VARIANT risk.

At least 8 consecutive weekly snapshots required for a diagnostic pulse; minimum 26 consecutive valid weekly observations for candidate research only. Neither is enough to approve live capital. Run every Monday approximately 00:30 UTC (01:30 Zurich in winter) on a trigger request. If outside timing window or source inaccessible: produce SOURCE_BLOCKED and do not create a backfilled signal.

## Why separate historical and prospective
The 2025–2026 winning episodes have already been viewed. Segmenting winners may be diagnostic but is by definition post-outcome and must never select new parameters and then claim these old data are out-of-sample.

## Guardrails
No trading API keys, no account access, no purchases, no funds, no subscriptions, no margin, no order placement, no claims of profit. GitHub Actions may run only static Python read-only jobs. Results uploaded as artifacts. Named GitHub request files create explicit audit trails. Failed days/weeks may not be silently rescued via hindsight. Economic **NO-GO** until truly prospective independent confirmation, account-level fee/slippage model, cash-vs-risk-adjusted benchmark comparisons, and drawdown/risk limits.
