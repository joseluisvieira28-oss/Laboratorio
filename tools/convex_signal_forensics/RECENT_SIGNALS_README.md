# CONVEX 10 — recent signal receipts, Windows offline only

Reads only metadata from three local existing SQLite outboxes (V07/V11/V12). It does not read message content, prices, balances, keys, account files or Telegram tokens. It does NOT request network, restart Windows tasks, trade, edit outboxes, or alter any installed EXEs.

1. Extract the GitHub Actions artifact into a NEW folder.
2. Check `SHA256_EXE.txt` matches `Get-FileHash .\CONVEX_RECENT_SIGNAL_RECEIPTS.exe -Algorithm SHA256`. A SHA256 matching its accompanying manifest proves package integrity only, not an independent publisher signature.
3. Run `.\CONVEX_RECENT_SIGNAL_RECEIPTS.exe --self-test` and expect `RECENT_SIGNALS_OFFLINE_SELFTEST_PASS`.
4. Run `.\CONVEX_RECENT_SIGNAL_RECEIPTS.exe --limit 30` in the same folder. You may paste the JSON in ChatGPT; it contains ONLY signal IDs, assets, UTC close, local outbox sent flags, stored numeric Telegram message IDs (when available), and same-symbol overlap markers. No credentials/account details. Audit program does not upload anything.
5. Keep the three Windows Scheduled Tasks running throughout. If endpoint protection prevents an unsigned EXE, stop and seek IT approval; do not bypass security settings.

Interpretation: outbox `sent=true` is only a local persistence marker. V07 and V11 V2 may store the numeric Telegram ACK ID. V12 PR239 cannot store that ID. Do not convert any signal into an automatic/manual real-money order solely from this metadata. No stop order, 1x/10x risk or profit is proven.

Limitations: Rows from earlier cycles might have been deleted or caches expired; no candle replay is performed by this collector. The previous independent two-signal forensic tool at PR #241 handles the exact 20:55 V07 and V12 pair. For general additional signals, the next gate is causal OHLC reconstruction (timestamped) and out-of-sample costed execution evaluation, not post-outcome SL/TP optimization.