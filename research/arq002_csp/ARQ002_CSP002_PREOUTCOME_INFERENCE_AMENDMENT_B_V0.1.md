# ARQ-002-CSP-002 — PRE-OUTCOME INFERENCE AMENDMENT B V0.1

Date: 2026-09-23
State when frozen: SOURCE_MASK_PASS; no CSP-002 economic outcome opened.

## Bootstrap draw semantics

Let the D-confirmed sample contain observations grouped by UTC event date.

For each of 10,000 repetitions:
1. let K be the number of unique UTC dates with at least one D-confirmed observation;
2. draw exactly K UTC dates independently with replacement using seed 2002001;
3. each selected date contributes every D-confirmed observation on that date;
4. if a date is selected multiple times, all of its observations are repeated the same number of times;
5. bootstrap statistic = unweighted arithmetic mean of BASE14 returns in the resampled observations.

## Percentile semantics

Sort the 10,000 bootstrap means ascending.

For percentile p in {0.025, 0.975}:
- position = p * (N - 1), N=10,000;
- lo = floor(position), hi = ceil(position);
- if lo == hi use that value;
- otherwise linearly interpolate between sorted[lo] and sorted[hi].

Gate 7 requires the 2.5th percentile to be strictly > 0.

No alternate bootstrap, block length, quantile convention or one-sided interval may be substituted after outcomes.

## Mean semantics

Every Discovery mean is the ordinary unweighted arithmetic mean over the observations specified by the gate.

No trade weighting, volume weighting, month weighting or side weighting.

## Manifest binding

The canonical source manifest must have SHA256:
`67058b6e4575f1a3a442c05cf4a57a66e354ee058848aa9b10caaa0648cf36ea`

Any other manifest hash => SOURCE_PROVENANCE_FAIL before outcomes for the affected job.
