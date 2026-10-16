# CONVEX 20:55 UTC — Forensic read-only Windows operator

**Only two exact historical signal IDs** are audited:
- SOL_CONVEX_NATIVE_5M:1792097700000 (V07)
- BNB_CONVEX_NATIVE_5M_EXPERIMENTAL:1792097700000 (V12)
- UTC close: 2026-10-15T20:55:00Z

The standalone CONVEX_SIGNAL_2055_FORENSIC_V03.exe reads only the installed V07/V12 **public-market cache JSON** files, existing **pre-upgrade backup** caches and two SQLite outbox rows. NO network, Telegram sends, orders, broker auth, or DPAPI access. Do not copy or upload SQLite files, secrets or credential stores. The report is JSON (SHA256, booleans, message_id, timestamps; no prices, raw message bodies, account balances or tokens).

## Operator instructions

1. Download the **verified Windows artifact** from this branch CI and extract in a new Downloads folder. Do NOT run EXEs from unverified sites or bypass enterprise restrictions without IT approval.
2. From PowerShell in the EXE folder, run:
    Get-FileHash .\CONVEX_SIGNAL_2055_FORENSIC_V03.exe -Algorithm SHA256
    Compare to SHA256_EXE.txt in that artifact (integrity, **not** a publisher signature).
    .\CONVEX_SIGNAL_2055_FORENSIC_V03.exe --self-test
    .\CONVEX_SIGNAL_2055_FORENSIC_V03.exe
3. Paste the sanitized **JSON output only**, not database or raw cache files. The tool does not send data itself.
4. Leave V07/V11/V12 Windows scheduled tasks running. NEVER stop/restart them, change main, or reset SQLite/outbox for this audit.

If the unsigned EXE is blocked, stop; no global ExecutionPolicy changes are requested. On a system with Python 3.11 and a local checkout, alternative: python -m tools.convex_signal_forensics.forensic_2055.

## V03 SOL-source disagreement diagnostic

The first audit found that V07 SOL and V12 SOL both reconstruct a complete 12,576-candle 5m window with **zero internal cache conflicts**, yet the two sources have different window hashes. Do NOT interpret V07's true V5 flag as independently source-parity-proven.

V03 extends `cross_observer_diagnostic` for SOL and BNB:

- `mismatched_candles`: number of differing 5m rows between the observer windows, not number of Telegram messages.
- `mismatched_open_times_utc_first_12`: UTC candle-open timestamps of the first twelve discrepancies; does not reveal prices. `mismatched_times_truncated` flags larger lists.
- `max_close_relative_difference_bps` and `max_volume_relative_difference_pct`: maximum relative differences without revealing original values; they may still reflect floating-point formatting/retrieval differences and do not attribute cause.
- `pinned_v5_signal_features` on BOTH observers: original parent score and regime/rsi/z/bollinger/volume boolean votes at the signal candle, without OHLC prices. A true signal on both sources does NOT certify source equality.
- `first_mismatch_open_utc` / `last_mismatch_open_utc`: when divergences occur; these timestamps are bar *opens*, not signal closes.
- `field_mismatch_counts`: open/high/low/close/volume differences by count, **never** reveals market prices.
- `signal_candle_2050_exact_match`: whether the particular 20:50 candle closing at 20:55 is identical.
- `recent_last_20_candles_mismatched` and `recent_last_200_candles_mismatched`: whether discrepancies overlap recent indicator windows; RSI14 Wilder can remain dependent on older history, so 0 differences over last 200 is not complete signal-equivalence proof.
- `independent_other_observer.pinned_v5_replay_five_minute_signal`: whether re-running pinned V5 on *the other* observer window reproduces a true flag. Matching flags alone do not restore source parity.

This program does not patch market cache data, make Binance requests, or change trading logic. In case of local Windows endpoint policy block, STOP rather than bypass.

## Interpretation

- exact_window_reconstructed=true means 12,576 continuous canonical 5m bars from joined local pre-event backups + later live cache, ending on the 20:50 opening bar, closed at 20:55 UTC.
- overlap_conflicts=0 means old/new snapshots agree on all overlapping candles for that observer.
- full_source_parity_at_exact_close=true means **independent V07/V12 local USD-M Binance caches** reconstruct precisely the same 12,576-bar window. It still cannot prove Binance originally served them truthfully.
- pinned_v5_replay_five_minute_signal=true means the pinned parent V5 source engine emits a flag on that exact reconstructed 5m window (operational causal replay, not an independently validated profitable trade).
- sqlite.found=true and db_marked_sent=true mean exact row is present and the local outbox marked it sent.
- V07 V2 has telegram_message_id, if API ACK was persisted. Compare that numeric ID to **Telegram message ID** from the operator client, if available.
- V12 PR239 persists sent_ms, but **does not persist the Telegram API message ID**. Visible delivery corroborates; no precise persisted API ACK↔SQLite receipt for V12.
- If any gate returns null, false, MISSING, or NOT_YET_PROVEN, **do not change strategy parameters and do not label the signal fake**. Investigate missing evidence first. Moving-window cache may have lost old bars. No historical replay on external outcomes and no claim of profitable edge.
- Previous telegram_sent_this_cycle=0 values captured after 20:55 do not negate earlier sends. V07's field is telegram_outbox_pending, not telegram_pending, and lacks the signal_events counter in its status schema.

This verifier is strictly observation-only. No live MEXC or Telegram test is authorized.
