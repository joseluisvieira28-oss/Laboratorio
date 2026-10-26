# Fusion Shadow V0.7 — PRE-OUTCOME OPERATIONAL FREEZE — 2026-10-26

**STATUS: SOFTWARE_ONLY_21_TESTS_PASS / PROSPECTIVE_OBSERVATION_NOT_STARTED / NO_TRADING_PROMOTION**

## Intent and identity
- Owner: human operator. Research-only observer, no automatic financial decisions or orders. This is NOT a new test of original CED1D's full entry and exit, and NOT a validated edge.
- Window fixed in advance: 2026-10-27 to 2026-11-09 inclusive. Exactly two UTC windows per date: entry snapshot 01:00:00..01:03:59, exit snapshot 02:00:00..02:03:59. No user-controlled replay, retry after window, or fill-in of missing days. Future read access restricted to live public market data during these windows.
- Inputs: BTCUSDT Binance spot, AVAXUSDT Binance USD-M futures; compare closed 1D close D-1 vs D-21 (21 consecutive fully closed UTC bars). Equal UP => LONG_CONTEXT; equal DOWN => SHORT_CONTEXT; else NO_CONFLUENCE. No parameter, asset, fee or signal adaptation after outcome.
- Observation market: MEXC AVAX_USDT perpetual top-20 public bids/asks and contract metadata, contractSize 0.1 AVAX. Book publication timestamp freshness [-3s future, +30s stale] and local observed time. Do not interpret current 2026 MEXC price as historical 2022-23 fill.
- Read-only public GET endpoints only for exchange queries, optionally Telegram Bot sendMessage POST with user-configured private credentials. Telegram not installed or tested on operator's account. No keys, logins, wallet reads, exchange order endpoints, Render deploy, Telegram shared bot mutation, merge to main or research holdout opening.

## Safety controls
- No command-line options for symbol, lookback, window length, leverage, trade execution, position size or stop.
- Disabled by default: running Python without --cycle prints NOT_RUNNING. --cycle outside UTC gate fails closed. --notify-telegram explicit, absent secrets => NOT_CONFIGURED. No secrets in source, receipt or task arguments.
- Single receipt per [UTC date, phase] reserves file atomically; no blind retry if process crashes or Telegram delivery is unclear. Network/source failure yields SOURCE_BLOCKED, never a normal signal.
- No market PnL calculation or economic decision from the forward period. Legacy 2026 holdout datasets stay sealed. These public current observations are separately registered operational records, NOT untouched 2026 OOS economic evidence.

## Frozen release files and local test evidence
- Local, Python 3.10+ stdlib implementation: fusion_shadow_observer_v07.py, 21 unit tests, operator-controlled installer/remover PS1, README in the PR folder and also a reproducible ZIP delivered to operator.
- Container unit tests: 21/21 pass using mocks; no live Binance, MEXC or Telegram requests exercised.
- Local prepackaged ZIP: CryptoLab_Fusion_Shadow_V07_Windows.zip, SHA256 b40e2d4b3922619fa7755574a005ee860b919ebfefe944703ca23ce2072d2e51; internal ZIP member integrity checked PASS. This ZIP was prepared before GitHub source was uploaded; GitHub files may have different harmless trailing-newline formatting, so do not assume its bundle digest applies to a GitHub archive.
- Local source Python SHA256 94ee8398a19f129b1d6bfa691b4f4b87d76c705e754a442dd1372fc64f308047. Changes to code after this freeze invalidate the prospective identity and require a new documented preregistration before observation.
- Native Windows Task Scheduler scripts are untested in the assistant's Linux execution environment; operator must install and verify schedule if desired.

## Gate: what 14 days can and cannot prove
- CAN assess whether two public feeds and contract metadata arrive on time; proportions of OBSERVED/SOURCE_BLOCKED; static bid/ask spreads and available displayed levels at scheduled clock times; whether alert transport, no duplicates and safe no-signal behaviors work.
- CANNOT certify expected return, account-level 0% fees, MEXC actual entry/exit fills, adverse selection, trade size, capital risk, stop execution, or standalone profit. 14 days is not statistical power for a high-variance trading strategy.
- Parent historical gate remains: 2022/23 proxy BASE14 +1051.38 summed bps, STRESS20 -2356.62; tails and 2023 fragility matter. Zero-fee interface screenshot is time-local and cannot be promoted into permanent costs.
- PASS operationally only if all intended 28 UTC windows have nonmissing valid receipts, source freshness and stable metadata, independent alert delivery confirmation, no duplicate, and all venue identity constraints. Any incomplete window => INCOMPLETE, not retrofit/backfill.

## Verified documentation
- Binance Spot API: https://binance-docs.github.io/apidocs/spot/en/
- Binance USD-M klines: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- MEXC public contract: https://mexcdevelop.github.io/apidocs/contract_v1_en/
- Telegram Bot API sendMessage: https://core.telegram.org/bots/api