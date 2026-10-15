# CONVEX 20:55 UTC — Forensic read-only Windows operator

**Only two exact historical signal IDs** are audited:
- SOL_CONVEX_NATIVE_5M:1792097700000 (V07)
- BNB_CONVEX_NATIVE_5M_EXPERIMENTAL:1792097700000 (V12)
- UTC close: 2026-10-15T20:55:00Z

The standalone CONVEX_SIGNAL_2055_FORENSIC.exe reads only the installed V07/V12 **public-market cache JSON** files, existing **pre-upgrade backup** caches and two SQLite outbox rows. NO network, Telegram sends, orders, broker auth, or DPAPI access. Do not copy or upload SQLite files, secrets or credential stores. The report is JSON (SHA256, booleans, message_id, timestamps; no prices, raw message bodies, account balances or tokens).

## Operator instructions

1. Download the **verified Windows artifact** from this branch CI and extract in a new Downloads folder. Do NOT run EXEs from unverified sites or bypass enterprise restrictions without IT approval.
2. From PowerShell in the EXE folder, run:
    Get-FileHash .\CONVEX_SIGNAL_2055_FORENSIC.exe -Algorithm SHA256
    Compare to SHA256_EXE.txt in that artifact (integrity, **not** a publisher signature).
    .\CONVEX_SIGNAL_2055_FORENSIC.exe --self-test
    .\CONVEX_SIGNAL_2055_FORENSIC.exe
3. Paste the sanitized **JSON output only**, not database or raw cache files. The tool does not send data itself.
4. Leave V07/V11/V12 Windows scheduled tasks running. NEVER stop/restart them, change main, or reset SQLite/outbox for this audit.

If the unsigned EXE is blocked, stop; no global ExecutionPolicy changes are requested. On a system with Python 3.11 and a local checkout, alternative: python -m tools.convex_signal_forensics.forensic_2055.

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
