# Crypto Lab — Bybit L1 vs L50 source reliability V2.2

**Source-only science, never a trading system.** Branch stacked on PR #336; earlier PRs/holdouts and `main` untouched.

The official Bybit V5 public feed documents L1 unchanged snapshot repeats up to 3 seconds and nominal L50 20ms push, but level 50 requires correct snapshots + deltas. This study freezes source-only comparison of A=L1 V2.1 changed-u freshness, B=L1 repeat-refresh diagnostic, C=L50 reconstructed book. Same public MEXC full-depth source, same receive-time 1-second causal grid. It does **not** change historic V2.1 source verdict, trading strategy, cost model or signal rules.

## Reproduce
No network needed for tests or raw replay:

```sh
python -m unittest discover -s research/source_reliability_v22 -p 'test_*.py' -v
python research/source_reliability_v22/audit_receipts.py PATH_TO_EXTRACTED_EVIDENCE/v22_evidence
```

Single permitted captured GitHub run: [Actions #41976298621](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41976298621). It was started with frozen source SHA `728c00188975616f0366e98189c63ab557e65e8e`, one bounded 600-second UTC receive-order public capture. Artifacts with raw source, manifest and report have finite retention; SHA256 and forensic verdict should be preserved before expiry.

## Limits not obscured by good tests
- Delta `u`/cross-sequence monotonicity cannot, by itself, certify that every intermediate WebSocket message arrived. Neither a local SQLite journal nor increased message frequency proves native broker fills. L50 cannot become an order/risk source without stronger gap/reconstruction parity and independently verified account/execution mechanics.
- One 10-minute comparison does not establish stable two-hour reliability, liquidation event rate, net PnL, source availability at crucial entry times or 14-day economic power. It is allowed to suggest a **future independent source study** only.
- If source gates fail, report SOURCE_COMPARE_NO_GAIN/BLOCKED with raw proof; do not weaken the predeclared 95% and +5pp thresholds or retroactively repair V2.1.
- No real orders, exchange keys, auth, premium services, leverage, recurring background tasks, merges or new PnL.
