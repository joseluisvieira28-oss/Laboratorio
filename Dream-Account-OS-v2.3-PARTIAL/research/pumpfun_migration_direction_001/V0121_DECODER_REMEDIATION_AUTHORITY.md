# PMD-001 — V0.12.1 Decoder Remediation Authority

Status: **SOURCE/DECODER PLUMBING ONLY — FROZEN V0.12 SCIENCE UNCHANGED**

V0.12.1 exists because the V0.12 pilot showed that decoder incompleteness mixed three distinct cases:

1. successful Pump trades with authoritative TradeEvent data;
2. failed transactions incorrectly counted as trade intents;
3. non-SOL quote trades whose TradeEvent correctly reports quote volume while `sol_amount` is zero.

The remediation is constrained as follows:

- W30/W60/W300 remain unchanged.
- The fixed feature family remains unchanged.
- No feature threshold, BH-FDR rule, chronological-third rule, quintile rule, cost, outcome, or promotion gate changes.
- Failed transactions do not count as successful trade intents.
- Pump trade instructions are recognized by deterministic Anchor discriminators for `buy`, `sell`, `buy_v2`, `sell_v2`, `buy_exact_sol_in`, `buy_exact_quote_in`, and `buy_exact_quote_in_v2`.
- TradeEvent decoding follows the official Pump public IDL field order.
- A non-SOL quote is never converted to SOL. Structural features (counts, sides, wallets/breadth) may remain decoder-complete when authoritative event fields exist; SOL-volume features require `sol_volume_complete=true`.
- Missing or unsupported values remain null, never zero-filled.
- This remediation has no promotion authority and does not restore holdout status.
