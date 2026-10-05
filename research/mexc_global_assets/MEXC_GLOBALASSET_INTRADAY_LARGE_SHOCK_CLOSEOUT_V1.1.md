# MEXC GLOBAL-ASSET — INTRADAY LARGE-SHOCK CATCH-UP V1.1 — CLOSEOUT

Date: 2026-10-05
Outcome run: 37283224760
Outcome artifact ID: 11333670899
Outcome artifact ZIP SHA256: `46169656efd442af7df5e1c27e9be24de4789dbbf75a5f77792a24ffe2bbb930`

Frozen rule:
- 35 inherited source-bound global-asset contracts
- U.S. regular session scan 13:45–19:55 UTC
- 15m external shock
- Binance + Bitget same sign
- each leader >=50 bps absolute
- mean external move >=60 bps absolute
- MEXC same-window lag gap >=25 bps in external direction
- FOLLOW_EXTERNAL_CONSENSUS
- enter at signal close; exit +5m
- global cooldown 15m
- simultaneous triggers -> event basket
- daily equal-weight event basket = scientific unit

Results:
- raw trigger rows: 433
- admitted event baskets after global cooldown: 120
- triggered days: 17
- winning days: 14/17
- win-day rate: 82.3529%
- exact one-sided binomial p = 0.0063629150
- chronological half means: +14.5222 bps / +10.3980 bps
- mean daily gross: +12.3388 bps
- median daily gross: +15.2440 bps

Round-trip cost scenarios:
- 0 bps: mean +12.3388 / median +15.2440
- 12 bps: mean +0.3388 / median +3.2440
- 14 bps: mean -1.6612 / median +1.2440
- 16 bps: mean -3.6612 / median -0.7560
- 20 bps: mean -7.6612 / median -4.7560

Scientific gate:
PASS.

Operational gate:
FAIL at the frozen 16 bps API-fee requirement.

Verdict:
`SCIENTIFIC_PASS_FEE_BLOCKED`

Interpretation:
The large-shock construction materially amplified the previously observed MEXC follower effect and passed the frozen scientific test, but not enough to clear the standard API fee authority. It is therefore not a serious operational candidate and must not be called a cana.

No threshold reduction, no horizon change, no asset-specific rescue, no post-outcome tuning, no live trading, no orders, no private endpoints, no account reads, no wallets, no exchange mutation.
