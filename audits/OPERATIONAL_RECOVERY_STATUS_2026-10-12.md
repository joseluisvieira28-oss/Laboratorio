# Crypto operational recovery — 2026-10-12

Authority: autonomous operational recovery only. No main merge, trading/account/order/wallet actions, spending, scientific retune, backfill or unsealing before frozen gates.

## Verified results
- Multi-Stable original readiness recovered via job-only rerun, run 37780604059 attempt 2, job 114710002904: 9/40 admitted baskets, 2/7 dates, BTC 3/10, ETH 6/10, max-date share 66.7%, no conflicts. PROSPECTIVE_ACCUMULATING, economic_metrics_opened=false. Original artifacts unchanged. 360/360 valid-trigger scans excludes malformed missed Oct08 01–03:59 JSON under the unchanged frozen parser. This gap remains a separate operational limitation and must never be hidden.
- USOPEN operational branch ops/usopen-window-recovery-2026-10-12 preserves scientific collector blob 7fb57c214b4e8dd250bbb24337d48f4afedf439a. 8/8 synthetic DST/window tests PASS. Run 38222918013 SUCCESS correctly NOOP outside 09:00–09:10 / 11:00–11:10 America/New_York. First eligible source capture has not yet occurred. Prior missed dates remain missed.
- Aave HF operational branch ops/aave-daily-source-recovery-2026-10-12 preserves collector blob 3e505b4cc85cbcd25c4e9a5e9e426c5090227eda and original technical amendment V0.1A (limit=10). Run 38221678561 SUCCESS, actual Oct12 08:10:12 UTC snapshot: 102 reserves, 488/488 valid HFs, zero holder/summary errors. ROLLUP 3/30 valid days, median coverage 100%, outcomes closed, q90 not computed.
- Exitflow branch ops/exitflow-actual-hour-recovery-2026-10-12 preserves G3 science and copies original six eligible hours plus pilot data. Run 38221745465 SUCCESS appended actual Oct12 08 UTC receipt, 178 markets, source SHA256 cc7527a73906e8afa9e26483bf97afb3c6c243bd234887f32f2cc28a80fcac00. No backfill. Original G3 window Oct10–23 / >=320 hours / >=14 dates is untouched. Extensive missed hours remain; recovery does not rescue coverage. Do not finalize before Oct24 UTC.

## Source branches and links
- https://github.com/joseluisvieira28-oss/Laboratorio/tree/ops/multistable-original-evidence-recovery-2026-10-12
- https://github.com/joseluisvieira28-oss/Laboratorio/tree/ops/usopen-window-recovery-2026-10-12
- https://github.com/joseluisvieira28-oss/Laboratorio/tree/ops/aave-daily-source-recovery-2026-10-12
- https://github.com/joseluisvieira28-oss/Laboratorio/tree/ops/exitflow-actual-hour-recovery-2026-10-12

## Ongoing scope / gate boundaries
Only actual future source receipts may be appended. A single thread heartbeat may update the operational TICK files only when due and no matching job/receipt exists. It must use real UTC and DST-aware NY time, not fake timestamps or FORCE_PHASE. Canonical branches remain preserved; recovery branches retain inherited source data and exact original scientific code. Keep provenance of this operational handover; do not aggregate duplicate inherited records across branches.

USOPEN: first 30 completed eligible dates plus original PF/bootstrap/month/concentration gates. Stop after terminal; no repeated economic decisions. Aave HF: 30 valid dates, each >=20 HFs, median coverage >=80%; ready-to-freeze is calibration only, not economic edge. Exitflow: terminal source audit after Oct24, not economic adjudication. Multi-Stable: economics sealed until every existing gate passes; never silently remove missing schedule windows. LICP: keep existing active canonical watch without duplicate shards or a second writer.

Pending further diagnosis: Overshoot exact-point coverage; Radar public health and source archive failure; Aave governance partial proofs; Options/liquidation/RR calibrations. DLS 2025 and INDEX are terminal/closed and will not be resurrected. TVFP terminal PASS_STRONG remains a measurement-only result. Triple verified build remains unarmed by this work.

Quiet while unchanged; notify only meaningful operational change, terminal scientific result, failure or required user intervention. This status is a progress receipt, not a declaration that all candidates recovered or that any economic survivor exists.

## Confirmed follow-up and Radar root cause

Hourly heartbeat `crypto-recupera-o-at-veredito` is ACTIVE on this chat, at minute 01. It keeps no-change periods quiet and stops after the first new legitimate scientific terminal verdict. USOPEN still needs actual entry/exit captures; a passing NOOP transport test does not meet its sample gate.

Draft PRs, unmerged and targeting original scientific branches:
- USOPEN: https://github.com/joseluisvieira28-oss/Laboratorio/pull/190
- Aave HF: https://github.com/joseluisvieira28-oss/Laboratorio/pull/191
- Exitflow: https://github.com/joseluisvieira28-oss/Laboratorio/pull/192

User explicitly confirmed Render workspace Laboratorio / tea-daffqvgu01pc73a9sad0 on 12/10. Read-only service and event evidence confirms **billing suspension**, 2026-10-11T02:35:41.415974Z; suspender_added event evt-db5fbvbm8hqs73c55cp0 (actor Billing), service_suspended evt-db5fbvbm8hqs73c55cpg. Service remains plan free / suspended; no billing balance or exact quota reason inferred. No paid upgrade, extra service, redeploy or second writer permitted as a workaround.

Public diagnostic run 38224423382: HTTP 503 text/html, body 243 bytes, no JSON. Original health classifier remains DEGRADED; diagnostic SUCCESS is not runtime health PASS. Full proof on branch ops/radar-public-health-diagnosis-2026-10-12 at audits/RADAR_BILLING_SUSPENSION_ROOT_CAUSE_2026-10-12.md.

Last original Render log snapshot reviewed: checked_at_utc 2026-10-11T01:46:13.535Z, deployment d645891a588c594b69f41938263cc4066652aa9b, immutable event count 2723 as reported by runtime. OPTIONS 20/50, base descriptive -26.5982494 bps, stress -36.5800472 bps; CED 14/60 and 1/8 weeks, WAITING_SOURCE_ARCHIVE. These are historical runtime-reported values, not current account PnL or independently recalculated database results. Q4 ETF economic outcomes remain sealed.

Main rechecked unchanged at 75fb36c8337c3221b7551c513e049cd472dad231. Scientific collector/protocol files unchanged in recovery comparisons. No claim that every candidate is operationally recovered.
