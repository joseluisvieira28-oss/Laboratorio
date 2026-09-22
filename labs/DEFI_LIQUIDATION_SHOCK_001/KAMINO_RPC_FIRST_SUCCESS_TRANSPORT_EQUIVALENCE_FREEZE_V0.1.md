# DEFI-LIQUIDATION-SHOCK-001 — KAMINO RPC FIRST-SUCCESS TRANSPORT EQUIVALENCE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED
Scope: Kamino Lend first-success boundary only

## Reason

The frozen BigQuery boundary method remains scientifically valid, but no BigQuery execution credential/connector is available in the current runtime. The corrected Kamino decoder path has already passed 16/16 RAW verification on the official Solana public RPC.

This document prospectively freezes a transport-equivalent source route before any chronological first-success crawl result is opened.

## Scientific contract — unchanged

Program:
`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

Instruction:
`liquidate_obligation_and_redeem_reserve_collateral`

Correct discriminator:
`b1479abce2854a37`

Source-supported lower boundary:
`2023-11-17T13:25:35Z`

Known RAW-verified upper anchor:
- signature: `37bfneBLcVoWnqWEoP7Y4EnJREUeaHeEYgnQ9kjBGpsN3tMjP2AceURMpbgQDeR8hmxZ4L5JVSokepJ7WhsuTDnK`
- slot: `307588986`
- time: `2024-12-15T07:32:56Z`

The task remains: identify the earliest successful realized transaction at or after the source-supported lower boundary whose Kamino instruction bytes begin with the frozen discriminator.

## Frozen transport route

Endpoint:
`https://api.mainnet-beta.solana.com`

Phase A — complete address-history walk:
1. call `getSignaturesForAddress` for the frozen Kamino program;
2. start strictly older than the frozen upper-anchor signature using `before`;
3. page at limit 1000, newest-to-oldest;
4. continue without skipping/reordering until a returned transaction has `blockTime < 2023-11-17T13:25:35Z`;
5. duplicate signatures, non-monotonic time, irrecoverable null block time, RPC truncation, rate-limit exhaustion, or history exhaustion before crossing the lower boundary are fail-closed transport blockers.

Phase B — oldest-to-newest RAW scan:
1. retain only rows at or after the lower boundary and include the frozen upper anchor;
2. sort deterministically by `(blockTime, slot, signature)`;
3. failed signatures (`err != null`) cannot be realized first-success events;
4. for every successful signature in ascending order, fetch `getTransaction` with `jsonParsed`;
5. require non-null transaction, exact signature context, `meta.err == null`, exact Kamino program ID, and instruction data base58-decoding to bytes beginning with `b1479abce2854a37`;
6. stop at the first RAW-verified match. Its exact chain timestamp/slot/signature becomes the provisional first-success boundary.

No successful row may be skipped because retrieval is inconvenient. Any missing RAW transaction before the first match blocks adjudication.

## Equivalence rationale

The BigQuery method and this RPC method query the same Solana chain history for the same fixed program and decoder. The replacement changes transport and enumeration only, not:
- protocol;
- program ID;
- instruction class;
- discriminator;
- lower/upper temporal authority;
- success predicate;
- chronology;
- RAW requirement;
- economic hypothesis.

A Kamino program invocation must reference the program account in the transaction account-key set; `getSignaturesForAddress` enumerates confirmed transactions containing that address. RAW `getTransaction` then adjudicates the exact instruction bytes.

## Terminal routing

- lower boundary crossed + earliest match RAW verified:
  `KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_PASS`
- public RPC cannot supply complete history to the lower boundary:
  `KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`
- any content/chronology inconsistency:
  `KAMINO_FIRST_SUCCESS_BOUNDARY_SOURCE_ANOMALY_FAIL_CLOSED`

A PASS closes Kamino historical applicability only. It does not grant global `SOURCE_DATA_PASS`, sample sufficiency, discovery authority or economic edge.

## Firewall

- market prices: false
- returns: false
- PnL: false
- direction: false
- 2025/2026 market outcomes: false
- protocol selection from outcomes: false
- threshold tuning: false
- live trading: false
- orders: false
- wallets: false
- exchange mutation: false
- paid source: false
- merge main: false
