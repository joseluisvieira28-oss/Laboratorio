# CONVEX V03C — ARCHIVE SIZE-CAP TECHNICAL SOURCE REMEDIATION FREEZE (17 OCT 2026)

This amendment freezes exclusively TECHNICAL SOURCE TRANSPORT before opening any of the blocked original 2023–24 entry quotes. Research only; all economic strategy rules and population frozen from V03B.

## Immutable predecessor and why the initial 33+6 source gate was insufficient
Canonical V03B run 39026521571: SOL 33 entries, 11 fresh quote checks, 8 best-ASK-size sufficient, 1 no past quote and 21 status SOURCE_BLOCKED; BNB 6 entries, 3 fresh, 2 size-sufficient and 3 status SOURCE_BLOCKED.
Artifact-only root-cause run 39026910122 found **every** blocked source file resulted from OUR explicit prior resource caps: SOL 13 `PUBLISHER_ARCHIVE_TOO_BIG` + 5 `UNZIPPED_SIZE_CAP` days (21 blocked trade entries because some days contain two trades); BNB 2 compressed + 1 uncompressed limit. None is proven an official publisher missing file/HTTP451 failure.

## Exactly scoped remediation: NO NEW SCIENCE, NO SELECTION
- **Download and open ONLY source days originally marked `SOURCE_BLOCKED` for resource-cap reasons** in the EXACT immutable V03B run artifacts. Do NOT touch historical days with accepted SHA / fresh quote / insufficient quote / no prior quote.
- Recover exact same SOL1h 33 and BNB4h 6 original 2023-05-16 to 2024-03-30 entry timestamps from immutable ORIGINAL publisher-SHA-verified 8ALT trade artifacts in run 38432883246. Require SHA-bound original V03B original ledger fingerprint, exact 33 or 6, and original first two records parity. Require each failed-day original error string to be one of exactly `ValueError:PUBLISHER_ARCHIVE_TOO_BIG` or `ValueError:UNZIPPED_SIZE_CAP`. No other errors silently retried.
- Same official archive URL, same sibling publisher .CHECKSUM, same STRICT past-only `event_time <= entry_ms` last book update rule, quote age <=2000 ms, ask quantity >= modeled BASE quantity, same V5 old modeled entry and qty. All original 33 + 6 slots preserved. No retrospective PnL retuning. Raw archive byte cap increased once from 85MB to **320 MB**, uncompressed ZIP member cap from 500MB to **2,500 MB**, timestamped event count cap from 8 million to **35 million**. Memory never holds archive: stream 4 MB chunks to one temporary disk file and compute SHA256 incrementally. Enforce max bytes during stream, not after. One official publisher ZIP GET and one sibling checksum GET per target date, zero retry, no source or region bypass; discard after the check. Never download same accepted day again.
- Keep a *single* bounded archive on disk at a time; verify one CSV member, no zip-slip writing, CSV parse incrementally, fail-closed on missing/bad field names, invalid/crossed price/negative qty, out-of-day or decreasing timestamp, nonfinite price, checksum mismatch, too-large date. No alter to scientific thresholds.
- Output both exact original historic receipts and V03C per-date remediation receipts (with original source artifact SHA256 and new publisher ZIP hashes), complete 33+6 denominator, source age / size status and outcome-blind missing episodes. Report separately **repaired-date coverage** and overall new full-population coverage. V03B result remains canonical for first source pass, V03C a separate amendment; do not erase historical blocked state.
- Fixed predeclared source classification thresholds from V03B still unchanged: >=95% fresh quotes <=2s and >=90% best ASK quantity sufficient **per symbol**. Zero OOS/alpha/trading authority even if satisfied. Native stop ACK unresolved.
- If remaining source ZIP exceeds new fixed limits or HTTP error occurs, classify `SOURCE_STILL_BLOCKED` and STOP further iterative size enlargement or additional API source family without separate new freeze. No infinite escalation.

## Literal origin
- Official Binance public publication stop circa 2024-03-30: https://github.com/binance/binance-public-data/issues/334
- Exact initial BNB+SOL V03B market sampling run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39026521571
- Immutable error classification run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39026910122

**SCIENCE: ORIGINAL V5 NO CHANGES, 2026 HOLDOUT LOCKED, NO LIVE TRADING, NO EXCHANGE PRIVATE API, NO MAIN MERGE.**
