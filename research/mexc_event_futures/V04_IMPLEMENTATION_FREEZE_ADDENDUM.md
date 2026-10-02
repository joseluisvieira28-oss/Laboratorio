# V0.4 IMPLEMENTATION FREEZE ADDENDUM

Date: 2026-10-02
Must be read with `V031_CLOSEOUT_AND_V04_FREEZE.md`.

Frozen implementation details before outcomes:

- Feature warm-up source begins 35 calendar days before 2026-04-01.
- Resampled chart closes are only Min5 closes whose mapped bucket-end timestamp lies exactly on the requested chart boundary.
- EMA uses the standard recursive form with alpha = 2/(period+1), initialized from the first available chart close; EMA strategy is invalid until at least 21 chart closes exist.
- RSI14 uses simple averages of positive and negative changes over the latest 14 chart-to-chart returns (15 closes). If average loss is zero and average gain > 0, RSI=100; if both are zero, no signal.
- Donchian and Bollinger reference the 20 completed chart closes strictly before the current close.
- Bollinger uses population standard deviation.
- STREAK3 uses the latest 3 chart-to-chart returns, requiring 4 closes including current.
- ROC3 compares current close with the close 3 chart bars earlier.
- RANGE20_POSITION_REV uses prior-20 min/max strictly before current; range location >=0.80 predicts DOWN, <=0.20 predicts UP.
- Event outcome is the sign of proxy close(t+H) - proxy close(t).
- If entry or outcome proxy price is absent, the observation is missing and excluded.
- Ties are recorded separately and do not count in binomial accuracy N.
- The 80% payout is an illustrative reference observed by the operator, not assumed to be historical truth.
- No September 2026 source request is permitted.
