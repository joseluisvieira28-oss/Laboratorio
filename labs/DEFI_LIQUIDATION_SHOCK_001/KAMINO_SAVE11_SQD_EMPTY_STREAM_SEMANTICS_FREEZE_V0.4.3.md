# KAMINO + SAVE11 SQD EVENT CENSUS — EMPTY STREAM SEMANTICS FREEZE V0.4.3

Lab: DEFI-LIQUIDATION-SHOCK-001

## Objective source correction

Official SQD Solana Portal documentation defines stream continuation as a loop over batches. After an HTTP-success response, the client parses NDJSON lines and terminates the range loop when the returned line set is empty.

Authority:
https://docs.sqd.dev/en/portal/solana/api

Documented continuation pattern:
- 204 => break
- non-OK => error
- parse NDJSON
- zero lines => break
- otherwise advance fromBlock to last returned block + 1 and continue

Therefore HTTP 200 + empty NDJSON is not classified as a transport exception in V0.4.3. It is treated as documented filtered-stream termination.

This supersedes Transport R1 retry treatment of literal `empty_200_response` before R1 is used as final census authority.

## Scientific invariants preserved

Unchanged:
- Kamino authoritative start 2023-11-17T14:48:24Z
- Save11 authoritative start 2024-07-19T19:30:52Z
- end exclusive 2025-01-01T00:00:00Z
- Kamino program and discriminator
- Save/Solend program and tag 0x11
- outer + inner/CPI handling
- exact local UTC timestamp membership
- timestamp resolver used only as slot seed
- frozen +16 slot transport envelope
- successful candidate semantics
- failed-attempt semantics
- anomaly fail-closed semantics
- instruction key protocol + signature + instructionAddress
- deterministic RAW sample rule
- Official Solana RPC as RAW reconciliation authority
- no economic outcomes

## V0.4.3 empty-stream rule

For each exact frozen slot envelope:
1. query SQD finalized-stream with the same frozen selectors;
2. if HTTP 200 returns one or more NDJSON blocks, process them and advance from last block + 1;
3. if HTTP 200 returns zero NDJSON lines, terminate that filtered stream as complete for the requested range;
4. zero-event day is valid only after this documented stream termination and exact local UTC filtering;
5. any malformed row, non-advancing response, missing parent transaction, decode/provenance inconsistency, or non-retryable source error remains fail-closed;
6. 429 / 529 / retryable 5xx remain transport-retry conditions and do not become zero-event proof.

## Required calibration before full census

V0.4.3 must recover:
- Kamino known first success on 2023-11-17;
- Save11 known first success on 2024-07-19;

and must close previously blocked empty-stream days without anomaly:
- Kamino 2023-11-23;
- Save11 2024-07-23.

Only after all four calibration jobs pass may the full-range V0.4.3 census launch.

## Firewall

Still false / closed:
prices, returns, PnL, direction, economic outcomes, protected 2025/2026 market outcomes, live trading, orders, wallets, exchange mutation, paid sources, account creation, merge main.

SOURCE/DATA/TRANSPORT blocker != NO_EDGE.
