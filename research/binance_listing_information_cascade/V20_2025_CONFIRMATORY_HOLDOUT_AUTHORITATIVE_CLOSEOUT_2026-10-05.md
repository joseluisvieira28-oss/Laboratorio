# V2.0 2025 CONFIRMATORY HOLDOUT — AUTHORITATIVE CLOSEOUT
Date: 2026-10-05
Status: CLOSED

## Lineage
Parent freeze:
7baa29f41260470ed78fb8d9e92bbcdabc8446b4

Activation receipt:
edad79d8c2d55041da1eeb766891d5f57b0a60a4

One-shot runner commit:
a6c1b06d3907bbad785977ab0ad45c5315521c36

GitHub Actions one-shot run:
37361885934

The one-shot run completed successfully with all 12 frozen observations valid.

No event, T0, venue binding, horizon, direction, threshold, transaction-cost stress, BTC-relative rule or gate was changed after outcome activation.

## Information layer
n = 12

Observed:
- median R1 = +13.6307%
- median R5 = +9.7221%
- median R15 = +10.4961%
- median R60 = +13.5636%
- R15 positive hit rate = 91.67%
- median 5m volume shock = 54.2219x
- leave-one-out median R15 positive = PASS
- positive R15 concentration = 43.8943%

Frozen information gate required concentration <=35%.

Therefore:
INFORMATION GATE = FAIL

The information shock remains large descriptively, but the frozen robustness gate is not satisfied because positive R15 contribution is too concentrated.

## PRIMARY delayed execution layer
Frozen entry:
first full minute boundary >=60s after T0.

Frozen primary horizon:
15 full minutes.

Frozen primary cost stress:
50 bps round trip, modeled as 25 bps adverse entry +25 bps adverse exit.

Observed:
- median delayed gross R5 = -0.9079%
- median delayed gross R15 = +0.3186%
- median delayed gross R60 = -0.5087%
- median delayed net25 R15 = +0.0682%
- median delayed net50 R15 = -0.1817%
- median delayed net100 R15 = -0.6796%
- delayed net50 R15 positive hit rate = 50.00%
- delayed net50 R15 leave-one-out median positive = FAIL
- delayed net50 positive concentration = 77.7879%
- median delayed gross R15 ex-BTC = +0.3710%
- median delayed MFE15 = +5.1617%
- median delayed MAE15 = -4.2650%

## Frozen primary execution gate
Required ALL:
- n >=12: PASS
- median delayed net50 R15 >0: FAIL
- delayed net50 R15 positive hit-rate >=60%: FAIL
- leave-one-out median delayed net50 R15 >0: FAIL
- no single observation >35% of summed positive delayed net50 R15: FAIL
- median delayed gross R15 ex-BTC >0: PASS

## AUTHORITATIVE VERDICT
NO_EXECUTABLE_EDGE_HOLDOUT

Interpretation:
- The Binance listing announcement information shock is still visibly large at/near T0 in 2025.
- The pre-registered delayed-entry strategy does NOT survive the confirmatory 2025 execution holdout under the frozen 50 bps cost stress.
- This is a scientific execution failure, not a source failure and not an operational blocker.
- The hypothesis that one can systematically capture this effect with the frozen >=60s delayed entry and 15-minute exit is rejected by this holdout.
- No post-outcome tuning is permitted within V2.0.

## Governance
V0.4: SOURCE_BLOCKED.
V1.0: SOURCE_BLOCKED.
V2.0: NO_EXECUTABLE_EDGE_HOLDOUT.

2024 remains quarantined.
2026 remains unopened.
No merge to main.
No live trading.
No orders.
No authenticated/private exchange endpoints.
No account reads.
No wallets.
No post-outcome tuning.

Any future work must be a genuinely new pre-registered economic hypothesis or execution mechanism and may not reinterpret or rescue this closed V2.0 holdout.
