# L2R-EXEC-PASSIVE-FEETIER-001 — FEE SOURCE FEASIBILITY PREFLIGHT V0.1

Date: 2026-09-26
Status: **SOURCE_FEASIBILITY_PASS / ACCOUNT_SPECIFIC_TRIGGER_NOT_YET_PROVEN**
Parent: `L2R-EXEC-PASSIVE-FEETIER-001`
Reopen trigger already frozen: effective maker fee <= **0.4 bps/fill** before any new forward outcome.

## Official Hyperliquid fee source

Source:
https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees

Current perp base schedule includes:
- Tier 0: maker 0.015% = 1.5 bps/fill
- Tier 1, >$5M 14d weighted volume: maker 0.012% = 1.2 bps/fill
- Tier 2, >$25M: maker 0.008% = 0.8 bps/fill
- Tier 3, >$100M: maker 0.004% = 0.4 bps/fill
- Tier 4, >$500M: maker 0.000% = 0.0 bps/fill
- Tier 5 and Tier 6: maker 0.000% = 0.0 bps/fill

The protocol also publishes staking discounts and maker-rebate tiers. Those must not be inferred manually for this lab. The account-specific final effective rate is authoritative.

## Authoritative account query

Official API source:
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint

Read-only request:
`POST https://api.hyperliquid.xyz/info`
with:
`{"type":"userFees","user":"0x..."}`

The authoritative field for this gate is:
`userAddRate`

Trigger:
`float(userAddRate) <= 0.00004`

because 0.00004 decimal = 0.004% = 0.4 bps/fill.

## Governance

- A published fee tier being theoretically reachable does NOT fire the trigger.
- The exact trading account must prove its current effective `userAddRate`.
- No address/account identifier is committed to the repository.
- No order, wallet action, deposit, transfer, staking, volume generation, exchange mutation or forward market outcome is authorized.
- Do not trade merely to manufacture fee-tier eligibility.
- If `userAddRate > 0.00004`: child remains DORMANT.
- If `userAddRate <= 0.00004`: source trigger fires; next step is a separately frozen queue/fill/adverse-selection preflight before any forward outcome.

No 2026 market outcome is opened by this preflight.
