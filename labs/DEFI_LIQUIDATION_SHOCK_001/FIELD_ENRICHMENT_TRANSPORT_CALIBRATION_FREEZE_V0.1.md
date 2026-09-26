# DEFI-LIQUIDATION-SHOCK-001 — FIELD ENRICHMENT TRANSPORT CALIBRATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Calibrate whether the same SQD Solana finalized-stream route used for the frozen event censuses can retrieve the additional source fields required for pre-Discovery enrichment without changing the event population.

The calibration requests only:
- instruction accounts;
- full instruction data;
- transaction account keys;
- existing identity/execution fields.

It MUST NOT request market prices, returns, PnL, USD notional or protected outcomes.

## Frozen calibration references

### Save0c
Program: So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo
Prefix: 0c
Slot: 110526981
Signature: 3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V
Instruction address: [3]

### Save11
Program: So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo
Prefix: 11
Slot: 278496102
Signature: WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L

### Marginfi
Program: MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA
Prefix: d6a997d5fba756db
Slot: 177590210
Signature: 2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK
Instruction address: [0]

### Kamino
Program: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
Prefix: b1479abce2854a37
Slot: 230572965
Signature: 2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv

### Drift liquidate_perp
Program: dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH
Prefix: 4b2377f7bf128b02
Slot: 159692675
Signature: 4r37rDVwUvdxJjJsx5fa5kXm8obE6TAn9czVMnMABDXa6L6QnQQnoRTmF9Kct5Cx5HUD8a3GB9P9cebSUQqDERad
Instruction address: [1]

### Drift liquidate_perp_pnl_for_deposit
Program: dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH
Prefix: ed4bc6ebe9ba4b23
Slot: 159694878
Signature: 3sRvzJkuuqMPhftGKSqiPJVJ72u6fyiyUYfWB4pqA3o6y9HcNvWsydVFe9iNtvZzkMXBoCDvgaontLzAnYArzxBi
Instruction address: [1]

### Drift liquidate_spot
Program: dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH
Prefix: 6b00802923e5fb12
Slot: 159863566
Signature: 6Nna7TV5aSH2uczPrT3mHGMjsVKtLf49TF6C823tLY9ZdSpbdQYbB4tMtNUXKEoQ3VEC4cbzRS49KMcZEakjYVm
Instruction address: [1]

### Drift liquidate_borrow_for_perp_pnl
Program: dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH
Prefix: a911205acf94d11b
Slot: 195239739
Signature: 5kYZPtPTFhvdBZfaFMPXtWh2A9tQYHt8bbzKJazopc7pWWmpwdcn1DeT4yLjxaidn387VMK6g6rYX4KMMh7NPka6
Instruction address: [1]

## Exact PASS rule

For all 8 frozen references:
1. query only the exact slot;
2. locate exact signature and protocol instruction;
3. decode the full Base58 instruction data locally;
4. require expected prefix;
5. require expected instruction address when frozen above;
6. require transaction err null and instruction committed;
7. require non-empty instruction `accounts`;
8. require non-empty full instruction `data`;
9. record transaction account-key count as transport evidence.

PASS:
`FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS`

Any identity mismatch, empty accounts/data or source anomaly:
`FIELD_ENRICHMENT_TRANSPORT_CALIBRATION_FAIL_CLOSED`

## Consequence of PASS

PASS authorizes only a source-only enrichment implementation keyed to the already frozen canonical event identities.

It does not authorize:
- changing the census population;
- event-size thresholds;
- prices or USD notional;
- returns/PnL;
- economic Discovery.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
balances=false
token_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
