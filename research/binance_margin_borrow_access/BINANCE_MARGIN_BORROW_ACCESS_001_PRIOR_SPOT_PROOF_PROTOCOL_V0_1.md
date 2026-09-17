# BINANCE-MARGIN-BORROW-ACCESS-001 — PRIOR SPOT PROOF PROTOCOL V0.1

Date: 2026-09-17  
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**  
Preconditions: `SOURCE_CENSUS_PASS`, `EVENT_SOURCE_SCHEMA_PASS`, `EVENT_PARSE_PASS` V0.1.1.

## Purpose

For every retained asset-event candidate, prove that the asset was already trading on Binance Spot strictly before the information time of the Cross Margin borrow-access announcement.

This gate does not measure price behavior. It exists only to distinguish a relaxation of borrowing/short-access constraints from an inseparable initial Spot listing/access shock.

## Candidate unit

The scientific candidate unit is **asset × borrow-access article**.

A multi-asset article is split into one candidate row per exact Cross Margin borrowable asset. Failure to prove prior Spot for one asset does not silently invalidate a different asset in the same article; each row is adjudicated independently.

## Same-announcement ACCESS_CONFOUND

Any parsed ADD article whose canonical scientific content explicitly contains initial Binance Spot listing/trading-start semantics is `ACCESS_CONFOUND` before external proof and all of its asset-event rows are excluded from the clean mechanism universe.

The V0.1.1 parser identifies four such source-confounded ADD articles: the bundled access announcements for `VELODROME`, `VANA`, `USUAL`, and `1000CAT`.

No market outcome is involved in this exclusion.

## Primary prior-Spot authority — Binance Public Data archive metadata

Binance's official `binance/binance-public-data` documentation defines `data.binance.vision` as the Binance public data archive and defines deterministic daily Spot kline file paths by symbol/date, with a `.CHECKSUM` companion for every archive file.

V0.1 uses **archive object/checksum existence only**. It must not download, unzip, parse or inspect kline/OHLCV/trade values.

For an asset-event with official article publication time `T`:

1. compute `D = UTC calendar date(T) - 1 day`;
2. test a prospectively frozen ordered set of quote assets;
3. for each pair `<ASSET><QUOTE>`, request only the exact official checksum path:
   `https://data.binance.vision/data/spot/daily/klines/<PAIR>/1d/<PAIR>-1d-YYYY-MM-DD.zip.CHECKSUM`;
4. HTTP 200 plus a syntactically valid checksum line for the exact expected ZIP filename is canonical proof that Binance archived Spot kline data for a full calendar day strictly before the borrow-access announcement;
5. stop at the first valid proof in the frozen quote order for that asset-event.

No ZIP content is requested.

## Frozen quote order

The ordered proof universe is frozen before execution as:

`USDT, BTC, BNB, BUSD, FDUSD, USDC, TUSD, ETH, EUR, TRY, BRL, GBP, AUD, BIDR, DAI, PAX, USDP, IDRT, NGN, RUB, UAH, BKRW, BVND, ZAR`

Quotes are source-search routes only. Selecting the first available route does not select on market outcome.

An asset equal to the quote symbol is skipped for that quote. Duplicate pair strings are forbidden.

## Primary proof PASS

For an asset-event, `PRIOR_SPOT_ARCHIVE_PASS` requires:

- exact checksum URL date `D < UTC date(T)`;
- HTTP 200;
- checksum payload contains one SHA256-like digest and the exact expected ZIP filename;
- no archive data body/price value opened;
- no 2025/2026 path requested.

Record pair, date, URL path (not dynamic redirect), checksum digest string, response SHA256 and HTTP status.

## Unresolved primary cases

If no frozen quote route has a valid checksum for `D`, classify the asset-event `PRIOR_SPOT_PRIMARY_UNRESOLVED`. Do not infer that the asset was not Spot-listed.

Those rows may enter a separately frozen fallback provenance step using an earlier official Binance Spot listing/trading announcement or another independently canonical Binance historical representation. Current exchange metadata is not admissible historical proof.

## Event-level outputs

Each asset-event receives exactly one source status:

- `ACCESS_CONFOUND`;
- `PRIOR_SPOT_ARCHIVE_PASS`;
- `PRIOR_SPOT_PRIMARY_UNRESOLVED`;
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`.

The gate cannot issue `NO_EDGE`.

## Aggregate gate

The primary archive probe emits:

- total parsed ADD articles;
- total asset-event rows;
- same-announcement ACCESS_CONFOUND rows;
- prior-Spot archive passes;
- unresolved rows;
- technical failures;
- years represented after proof;
- safety receipt.

A nonzero unresolved count does not authorize Discovery; unresolved rows must be resolved or excluded under the Event Source Adjudication Authority before final adjudication.

## Safety

Forbidden: kline/trade/aggTrade ZIP download or inspection; prices; OHLCV; returns; basis; abnormal returns; borrow rates; borrow inventory; authenticated account/API calls; PnL; win rate; PF; drawdown; 2025/2026 scientific data; orders; wallets; alerts/webhooks; exchange mutation; live trading.