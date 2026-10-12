# BTC-CONVEX-TREND-CAPTURE-001 — H2 RISING-REGIME CLOSEOUT V0.1

Date: 2026-09-24

Status: H2_FAIL

Source gate:
- run 35956275475
- artifact 10790398184
- SHA-256 dcf38c229bb340c01c44b141756872463a2f9f0e017a3eac47baaede9fa85f46
- 5/5 assets source-valid

Economic validation:
- run 35956632021
- artifact 10791006099
- SHA-256 daac760f9fec435afe46f085d2c37831a4a19b7c5c62aa615b4b280f6d750838

Third untouched basket: LTCUSDT, BCHUSDT, TRXUSDT, DOTUSDT, UNIUSDT.
Window: 2021-01-01 through 2025-12-31.
Timeframe: 1h.

H2 change only:
close > SMA200 AND SMA200 > SMA200[200]

H2 BASE:
- LTC: -42.68%, PF 0.869
- BCH: -7.42%, PF 0.985
- TRX: +397.69%, PF 1.677
- DOT: -57.79%, PF 0.744
- UNI: -52.50%, PF 0.743

H2 family BASE:
- positive assets: 1/5
- PF > 1: 1/5
- positive after largest-winner removal: 1/5
- equal-weight mean return: +47.46%
- median return: -42.68%
- median MTM drawdown: -72.17%

Parent benchmark on the same untouched basket:
- positive assets: 2/5
- PF > 1: 2/5
- equal-weight mean return: +49.78%
- median return: -64.97%

Frozen H2 gate:
- >=3/5 positive BASE: FAIL
- >=3/5 PF > 1: FAIL
- STRESS family mean > 0: PASS
- >=2/5 positive after top-winner removal: FAIL
- >=4/5 source-valid: PASS
- H2 family mean > Parent family mean: FAIL

Final adjudication: H2_FAIL.

Interpretation:
The rising-SMA200 condition reduced trade count and improved drawdown/return severity on several losing assets, but it did not create broad positive expectancy. TRX is an isolated survivor under both Parent and H2 and must not be cherry-picked into the canonical research family.

Historical filter mining for this family stops here. Further evidence should be prospective and use the unchanged Parent rule.
