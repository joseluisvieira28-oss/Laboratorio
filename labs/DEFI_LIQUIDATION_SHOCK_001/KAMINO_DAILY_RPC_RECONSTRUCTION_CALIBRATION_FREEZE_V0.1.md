# DEFI-LIQUIDATION-SHOCK-001 — KAMINO DAILY RPC RECONSTRUCTION CALIBRATION V0.1

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / SOURCE-TRANSPORT ONLY / OUTCOME-BLIND / FAIL-CLOSED

Purpose:
Calibrate a compact daily source reconstruction route against an already-completed authoritative daily queue before using it for the next day.

Program:
`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

Transport:
official public Solana RPC `getSignaturesForAddress` only.

No transaction body is read during reconstruction.

## Calibration control — 2023-11-18

Frozen daily manifest entry:
- window: `[2023-11-18T00:00:00Z, 2023-11-19T00:00:00Z)`
- expected rows: `550`
- expected canonical queue SHA256: `f94c0c6ae91bf74f9664d13a7e34a1e47c3285641dba95816be39062efe8c1ad`
- immediately newer anchor:
  - signature `5GjDCxV8pirvA3TFZcmCfBfjTy2zC37FLGUAqwwnyedkZq3p9b3mYHdH1EqztEHBraDagLZx1wJ4emQMTEGVFmnF`
  - slot `230852788`
  - blockTime `1700352087`
- immediately older anchor:
  - signature `4kAsx7MhnmgqVNTTHbaAgRDaTbQqSJEhzo85FJQfMoN6oFVHMta837xjeHEGuGqmXSa4qAdZamFzLPjvgCFQd15J`
  - slot `230647466`
  - blockTime `1700265530`

The RPC reconstruction must query the program with:
- `before=<newer anchor>`
- `until=<older anchor>`
- pagination only by the final signature returned from each page.

It must reproduce the exact canonical row set:
`signature, slot, blockTime, err`
sorted oldest -> newest by `(blockTime, slot, signature)`.

Calibration PASS requires exact row-count AND exact canonical SHA256 equality.

## Next target — 2023-11-19

Only if the 2023-11-18 calibration passes, reconstruct:
- window: `[2023-11-19T00:00:00Z, 2023-11-20T00:00:00Z)`
- expected rows: `716`
- expected SHA256: `e9691dbe503ce8bbc5a54c321fbf560c0aba444303d3304a0f6f7b7cc1256400`
- newer anchor signature:
  `34PcMiHAnS2ydNGRmUTV129ms9BhgG2AGUgBN11G3bT14z1PqVjfZGRyrCwPH8zNamcJ8z8vh72pwJwx3WTaHSx4`
- older anchor signature:
  `5xPgHD26z25Q1baPZDQb2NnAmfMauoAgNzR3R9D8gH7TCAXFaWbw9ecHjdymKr5JBouahMGGp48kCN8gukECCiE4`

The next-day queue is usable for RAW census only if its count and SHA match the pre-existing manifest exactly.

## Fail-closed rules

- null blockTime => fail closed;
- duplicate signature => fail closed;
- returned rows outside the frozen day after anchor reconstruction => fail closed;
- unexpected anchor inclusion => fail closed;
- count/hash mismatch => fail closed;
- RPC exhaustion => technical blocker only;
- no liquidation decoding in this step.

Classifications:
- `KAMINO_DAILY_RPC_RECONSTRUCTION_CALIBRATION_PASS`
- `KAMINO_DAILY_RPC_RECONSTRUCTION_CALIBRATION_FAIL_CLOSED`
- `KAMINO_DAILY_RPC_RECONSTRUCTION_RPC_BLOCKED`

Firewalls:
liquidation_classification=false; prices=false; amounts=false; returns=false; pnl=false; direction=false; market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
