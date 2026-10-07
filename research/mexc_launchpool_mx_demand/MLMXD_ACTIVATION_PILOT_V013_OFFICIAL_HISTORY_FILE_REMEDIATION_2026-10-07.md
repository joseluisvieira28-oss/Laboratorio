# MLMXD ACTIVATION PILOT V0.1.3 — OFFICIAL HISTORY FILE TRANSPORT REMEDIATION
Date: 2026-10-07
Status: TECHNICAL REMEDIATION; SCIENCE UNCHANGED

Parent scientific freeze:
MLMXD_ACTIVATION_PILOT_V01_PRE_OUTCOME_FREEZE_2026-10-07.md

Prior transport runs recovered only 2/14 frozen observations because the REST kline route did not expose the older 2025 windows.

A public official MEXC history-file route has now been identified:
- current public symbol registry: /api/platform/spot/market-v2/web/symbolsV2
- public history file listing: /file-svc/history/download
- daily 15m CSVs for MX_USDT and BTC_USDT
- CSV schema verified: open_time,open,high,low,close,volume,amount,close_time

Permitted correction:
- use only official MEXC MX_USDT and BTC_USDT daily Min15 CSV files;
- recover the exact same 14 pre-frozen event timestamps;
- require exact open_time matches at T0, +1h, +6h and +24h;
- preserve the exact metrics, seed and PILOT_SIGNAL_PRESENT gates.

Forbidden:
- no event addition/deletion;
- no T0 change;
- no horizon change;
- no direction change;
- no alternate venue;
- no interpolation/nearest candle;
- no threshold or gate change.

This remediation changes transport only.
