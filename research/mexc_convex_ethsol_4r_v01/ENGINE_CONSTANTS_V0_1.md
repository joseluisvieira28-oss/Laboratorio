# MEXC-CONVEX-ETHSOL-4R-001 — PRE-OBSERVATION ENGINE CONSTANTS V0.1
Date 2026-10-12. Additive to DESIGN_FREEZE_V0_1.md; original design freeze unchanged.
Status: DESIGN_ONLY; no scored outcomes, no account/exchange mutation.

These invariants are fixed BEFORE the first runtime or future price outcomes under this ID:

- Public MEXC current depth max exchange quote age = 2,000 milliseconds at receipt.
- Max consecutive quote/mark observation gap = 30,000 milliseconds, including between hypothetical entry time and first mark/BID observation. Exceeding this gives PATH_UNIDENTIFIABLE, NOT a stop loss, target or guaranteed liquidation. Such records have no positive economic credit.
- For long 1x reference, book bid/ask quote must be coherent and fresh; for any leverage-specific trial, timestamped mark and venue-specific, point-in-time liquidation threshold are mandatory. If missing, the leveraged path returns LIQUIDATION_UNIDENTIFIABLE before economic scoring.
- Stops, target and deadline are checked on observed causal BID (for long sale); no bar OHLC or post-hoc observation substitution.
- No simultaneous sub-second same-tick stop and target resolution by invented internal event ordering. If mark and stop conflict but timing cannot be proven: AMBIGUOUS_LIQUIDATION_ORDER (block).
- The 0.25% risk-of-account, 0.50% concurrent aggregate planned stop-budget, 4% underlying stop and 0.08% taker fee per side are deterministic synthetic parameters; lot rounding DOWN, never up. Max hypothetical leverage diagnostic = 20x. No authenticated tier assumed.
- The code below is an invariant test harness, NOT a live source collector, NOT a durable event store and NOT an activation. A later new freeze with code SHA and future boundary remains mandatory.
