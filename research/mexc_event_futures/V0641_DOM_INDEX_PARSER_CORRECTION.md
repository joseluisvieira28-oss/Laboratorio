# MEXC EVENT FUTURES LAB — V0.6.4.1 DOM INDEX PARSER CORRECTION

Date: 2026-10-02

V0.6.4 returned zero valid pairs because the source parser did not extract the visible Index chart Close from the DOM context. No numerical equivalence result was produced.

V0.6.4.1 changes only the parser:
- it tolerates bidirectional/invisible characters between "Close:" and the first numeric token;
- it captures the first numeric Close token explicitly;
- it prints the first sample per asset for auditability.

The pre-frozen sample count, tolerance, gate, assets and read-only boundaries remain unchanged.
Settlement equivalence remains NOT_PROVEN regardless of this current-display diagnostic.
