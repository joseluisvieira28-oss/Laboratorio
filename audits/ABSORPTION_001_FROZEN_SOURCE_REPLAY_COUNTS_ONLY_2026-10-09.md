# ABSORPTION-FAILED-AUCTION-001 — RESTORED SOURCE FROZEN CLASSIFIER AS-OF 2026-10-09 11:00 UTC

**Operational stage: RESTORED_SOURCE_JOIN_PASS / REPLAY_DIAGNOSTIC_ONLY / NO PRIMARY EVENTS**
**Economic stage: NOT OPENED / NOT TESTED / NO TRADING AUTHORITY.**

## Immutable evidence links
- Render receiver active 2026-10-09 in workspace Laboratorio; telemetry recovered from `TVFP_RECEIPT` app logs. No webhook credentials exposed.
- All restored MM-V1 source continuity and payload/corpus/chain SHA256: [run 37921551326](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37921551326); 2036 5m bars 2026-10-02 09:25 to 2026-10-09 11:00 UTC, 2016 required prior bars, 20 potential following bar closes.
- Binance canonical SPOT aggTrades 2026-10-02..08 immutable 7 ZIPs, full archive SHA256 and 1903 restored Vault bars matched: [run 37922287209](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37922287209). 7,091,269 actual aggTrade records; total compressed data 104,199,387 bytes; source feature corpus sha256 `18750b490331240511bdb352080ce2b1bc30d2e441e4c23b1843109905803180`.
- 2026-10-09 **00:00–11:00 UTC bounded official Binance public aggTrades** source retrieved and joined using original vetted collector function: **233,623** aggTrade records, 238 public REST requests, no authentication or account data.
- Frozen `engine.classify` re-run UNMODIFIED over the 2036 genuine 5m bars with 2016 consecutive causal predecessors. Original `test_engine.py` regressions passed. [Successful source-only replay run 37922692085](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37922692085); [immutable receipt artifact 11613075574](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37922692085/artifacts/11613075574) (artifact ZIP SHA256 `90d0ebc8365d333190074d337ccedd4b677cd62e2429ea97c476f2148d897865`).

## First post-baseline event-time result — COUNTS ONLY
As-of snapshot: first admissible candidate 2026-10-09 09:25 UTC, last 11:00 UTC.

| Original frozen classifier event type | Result in 20 post-baseline bars |
|---|---:|
| NON_EXTREME | 20 |
| FAILED_AUCTION | 0 |
| EFFICIENT_ACCEPTANCE | 0 |
| Any other active candidate | 0 |

These are **20 event-time classified bars**, not economic trades and not profits. 20/20 NON_EXTREME is NOT evidence of positive or negative predictive edge. The original scientific terminal sample requirements remain >=100 FAILED_AUCTION, >=100 EFFICIENT_ACCEPTANCE, >=30 UTC dates and high coverage. Current recoverable candidate history is far too short and no future-return outcomes were opened.

## Strict interpretation and authority
1. This proves source capture, source consistency and the mechanical classifier can be replayed after a **real gap** using a new consecutive-2016-bar epoch. It is an authorized *diagnostic* source-only replay of originally prospective 5-minute receipts, not automatic promotion of event ledger entries.
2. Original canonical `absorption_failed_auction/forward/EVENT_LEDGER.jsonl` was **not modified**. Old 16 NON_EXTREME bars and their sealed authority remain untouched.
3. Source real gap before 2026-10-02 09:25 remains unfilled. Do not stitch old September/Oct01 sensor to new epoch without segmentation.
4. Last daily UTC snapshot 2026-10-09 is PARTIAL (133 receipts as of 11:00) and may be archived as a FINAL daily snapshot only when 2026-10-09 UTC day ends, using genuine additional Render messages. No backfilled or fabricated bars.
5. No continuous daily Render→GitHub archival exporter has been set up. Existing staged-archive GitHub Actions auto-hash only AFTER someone pushes raw daily log files. Durable prospective collection must fix this maintenance dependency or this blockage will recur.
6. Any upgrade from diagnostic source replay to the canonical forward ledger requires independent governance approval, coverage/restart provenance, deterministic collision policy and the **unmodified frozen** classifier/suppression rules. Never open economic returns before actual original minimum event/date/sample gates.
7. This finding is **NOT `MECHANISM_SURVIVES`**, `QUASE_DIAMANTE`, `MICRO-LIVE_GO`, `NO_EDGE` or `NO_MECHANISM`.

## Related independent liquidation forward
LICP-001 canonical V03 run [37919982538](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37919982538) completed technical PASS; 12 valid ledger receipts, no conflicts, 10 independent events over 2 UTC dates remain unchanged. `FORWARD_INSUFFICIENT`: 10/20 episodes, 2/3 dates. No modification to costs, freeze, or economic authority.

All changes confined to non-main research/audit/Vault branches. No trades, orders, balances, private exchange APIs, wallets, capital, merge, Render deploy or scientific parameter changes.
