# ETH-STAKING-FLOW-001 / ESF-NETQUEUE-XATU-7D-003 — FULL SOURCE COVERAGE CENSUS V0.3B

Date: 2026-09-18
Status: **FROZEN BEFORE FULL COVERAGE EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

## Preconditions

- V0.3 authority frozen at commit `056118e17d802cd0a3e362d228dd2593ebf4bbaf`.
- V0.3A metadata feasibility: `SOURCE_FEASIBILITY_PASS`.
- V0.3A run: `35380446290`.
- V0.3A artifact ID: `10561848802`.
- V0.3A artifact digest: `sha256:40159b200b6e26218bc4767ff795a46fa44bc784d997e2e9fad4c8fe1cc0b4ac`.
- Four deterministic probes all had required schema and earliest epoch at 00:03:35 UTC.

## Purpose

Prove exact public-object coverage for every frozen date before reading queue/status values.

## Frozen date set

Every UTC date from **2023-04-12 through 2024-12-31 inclusive**, exactly **630 dates**.

For each date only:
`https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators/YYYY/M/D/0.parquet`

No alternate hour, date, table, network or mirror.

## Allowed request

One bounded HTTP GET per exact object with:
`Range: bytes=0-3`.

Record only:
- date;
- URL;
- HTTP status;
- response metadata headers;
- first four bytes;
- whether prefix is `PAR1`.

No Parquet row values may be opened.

## Deterministic sharding

Shard by calendar month:
- 2023-04 partial from day 12;
- each full month thereafter;
- through 2024-12.

Exactly 21 disjoint month shards.
No gap, overlap or date substitution.

## PASS

`XATU_FULL_COVERAGE_PASS` requires:
- exactly 630 unique expected dates;
- 630/630 HTTP 200 or 206;
- 630/630 returned prefixes `PAR1`;
- zero duplicate dates;
- zero dates outside the frozen window;
- no 2025/2026 request.

Any missing object = `DATA_FAILURE`.
Transport exceptions without a definitive object result = `SOURCE_ACQUISITION_TECHNICAL_FAILURE`.
Unexpected body signature = `PROVENANCE_FAILURE`.

## Next phase

Only `XATU_FULL_COVERAGE_PASS` releases the V0.3C daily canonical-epoch queue-count reconstruction gate already contemplated by the V0.3 authority.

V0.3B itself does not read `status`, count validators, calculate net queue, or open market outcomes.

## Firewalls

- status values: forbidden
- queue counts: forbidden
- ETH/BTC prices: forbidden
- returns/PnL: forbidden
- 2025/2026: forbidden
- trading/orders/wallets/exchange mutation: forbidden
- merge main: forbidden
