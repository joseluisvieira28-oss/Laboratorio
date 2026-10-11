# ASYMMETRIC ECONOMIC HURDLE — LOCAL SYNTHETIC TEST RECEIPT
Date: 2026-10-11
Status: LOCAL_TESTS_PASS / SYNTHETIC_ONLY / NOT CI / NO MARKET OUTCOMES

Execution: Python 3.13.5, six unittest cases on locally reproduced
copies of the two new Python files. Their byte lengths match the verified
GitHub source files (economic_hurdle.py 3589 bytes, test_economic_hurdle.py
1824 bytes). NOT a GitHub CI run and NOT evidence of strategy success.

Cases all PASS:
1. Zero-fee 4R theoretical break-even = 20%.
2. Stop=40 bps; 4R; 16 bps fee => 28% break-even, +3.6R win.
3. Fee stress 32 bps + illustrative 8 bps extra => 40% break-even.
4. Only 20% winners at stop=40 bps/base fees => negative expected R.
5. Stop=10 bps, 1R target, 16 bps fee => no feasible break-even.
6. Reject invalid/negative/non-finite parameters.

Sample calculator invocation (sensitivity, never a trading signal):
python research/asymmetric_shock_breakout/economic_hurdle.py --stop-bps 40 --target-r 4 --assumed-win-rate 0.30

Output conditions: cost=0.4R; net winner=+3.6R, net loser=-1.4R,
assumed p=0.30 => hypothetical expected +0.1R/trade. The assumed win rate
is NOT ESTIMATED from historical or forward markets. Execution gap-through-stop,
adverse selection, liquidity, position size, funding and stop/target path
risk have not been validated. Therefore NO EDGE claimed.

Repository source files:
research/asymmetric_shock_breakout/economic_hurdle.py
research/asymmetric_shock_breakout/test_economic_hurdle.py

Operations: no orders, no external calls, no exchange authentication,
no wallets, no capital, no main change.
