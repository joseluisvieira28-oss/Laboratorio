# BTC-ALT-LL-004B — SOL EXECUTABLE BBO VALIDATION RESULT

Date: 2026-09-26
Workflow run: 36230583344
Status: NO_EXECUTABLE_CEILING_EDGE

## Frozen candidate
- leader: BTCUSDT Bybit L2
- follower: SOLUSDT Bybit L2
- BTC shock window: 5s
- absolute shock threshold: 7.002526745067178 bps
- direction: sign(BTC 5s return)
- horizon: 60s
- no flow gate
- no follower lag gate

## Fresh Discovery dates
2024-08-07:
- n 699
- maker gross +1.3774 bps
- Bybit VIP0 maker net -2.6226 bps
- taker net -11.0048 bps

2024-09-04:
- n 544
- maker gross +4.0435 bps
- Bybit maker net +0.0435 bps
- taker net -8.6010 bps

2024-10-02:
- n 39
- maker gross +1.0186 bps
- Bybit maker net -2.9814 bps
- taker net -11.3592 bps

Pooled:
- n 1,282
- positive date means: 1 / 3
- maker gross +2.4978 bps
- Bybit VIP0 maker net -1.5022 bps
- taker gross +1.0045 bps
- Bybit VIP0 taker net -9.9955 bps

## Decision
The post-hoc fee-overlay candidate did NOT survive fresh executable-BBO validation.

Do not build a fill model for this candidate.
Do not open 2025 OOS.
Do not open 2026 holdout.
