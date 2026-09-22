# CRYPTO EDGE RADAR — DEPLOY DRIFT FALLBACK V0.2

Date: 2026-09-22
Status: OPERATIONAL OBSERVABILITY ONLY

Problem:
The primary unauthenticated GitHub branch API can return HTTP 403 rate-limit errors from the Render runtime. V0.1 then emits UNAVAILABLE_FAIL_CLOSED, which prevents direct drift adjudication.

Frozen remediation:
1. Keep the GitHub REST branch endpoint as primary.
2. If the primary lookup fails, query the public branch Atom feed:
   https://github.com/joseluisvieira28-oss/Laboratorio/commits/crypto-edge-radar-postgres-v0.5.atom
3. Extract only a 40-hex commit SHA from a /commit/<sha> link.
4. Compare that SHA to RENDER_GIT_COMMIT exactly.
5. Never deploy automatically.
6. If both sources fail, keep UNAVAILABLE_FAIL_CLOSED and require operational attention.

No strategy, source data, timing, signal, cost, risk, promotion, trade, order, wallet, capital or database semantics change.
