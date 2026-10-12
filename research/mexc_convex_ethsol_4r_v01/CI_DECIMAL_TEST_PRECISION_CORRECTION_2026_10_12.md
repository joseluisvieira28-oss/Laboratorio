# CI TECHNICAL CORRECTION — Decimal equality only — 2026-10-12

Initial branch-only synthetic run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38286104286 failed exactly 1/16 assertions: Python Decimal finite precision made +4R calculation differ by 1e-28 despite algebraic equality at unlimited precision. All 15 remaining synthetic tests passed; Python compilation passed. No market outcomes read. This is a *test precision representation* issue, not new science, optimization, rounding a fill, or outcome selection.

Replace exact Decimal equality test ONLY with an absolute tolerance 1e-24 (far below one USDT subcent and any trading increment) while retaining the fee formula, barriers, model implementation, cost and risk rules unchanged. Re-run the identical offline test suite. Preserve failed run as evidence.
