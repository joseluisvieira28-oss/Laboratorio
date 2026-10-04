# SP500 PUBLIC BBO OFF-HOURS CLOSEOUT V0.3

Date: 2026-10-04
Run: 37194285361
Artifact ZIP SHA256: `18cf9ce59f0ccda857b5b3f67a56cca91008cb2af1f3900488b3c0b6fe76c494`

## Context

This is a Sunday / off-hours diagnostic only.

Scientific reference:
- replicated SP500 basis signal mean gross in untouched September holdout:
  +0.5177567737 bps per accepted signal.

No scientific signal rule was changed.

## Public BBO sample

MEXC `SPX500_USDT` public order-book depth:
- requested snapshots: 60
- valid snapshots: 60
- invalid: 0
- interval: 1 second

Spread distribution:
- min: 2.4573043371 bps
- p10: 2.4573043371 bps
- p25: 2.4573043371 bps
- p50: 2.4573043371 bps
- mean: 2.6772015292 bps
- p75: 2.9747085109 bps
- p90: 2.9876440335 bps
- max: 3.1040637368 bps

Fraction of snapshots with spread below the September gross-edge reference:
- 0.0%

Median top-of-book sizes:
- best bid size: 80,064 contracts
- best ask size: 1,190 contracts

## Verdict

`OFF_HOURS_SPREAD_HOSTILE`

The Sunday quoted spread alone was approximately 4.75x the replicated September mean gross edge at the median.

This does NOT invalidate the weekday scientific signal and must NOT be used as a weekday execution verdict.

## API fee context

The latest official MEXC API Futures fee update found in the current audit is effective 2026-06-01:
- maker: 0.06% = 6 bps per side
- taker: 0.08% = 8 bps per side

Thus the standard API fee-only round-trip is approximately:
- maker/maker: 12 bps
- maker/taker: 14 bps
- taker/taker: 16 bps

Those API costs alone exceed the replicated signal gross edge by a wide margin.

## Classification

Scientific signal:
`REPLICATED_SIGNAL_SURVIVOR`

Sunday public execution conditions:
`OFF_HOURS_SPREAD_HOSTILE`

Standard MEXC API route:
`EXECUTION_FEE_BLOCKED_STANDARD_API`

Weekday/web-app/account-specific execution:
`UNPROVEN`

No account reads, private endpoints, orders, exchange mutation or live trading were used.
