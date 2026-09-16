# BOER-V2-PATH2-2024-001 — Protected 2024 Replication Freeze

Status: FROZEN / 2024 MARKET OUTCOMES UNOPENED.

This is a prospective independent replication of `BOER-BINANCE-PERP-4H2H-001` for V2 Support Path 2. It preserves the exact parent signal, venue, calendar event, entry/exit timing, holding period and 15/25 bps cost assumptions.

The protected 2024 outcome block MUST NOT be opened merely because this file exists. Separate explicit authorization is required before an execution runner may read 2024 price fields.

All required pass gates are frozen in `V2_PATH2_REPLICATION_2024_FREEZE_V01.json`:
1. >=11 resolved trades out of 12 scheduled events.
2. Base mean net return > 0.
3. Base profit factor >= 1.00.
4. Stress mean net return > 0.
5. >=7 base-cost winning trades.
6. Minimum leave-one-trade-out base mean > 0.

If any evaluable economic gate fails, no parameter, cost, timing, horizon, event, subgroup or venue rescue is allowed. 2025/2026 remain locked. No live trading, exchange mutation, merge to main or Render deployment is authorized.
