# MRCR V0.1 — Pretarget Science Lock Policy
Status: ACTIVE / H02 DESIGN FROZEN / TARGET FAIL-CLOSED
Date: 2026-09-24

This lock exists to prevent accidental arming of MRCR before a separate explicit scientific authority exists.

While this lock is active, CI must fail if the canonical templates indicate any of the following:

- H02 authorized;
- target observation authorized;
- complete official prospective calendar declared;
- event families selected in the canonical pretarget template;
- venue/symbol target scope selected;
- anchor definition selected;
- decision clock selected;
- depth mode/value selected;
- classifier or abstention rule selected;
- future outcome horizon/definition selected;
- benchmark selected;
- economics activated;
- protocol freeze timestamp/operator authority/fingerprint populated;
- live/paper trading or exchange mutation represented as allowed.

This lock does not claim that these fields can never be set.

It means they may only be set after a **new, separately documented authority transition** that explicitly supersedes this pretarget lock.

The lock is intentionally independent of scientific merit. It protects chronology and prevents an implementation edit from silently becoming scientific authorization.

Final rule:

**NO AUTHORITY TRANSITION -> NO SCIENTIFIC ARMING.**


## Freeze chronology hardening — 2026-09-25

The future authority transition is now explicitly two-stage:

1. H02_DESIGN_FREEZE authority may supersede this lock only for scientific
   design/freeze work. Target observation must remain false while the protocol
   is frozen.
2. TARGET_OBSERVATION_OPEN is a later authority that may exist only after a
   complete frozen protocol, official calendar manifest and implementation
   manifest exist. The target-open receipt must bind all three exact
   fingerprints and an earliest target timestamp after the freeze/authority
   boundaries.

Structural freeze validation therefore rejects any protocol that marks target
observation authorized before freeze completion.

Current state after explicit operator authorization on 2026-09-25:

- H02_DESIGN_FREEZE authority is ACTIVE;
- the H02 scientific ruleset is frozen and fingerprinted;
- the canonical final protocol template remains target-locked and unpopulated
  until the complete official 2027 calendar exists;
- target observation remains NOT AUTHORIZED;
- live/paper trading and exchange mutation remain prohibited.

The lock now protects the frozen H02 ruleset against mutation and protects the
target boundary until a later exact TARGET_OBSERVATION_OPEN authority exists.
