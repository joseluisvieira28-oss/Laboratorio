# LCOD MULTI-BORROWER BLOCK-PIN TECHNICAL REMEDIATION V0.1A

Date: 2026-09-25
Science change: NONE
Outcomes: CLOSED

Initial 16-pair same-block scale selected 16 debt-bearing pairs at one finalized
Ethereum block. Nine reconstructions completed and all nine matched official
Aave HF exactly (relative error 0). Seven remaining cases failed only because
the public Blast RPC returned HTTP 429 rate-limit errors.

No completed borrower failed the frozen <=5e-5 tolerance.

Technical correction:
- keep the same deterministic candidate/selection rule;
- keep TARGET=16;
- keep the same formula and frozen tolerance;
- keep all scientific calls pinned to one finalized block per run;
- add bounded retry/backoff only around eth_call failures.

A remediation run may use a new finalized block because no market/liquidation
outcome was opened and raw wallet addresses from the prior run were not retained.

PASS condition remains unchanged:
16 selected / 16 reconstructed / 16 within tolerance / zero unresolved errors.

No curve or market outcome is authorized by this remediation.
