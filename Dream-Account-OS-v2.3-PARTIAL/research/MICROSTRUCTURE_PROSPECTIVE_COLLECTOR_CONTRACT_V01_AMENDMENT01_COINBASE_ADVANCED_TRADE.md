# Microstructure Prospective Collector Contract V0.1 — Amendment 01

Status: **FROZEN PRE-COLLECTION PROVENANCE CORRECTION**
Date: 2026-09-12
Branch: `dream-account-phase-b-signal-research-v0.1`

## Reason for amendment

Before any real network capture, a current-documentation review found an authentication ambiguity in the legacy Coinbase Exchange WebSocket documentation: the channel documentation and overview describe public/unauthenticated Level2 behavior, while the authentication documentation lists Level2 among channels requiring authentication.

Because this laboratory requires an unambiguous public read-only source and no credentials, the secondary venue is corrected prospectively **before any real Coinbase market-data capture**.

No target outcomes have been accessed to make this correction. No trading hypothesis, direction, threshold, window, symbol subset, or performance criterion is changed.

## Superseded secondary venue section

The V0.1 reference to **Coinbase Exchange Spot** is superseded for prospective collection.

Legacy Coinbase Exchange parsers already present in the repository are retained only as offline fixtures and MUST NOT authorize network capture.

## Frozen replacement secondary venue

### Coinbase Advanced Trade — public Market Data WebSocket

- canonical venue ID: `COINBASE_ADVANCED_SPOT`
- endpoint family: public Advanced Trade Market Data WebSocket only
- production host: `advanced-trade-ws.coinbase.com`
- products: `BTC-USD`, `ETH-USD`
- channels:
  - `level2`
  - `market_trades`
  - `heartbeats`
- authentication: **not required under the frozen public-channel contract**
- user-order endpoint `advanced-trade-ws-user.coinbase.com`: **FORBIDDEN**
- JWT/API-key fields: **FORBIDDEN**
- `user` and `futures_balance_summary` channels: **FORBIDDEN**

## Advanced Trade message semantics

The collector must preserve the complete source envelope before normalization, including when present:
- top-level `channel`;
- top-level `client_id`;
- top-level `timestamp`;
- top-level `sequence_num`;
- complete `events` array;
- per-event `type`;
- `product_id`;
- all level/trade fields exactly as sent.

The normalized parser must not assume the legacy Coinbase Exchange `type/product_id/changes` top-level schema for Advanced Trade.

### Level2

- process only messages whose top-level channel identifies Level2;
- initialize/reinitialize local state only from a source event explicitly marked as a snapshot under the Advanced Trade schema;
- apply update events only after a valid snapshot;
- size zero deletes a level; nonzero size replaces the absolute size at that price, subject to current source documentation;
- any missing/ambiguous sequence continuity or unrecognized schema version fails closed for L2-derived metrics.

### Market trades

- market-trade messages are captured as public trade data only;
- no aggressor-direction trading rule is authorized;
- no future-return label is computed under this contract.

### Heartbeats

- heartbeats are captured as connection/continuity evidence;
- heartbeat counters and top-level sequence numbers are audit fields, not BBO observations;
- heartbeat records MUST use a dedicated normalized stream type and MUST NOT be mislabeled as `BBO`.

## Normalized stream-type correction

The provenance core stream vocabulary is prospectively extended with:
- `HEARTBEAT`

This semantic correction must be implemented before real capture.

## Security rule

Only the public market-data host named above may be opened for the Coinbase side of the shakedown. No generic arbitrary-host WebSocket client is authorized.

## Governance

`H02_STATUS = NOT_AUTHORIZED`

`TARGET_OUTCOMES_ACCESSED_FOR_THIS_AMENDMENT = FALSE`

`LIVE_TRADING_AUTHORIZED = FALSE`

`EXCHANGE_MUTATION_AUTHORIZED = FALSE`

`COINBASE_CREDENTIALS_AUTHORIZED = FALSE`

Stop condition remains:
`STOP_AFTER_READ_ONLY_COLLECTOR_IMPLEMENTATION_GATE_BEFORE_PROVENANCE_SHAKEDOWN_CAPTURE`
