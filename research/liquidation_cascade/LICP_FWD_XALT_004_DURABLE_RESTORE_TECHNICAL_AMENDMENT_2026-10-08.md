# LICP-FWD-XALT-004 — DURABLE RESTORE TECHNICAL AMENDMENT 2026-10-08

Status: TECHNICAL_ONLY / PRE-OUTCOME_FIX

## Defect

Authoritative continuation run `37732159597` failed before the observer step while restoring prior durable state.

The workflow shell exported `GITHUB_REPOSITORY`, but the embedded Python snippet attempted to use the shell-style repository token inside Python. That token was not a Python variable and produced:

`NameError: name 'GITHUB_REPOSITORY' is not defined`

No new forward observer was started and no new XALT-004 outcome was opened by the failed run.

## Fix

Workflow commit: `486af1fba6dd0ed08a57c356c0b1b7e102b4a029`

The Python restore snippet now reads `repo = os.environ["GITHUB_REPOSITORY"]` and uses that value only to download the latest prior immutable XALT-004 state artifact.

## Scientific invariants unchanged

No change to trigger config, SELL-only eligibility, BTC confirmation, SOL_USDT target, 60-second entry delay, 60-minute exit horizon, 16 bps round-trip fee hurdle, 120-second cooldown, 20-event / 3-date / <=10% missing gate, historical holdout, or existing 4-event forward baseline.

Prior duplicate run `37732360638` remains NON_AUTHORITATIVE_REDUNDANT_TRANSPORT.

The next continuation launched from the fixed workflow is a new future-boundary technical retry.
