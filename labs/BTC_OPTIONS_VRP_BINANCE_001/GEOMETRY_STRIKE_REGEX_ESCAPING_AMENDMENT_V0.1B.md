# BTC-OPTIONS-VRP-BINANCE-001 — GEOMETRY STRIKE REGEX ESCAPING AMENDMENT V0.1B

Date: 2026-09-19
Parent geometry run: `35463286323`

## Evidence

The corrected geometry run still produced zero structurally complete 08:00 rows on all 147 loaded days. Code inspection showed the new strike parser itself was committed with over-escaped raw regex tokens:

- `r"(\\d{6})..."`
- `r"...(\\d{6})..."`

In Python raw strings, those patterns match a literal backslash plus `d`, not a six-digit token. Therefore the strike normalization amendment never activated.

## Authorized correction

Change only the two raw-regex escapes from `\\d{6}` to `\d{6}` and from `\\.` to `\.`.

No source date, decision hour, DTE bin, 24h geometry, episode threshold, performance rule or economic hypothesis changes.

No option prices, returns, realized variance, VRP or PnL are opened by this correction. Both prior all-zero geometry runs remain preserved as technical parser failures and are non-adjudicative.
