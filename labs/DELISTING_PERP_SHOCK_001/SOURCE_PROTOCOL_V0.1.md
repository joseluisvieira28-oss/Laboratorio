# DELISTING-PERP-SHOCK-001 — SOURCE CONTRACT V0.1

Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND
Branch: delisting-perp-shock-v0.1

## Purpose
Build a defensible event population for testing whether official Binance full-token delisting announcements create an executable negative shock in the token's USD-M perpetual.

This is a NEW identity. It does not modify or rescue EXCHANGE-DELISTING-SHOCK-001.

## Event authority
Primary source: official Binance Support announcement API already used by the parent source work.

Eligible article:
- publication UTC in 2023 or 2024;
- official title begins "Binance Will Delist";
- article body provides an exact all-pairs cessation timestamp.

Token identity is defined ONLY by ticker symbols explicitly named in the official article title before the terminal " on YYYY-MM-DD" phrase.
Title separators comma, "and", and "&" are normalized.
Generic quote assets are not inferred from trading-pair orientation.
No symbol may be introduced from a pair list if it is absent from the title.

First qualifying public announcement per ticker only.

## Executable route gate
For each title-authoritative ticker:
1. Binance Vision Spot SYMBOLUSDT archive must exist strictly before publication;
2. Binance Vision USD-M Futures SYMBOLUSDT archive must exist on the publication UTC date;
3. USD-M Futures archive must also exist on publication+1 UTC day, unless scheduled cessation is earlier;
4. all checks are metadata/checksum route only — no OHLC values under this source gate.

A route-qualified event therefore has a pre-existing Spot market and an observable USD-M perpetual after the public announcement.

## Minimum source gate
SOURCE_DATA_PASS requires:
- >=20 route-qualified ticker events;
- >=12 distinct tickers;
- at least 5 route-qualified events from 2023;
- at least 5 route-qualified events from 2024;
- exact publication timestamp for every event;
- exact all-pairs cessation timestamp for every event;
- zero third-party identity substitution.

Otherwise preserve INSUFFICIENT_SOURCE_SAMPLE / SOURCE_ACCESS_BLOCKED / SOURCE_TECHNICAL_FAILURE.

## Protected outcomes
No OHLC values, returns, direction performance, PnL, funding, borrow state, 2025 data or 2026 data may be opened by this gate.

SOURCE_DATA_PASS does NOT authorize Discovery. A separate FINAL_PRE_DISCOVERY_PROTOCOL must be frozen first.

## Safety
No live trading, orders, wallets, authenticated exchange endpoints, exchange mutation, paid data, main merge, post-outcome tuning or cherry-picking.
Trading authority: NONE.
