# GEOMETRIC-TRENDLINE-001 — IMPLEMENTATION CLARIFICATION V0.1.1

Status: FROZEN PRE-OUTCOME OPERATIONAL CLARIFICATION
Parent protocol: GEOMETRIC_TRENDLINE_001_PREDISCOVERY_PROTOCOL_V0_1.md
Purpose: remove two implementation ambiguities without changing the hypothesis, parameters, source, horizon or pass gate.

1. FIRST-INTERACTION CONSUMPTION DURING COOLDOWN
If a line's first qualifying interaction occurs during the global 6h overlap-suppression window, classify it SUPPRESSED_OVERLAP and consume that line permanently. It may not emit a later event.

2. BOTH-SIDES AMBIGUITY
If support and resistance both qualify on the same hour, classify AMBIGUOUS_BOTH_SIDES, consume both involved lines, and accept neither event.

These rules prevent delayed re-labelling of an already-observed interaction and are frozen before any Discovery market source is parsed.
