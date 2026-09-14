# OPTIONS-SPOTPERP-002 — OOS Timestamp Correction Receipt V0.2

Status: TECHNICAL_CORRECTION_ONLY
Date: 2026-09-14
Branch: options-spotperp-002-tier1-2025-v01
Prior failed run: 34859148788
Prior classification: TECHNICAL_FAILURE (non-scientific)
Prior Source/Data Gate: SOURCE_AUDIT_PASS
Prior valid source days: 365

## Scope

This receipt documents a technical-only correction after the prior 2025 OOS runner failed while parsing Binance spot daily timestamps. The failure occurred before any terminal OOS scientific classification was produced.

The correction normalizes Binance spot timestamps by magnitude:
- millisecond timestamps remain unchanged;
- microsecond timestamps are divided by 1000;
- unexpected magnitudes fail closed.

## Scientific invariants preserved

No change to:
- candidate regime: UP_LOW only;
- signal definition;
- DTE filters;
- moneyness filters;
- minimum distinct instruments;
- 2025 OOS window;
- base cost: 10 bps;
- stress cost: 20 bps diagnostic only;
- minimum entered trades: 80;
- beta/sign gate;
- base-net economics gate;
- profit-factor gate;
- quarterly stability gate;
- concentration gate;
- 2026 lock;
- no live trading;
- no exchange mutation;
- no merge to main;
- no tuning, cherry-picking, parameter rescue or subperiod rescue.

## Provenance

Failed-run head: 9803b7825c26b02a27cf97d73c7b0dafe0ae5df2
Corrected scientific branch head before this receipt: 2e74208923752dca02da4d75261a6de234b5b2e6
Diff 9803b782..2e742089: exactly one file modified, confirmation_runner_2025_v01.py, with 9 additions and 1 deletion limited to Binance timestamp normalization.

This receipt intentionally lives under the research path so the unchanged 2025 Confirmation workflow is triggered by a new push and executes the corrected branch state prospectively. Any resulting OOS_REPLICATED, OOS_FAILED or INSUFFICIENT_SAMPLE verdict is scientific and terminal under the frozen authority. Any new execution/data blocker remains non-scientific.
