# V0.1 DEVELOPMENT LABEL / ACTIVITY-SHOCK CLARIFICATION
Date: 2026-10-05
Status: FROZEN BEFORE 2025 SUB-MINUTE PRICE OUTCOMES

Parent:
5110f7ebda90809de56155b4605b9621bd8fb781

## Activity-shock normalization
The baseline is a median per 5-second block.

For an event window of H seconds, expected baseline activity is:
baseline_median_5s * (H/5).

For H in {1,5,10,30,60}:
trade_count_shock_H =
event_trade_count_H / [baseline_median_trade_count_5s*(H/5)]

quote_volume_shock_H =
event_quote_volume_H / [baseline_median_quote_volume_5s*(H/5)]

If the corresponding baseline median is zero, the shock is NULL.

## Deterministic development label priority
1. ACTIONABLE_WINDOW_CANDIDATE
   if the parent frozen actionable rule passes at one or more latency buckets >=1 second.

2. HFT_ONLY_OR_TOO_FAST
   if no ACTIONABLE_WINDOW_CANDIDATE exists, but BOTH:
   - median R60 > 0
   - R60 positive hit rate >=60%

3. NO_CONSISTENT_FIRST_SECONDS_EFFECT
   otherwise.

SOURCE_BLOCKED_SUBMINUTE applies only if the source gate n<8; that gate has already passed.

## Stronger descriptive flag
COST_ROBUST_50BPS remains as defined by the metric implementation spec.
It does not alter the development label, but is required to call a latency bucket economically interesting for a future serious forward execution protocol.

No 2026 outcomes may be opened by this clarification.
