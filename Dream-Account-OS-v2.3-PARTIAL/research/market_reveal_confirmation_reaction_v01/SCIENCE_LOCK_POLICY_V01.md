# MRCR V0.1 — Pretarget Science Lock Policy
Status: ACTIVE / FAIL-CLOSED
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
