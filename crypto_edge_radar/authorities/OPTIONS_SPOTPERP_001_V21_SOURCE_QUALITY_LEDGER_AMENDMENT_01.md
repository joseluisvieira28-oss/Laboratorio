# OPTIONS-SPOTPERP-001 V2.1 — SOURCE QUALITY LEDGER AMENDMENT 01

Status: OPERATIONAL AUDITABILITY ONLY / NO SCIENTIFIC CHANGE

The live adapter already follows the frozen historical source semantics: structurally valid Deribit rows with invalid IV/index are rejected from signal eligibility while structural/provenance failures remain fail-closed.

This amendment requires every newly constructed forward signal-day evidence payload to persist the exact count of invalid-IV/index rows rejected during that day's Deribit query. The watcher run summary also reports the total rejected rows observed by newly queried days in that run.

No historical day is backfilled merely to populate this field. Existing immutable signal-day evidence remains unchanged.

Signal, DTE, moneyness, minimum instruments, direction, RV20 scaling, entry/exit timing, costs and promotion gates are unchanged. No trading/order/capital authority.
