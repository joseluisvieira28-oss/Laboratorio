# DEFI-LIQUIDATION-SHOCK-001 — SQD FIRST-DAY CENSUS TRANSPORT CORRECTION V0.4.2

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / TECHNICAL CORRECTION ONLY / SOURCE-ONLY / OUTCOME-BLIND

The V0.4.1 timestamp probe learned two transport facts before any full-range census was opened:

1. the SQD timestamp endpoint returns JSON key `block_number`, not one of the originally assumed keys;
2. at the exact known first-success timestamps it resolves to a slot immediately before the known event slot (Kamino -1 slot; Save11 -2 slots), so it is a safe lower seed but is NOT itself the exact first slot at/after the timestamp;
3. the endpoint can return HTTP 529 overload and therefore requires bounded retry.

No population, instruction identity, authoritative boundary, success semantic, chunk size, dedup rule or RAW-sample rule changes.

## Corrected daily-boundary transport

For UTC day `[T0,T1)`:
- resolve `T0` and `T1` through the SQD timestamp endpoint;
- accept only integer `block_number`;
- use returned blocks as lower seeds;
- query a small conservative slot envelope from `seed(T0)` through `seed(T1)+16`;
- locally retain only block headers with timestamp `T0 <= timestamp < T1`;
- for the authoritative first day additionally require `timestamp >= authoritative first-success timestamp` and slot >= authoritative first-success slot;
- continuation of finalized-stream must prove the complete envelope was consumed;
- every returned instruction is locally decoded and classified exactly as V0.4/V0.4.1.

The +16-slot envelope is a transport safety margin fixed before census results and is removed by local timestamp filtering. It does not enlarge the scientific population.

## First-day calibration

Before full-range execution, run exactly the two first authoritative partial UTC days:
- Kamino: [2023-11-17T14:48:24Z, 2023-11-18T00:00:00Z)
- Save11: [2024-07-19T19:30:52Z, 2024-07-20T00:00:00Z)

Both must recover their already-known first-success signatures and produce zero source anomalies before full-range census launch.

No prices, balances, token balances, amounts, returns, PnL, direction, economic outcomes, trading, orders, wallets, exchange mutation, paid source, account creation or merge main.
