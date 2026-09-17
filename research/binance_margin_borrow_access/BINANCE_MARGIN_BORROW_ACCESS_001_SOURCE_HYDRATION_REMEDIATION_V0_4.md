# BINANCE-MARGIN-BORROW-ACCESS-001 — SOURCE HYDRATION REMEDIATION V0.4

Date: 2026-09-17  
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND / HYDRATION REMEDIATION ONLY**

## Trigger

V0.3 established a protected-period-safe deterministic index traversal using the official Binance English announcements channel:

- upper cursor `before=6899`;
- first page reaches `2024-12-31` UTC;
- traversal crossed below `2023-01-01`;
- no 2025/2026 message was retained or observed;
- 2,004 messages and 1,870 Binance Support links were encountered in-window;
- 232 structurally relevant/control article codes were identified;
- 199/232 official Binance Support article details were resolved before Binance returned HTTP 429.

The V0.3 terminal classification was therefore `SOURCE_ACQUISITION_TECHNICAL_FAILURE`. It was not an economic result. No market outcome was opened.

## V0.4 frozen architecture

V0.4 changes only the acquisition topology. The scientific hypothesis, event window, positive controls, source-pass criteria, canonical article authority and safety rules remain unchanged.

### Phase A — immutable index manifest

Re-run only the protected-safe Telegram index traversal from `before=6899` backward until timestamps cross below `2023-01-01T00:00:00Z`.

Fail closed if:
- any timestamp exceeds `2024-12-31T23:59:59Z`;
- first-page maximum timestamp is not on `2024-12-31` UTC;
- the lower boundary is not crossed;
- cursor ordering is non-descending.

Emit a sorted immutable manifest of all relevant/control 32-hex Binance Support article codes and their official-channel message metadata. The manifest is the sole input to detail hydration.

### Phase B — deterministic sharded official-detail hydration

The sorted manifest is split into exactly 8 deterministic shards by sorted-position modulo 8. Every code must occur in exactly one shard.

Each shard resolves official Binance Support article detail through the public Binance CMS detail endpoint only. Requests use conservative fixed pacing and bounded exponential backoff for HTTP 429/5xx responses. No event is removed because it is slow or rate-limited.

A shard emits either a complete detail record for every assigned code or a source-acquisition technical failure. Partial success cannot be silently promoted.

### Phase C — canonical aggregation

Aggregate all 8 shard receipts and require:
- manifest digest agreement;
- exactly-once coverage of every manifest code;
- zero missing/duplicate detail records;
- stable article-code identity agreement;
- non-empty official title and canonical article text;
- official release/publish timestamp provenance;
- both pre-frozen positive controls present and structurally valid;
- at least one explicit `Cross Margin` + `borrowable asset` event in each of 2023 and 2024;
- all safety/firewall fields false.

## Frozen official release-time extraction

The existing gate requiring an official article release date is **not weakened**.

For each official Binance article, release time may be recovered only from:

1. structured official payload fields with release/publish semantics: `releaseDate`, `releaseTime`, `publishTime`, `publishDate`, `publishedAt`, `publishedTime`; or
2. the official article text itself when it contains a literal publication marker matching `Published on YYYY-MM-DD HH:MM` (optional seconds / UTC suffix). Such publication text is parsed as UTC and retained with the matched literal for audit.

The Telegram message timestamp is an index/provenance cross-check only and is **not** an admissible substitute for missing official article release time.

If an article cannot provide an official release time through the frozen routes above, aggregation emits `PROVENANCE_FAILURE`.

## Positive controls unchanged

- 2023: `a74f935eaa2247889d58e33ec23313bb`
- 2024: `6674719e209641bda688729852d35fb5`

They remain source-completeness controls, never outcome selectors.

## Forbidden throughout V0.4

No prices, returns, basis, borrow rates, borrow inventory, authenticated exchange/API access, account data, PnL, win rate, PF, drawdown, 2025/2026 scientific data, orders, wallets, alerts/webhooks, exchange mutation or live trading.

## Terminal classifications

Only the already frozen source classifications are admissible:
- `SOURCE_CENSUS_PASS`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `SOURCE_ENUMERATION_INCOMPLETE`
- `PROVENANCE_FAILURE`
- `INSUFFICIENT_EVENT_SAMPLE`

`NO_EDGE` remains forbidden at this stage.
