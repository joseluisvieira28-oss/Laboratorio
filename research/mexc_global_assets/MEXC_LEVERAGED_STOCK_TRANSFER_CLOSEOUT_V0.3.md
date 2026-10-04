# MEXC LEVERAGED STOCK TRANSFER V0.3 — CLOSEOUT

Date: 2026-10-04
Branch: `mexc-leveraged-stock-transfer-v0.3-prereg-2026-10-04`
Run: `37235404640`

## Evidence

Source discovery run:
`37235145438`

Source artifact SHA256:
`eff1626678981ba884336bce10135bdc52542664e074cef6f87d3224db3e5a7e`

V0.3 outcome artifact SHA256:
`4c51928628904630b6defd1d6246f59f82f06f6fc62cd8286e0717610d36e43b`

Frozen rule:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon = 1 minute
- FOLLOW_EXTERNAL_CONSENSUS
- external = mean(Binance + Bitget 1m returns)
- 1-minute cooldown
- no per-asset parameter tuning

Holm-Bonferroni FWER 0.05 across the two frozen assets.

## MUU_USDT

- complete sessions: 17/17
- N=1117
- wins=639
- win rate=57.2068%
- mean gross=+5.245491 bps
- median=+3.588088 bps
- chronological thirds=+3.633751 / +5.433544 / +6.665360 bps
- exact binomial p=8.124928e-7
- scientific PASS=true
- net after 12 bps=-6.754509 bps
- net after 16 bps=-10.754509 bps

Verdict:
`SCIENTIFIC_SURVIVOR__STANDARD_MEXC_API_FEE_BLOCKED`

## MVLL_USDT

- complete sessions: 17/17
- N=1345
- wins=797
- win rate=59.2565%
- mean gross=+6.496329 bps
- median=+5.827506 bps
- chronological thirds=+5.505821 / +6.645103 / +7.336189 bps
- exact binomial p=5.958555e-12
- scientific PASS=true
- net after 12 bps=-5.503671 bps
- net after 16 bps=-9.503671 bps

Verdict:
`SCIENTIFIC_SURVIVOR__STANDARD_MEXC_API_FEE_BLOCKED`

## Overall verdict

`SCIENTIFIC_TRANSFER_SURVIVORS_FOUND__STANDARD_API_FEE_BLOCKED`

The NVIDIA/TESLA fixed 5/3/1m mechanism transfers again to two independent leveraged-stock instruments, but neither clears the frozen standard MEXC API fee floor.

No retrospective rescue, threshold change, post-outcome tuning, private endpoints, account reads, orders, wallets, exchange mutation or live trading were used.

Next legitimate attack is source-only alias resolution for the remaining MEXC global-asset contracts before any new outcomes are opened.
