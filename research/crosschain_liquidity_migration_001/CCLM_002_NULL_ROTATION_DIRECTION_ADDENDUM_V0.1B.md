# CCLM-002 NULL ROTATION DIRECTION ADDENDUM V0.1B

Frozen: 2026-09-25
Parent: CCLM_002_DISCOVERY_IMPLEMENTATION_ADDENDUM_V0.1A
Price outcomes at freeze: CLOSED

This addendum resolves only the sign convention of the already frozen monthly
circular shift.

For a sampled positive integer offset k:
- use NumPy semantics np.roll(month_flow, +k);
- the raw flow originally at zero-based hour index i moves to
  (i + k) mod month_hours.

Offsets are still drawn independently for each calendar month from the already
frozen inclusive interval [48, month_hours - 48] using
NumPy Generator(PCG64(seed=20260924)).

No negative-offset alternative, bidirectional search, best-of direction or
replacement draw is permitted.

Everything else in the parent Discovery/null freeze remains unchanged.
