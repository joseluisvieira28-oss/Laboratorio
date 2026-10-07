# FUNDING-SQUEEZE-001
## V0.1 DEVELOPMENT CLOSEOUT
Date: 2026-10-07
Status: CLOSED — NO_VIABLE_CONFIRMATORY_SPEC AT 30 BPS BINANCE HURDLE

### Authority chain
Development grid freeze:
- FUNDING_SQUEEZE_V01_DEVELOPMENT_GRID_FREEZE_2026-10-07.md
- freeze commit: 18201c7ddcc75145750d9de9e7287bc0cefb8e9d

Timestamp technical-fix freeze:
- FUNDING_SQUEEZE_V011_TIMESTAMP_ALIGNMENT_TECHNICAL_FIX_FREEZE_2026-10-07.md
- freeze commit: dab1ddf9043ec2fa9f701e482aaa4809a5571493
- fixed runner commit: 2c60002c4996210cd00cedb3b1129277c9d2148d

Authoritative successful run:
- GitHub Actions run: 37679167450
- artifact: funding-squeeze-v01-development-receipt
- artifact ID: 11509121169
- artifact digest: sha256:87408a2a7a29dabd8b6cd3b63e93fc2df4470d75787156c1b0cb291787ee2831

### Protected data
2025 opened: NO
2026 opened: NO

### Result
All 30 frozen grid cells failed the 30 bps Development promotion gate.

Verdict:
NO_VIABLE_CONFIRMATORY_SPEC

Therefore Binance 2025 remains unopened and there is no legitimate 30-bps Binance confirmatory candidate.

### Economically important diagnostic
The strongest low-cost clue was the q0.90 / 168h / FIXED cell:
- N = 86
- mean gross = +0.25742209744565384% per trade
- mean net @30 bps = -0.042577902554346165%
- mean net @10 bps diagnostic = +0.15742209744565386%
- 95% bootstrap CI of net@30 = [-0.13668283027492936%, +0.07282006387306783%]
- mean funding component = +0.25483576068907%
- mean basis component = +0.002586336756583909%
- positive net@30 years = 2/4.

Because subtracting a constant execution hurdle translates the bootstrap distribution by the same constant, the corresponding descriptive net@10 interval would be approximately [+0.0633%, +0.2728%]. This is diagnostic only and CANNOT rescue the Binance 30-bps version.

### Interpretation
The mechanism can accumulate enough gross carry over seven days to become economically interesting when all-in execution cost is materially below Binance retail spot+perp standard-cost assumptions.

That observation authorizes only a NEW, separately frozen low-cost venue/execution replication. It does not change the verdict of this Development run.

### Governance
- main unchanged;
- no live trading/orders/wallets/account reads/private endpoints;
- no exchange mutation/spending;
- no 2025/2026 Binance outcomes;
- no retroactive lowering of the 30 bps hurdle.
