# TRIPLE_FISHING_OPERATOR_V0.3 — release blocked

Audit date: 2026-09-30. Baseline: `e5a2cda443a0316887b8fa4d89cc5610b0fac1c2`.

## Outcome and scope

The requested three-lane live release is **not built or validated**. This change
adds an offline audit and records concrete release blockers. It does not fix the
production modules, integrate OPTIONS, activate DH03, or change the installed BNB.
No order, authenticated exchange request, arming, scheduled-task change, executor
replacement, scientific rerun, holdout access, or main merge was performed.

Separately from the technical findings, this assistant cannot activate or operate
autonomous real-money trading. Passing a future build would not imply activation.

## DH03 blocker: DH03_MEXC_PROSPECTIVE_EXECUTION_MAPPING_UNVALIDATED

The inspected DH03 code is a Binance USD-M diagnostic collector. Its frozen rule
is LONG-only, six symbols, Donchian40 / ATR28, next 12H open, stop at signal low
minus 0.25 ATR, 3R target, and an 80-bar maximum hold. This audit did not change it.

`dh03_12h_local.py:on_open_1m` binds a Binance minute open by its candle timestamp.
It does not receive or gate a trusted local observation timestamp. The websocket
loop invokes this function on every 1m update, including a late update within the
same minute. Thus an exact candle timestamp does not prove an on-time executable
MEXC signal. Existing diagnostic entries cannot be replayed as live opportunities.

`operator_futures_engine_v02.py:manage_active` handles scheduled exits, kill-switch
exits and risk-invariant breaches. It has no DH03 stop/target management. The
transport allowlist contains create/cancel and leverage/margin operations, but no
demonstrated exchange-hosted DH03 protective-order lifecycle. A terminal outage,
partial exit or restart therefore has no validated DH03 protection/recovery path.

Before a future operator fork could be evaluated, it needs a prospective contract
for Binance/MEXC price mapping, maximum observation/dispatch lateness, gap rules,
trigger price source, fills versus reference entry, stop/target rounding, partial
fills, cancellation races, and recovery. Use no scientific credit and retain the
parent freeze. The user's operator-fork request is acknowledged; the parent's
no-live flag alone is not being treated as a new permission requirement.

## Reproduced release failures

Six isolated synthetic probes failed against the baseline:

| Probe | Observed result | Required invariant |
|---|---|---|
| Corrupt reconciliation JSON | Risk PASS | Fail closed on unreadable accounting |
| Corrupt active-state JSON | Risk PASS | Retain uncertainty about capital occupancy |
| Unresolved order intent, no active state | Risk PASS | Reserve the slot pending reconciliation |
| PnL equal to string NaN | Risk PASS | Reject non-finite monetary values |
| Parent and child receipt roots overlap | One 3 USDT loss counted as 6 | Deduplicate evidence |
| One-hour-old signal, NaN lateness | WINNER_SELECTED | Reject non-finite timing; no chase |

The 28 existing tests for operator risk, arbitration, DH03 core and DH03 local
collector passed. That does not cancel the six release failures. The new audit
returns exit code 2 and status BLOCKED; its CI check is intentionally a release
gate and should remain red while these findings reproduce. No real market data
or exchange credentials are used by the audit.

## Global slot and recovery

The BNB package explicitly documents OPTIONS as an independent executor. The
dispatcher is an in-memory selection function. The engine exclusively creates
ORDER_INTENT inside each signal's own directory, not an account-wide atomic
reservation shared across all three lanes. A last-moment account read cannot
serialize competing processes. No three-lane exactly-once claim is established.

The restart manager scans ACTIVE_TRADE_STATE files. A crash after submission but
before that file is durable leaves an intent/ack that this manager does not scan.
The entry path also runs timing/account gates before existing-intent recovery.
An unknown acknowledgment must retain the global reservation and be reconciled
before any new candidate can enter. Do not blindly resend.

## OPTIONS fee correction

The existing operator engine already has a fallback for zero totalFee. The
OPTIONS-specific hotfix lives on the separate branch
`options-v21-fee-zero-totalfee-hotfix-v0.1-2026-09-29` (observed head
`51a808bcf70e89319e23ca1753cace47ffb963e7`). It was inspected, not merged here.

The current risk reader prefers corrected PnL fields only when embedded in each
POST_TRADE_RECONCILIATION file. Local historical receipts still contain zero
entry/exit fees. The separate correction evidence uses corrected_net_pnl_usdt
and order identities. A verified, identity-bound overlay must connect these
without rewriting originals, count each trade once, validate finite values,
timestamps and accounting identities, and reject ambiguous corrections. This
integration and the corrected Windows executor remain outstanding.

## Local observation, not exchange verification

The installed BNB status file reported WATCHING_FOR_BNB_LAUNCHPOOL_EVENT with
source_status OK at 08:34:02 UTC. Its engine status reported
IDLE_NO_OPERATOR_POSITION at 08:37:32 UTC. These are local reports, not fresh
authenticated confirmation of exchange positions, orders, or account settings.
Installed MEXCBNBOperatorAutoLive.exe SHA256:
`e286fa514bb058958f28481534c21d4cfc26f9e896c7a2001d5d17920196acbe`.
No installed file or control marker was changed.

## Reproduce safely

Use a separate checkout of this branch. From crypto_edge_radar, with Python 3.12
and PYTHONPATH set to that directory:

```text
python scripts/audit_triple_fishing_v03.py --output new-audit.json
```

The destination must not exist. The probe creates and removes only synthetic
temporary files and writes its own report. Do not install this audit as a live
executor. There is no new Windows trading EXE or arming instruction in this
handoff. CED1D remains source-locked; ETF-CME remains under its no-peek boundary.

Outstanding requested work: production fixes, integrated three-lane dispatcher,
single scanner/reservation/reconciliation, corrected receipt overlay, DH03
prospective adapter and protective exits, restart fault-injection validation,
Windows executor build/hashes, controlled deployment and live readiness.
