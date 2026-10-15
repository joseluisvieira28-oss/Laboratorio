# V06 — MEXC Futures REAL API transport fork (2026-10-15)

**This is NOT the V05 shadow monitor. This V06 fork contains signed REAL MEXC Futures private HTTP GET and POST implementation** based on the old CryptoLab V03 operator transport: original `crypto_edge_radar/radar/mexc_operator_futures_transport_v02.py` and `mexc_auth_readonly.py`. It is a new reviewed fork targeting exactly 10× ISOLATED, LONG SOL_USDT/BNB_USDT and one integer contract at a time, not 5× V03.

Implementation in `mexc_futures_live_transport.py`:
- Exact host allowlist `https://api.mexc.com`, HMAC-SHA256 private auth, Request-Time, and explicit private GET allowlist.
- Signed POST endpoints for actual market order creation `/api/v1/private/order/create` and exchange-hosted position stop `/api/v1/private/stoporder/place`, plus bounded leverage and auto-margin API paths (not yet wired).
- Real POST transport requires a **fresh, endpoint-bound, one-use ticket from a future audited live risk controller**. No command-line option can generate a mutation ticket, and no automatic live worker is yet connected. Unknown HTTP result burns the ticket and forbids blind resend. No hot wallet, private key on GitHub or exchange actions performed during development.
- Existing user-local DPAPI encrypted secrets are accessed by `CHECK_MEXC_V06_READONLY.ps1` in the current Windows account; no keys printed. The script calls `MEXC_V06_Account_Preflight.exe --account-check`, which performs authenticated read-only position/order/stop/fee/mode reads. It does NOT inspect or place account orders.
- Windows executable built via PyInstaller on the GitHub Windows hosted runner; **does NOT require Python installed on operator's PC**. This eliminates WinGet/Python installer dependency entirely. It does NOT yet install an automatic live task.

**Critical risk/authority gap**: the presence of a signed real order POST code path does not mean a three-CONVEX live strategy supervisor is built, armable or safe. Still missing production-quality source custody+parity, independently authenticated account+position risk checks, original nonlatched 4%/12% stop on filled qty with independent ACTIVE stop readback, partial fills, close+cancel/amend semantics, crash recovery with unknown broker outcome, measured prospective after-cost live-like forward and final signoff. Same-side SOL 5m and SOL 1h cannot both have separate physical SOL LONG in ordinary MEXC hedge mode; require a single shared SOL physical slot or a proven virtual allocation. The 100 USDT 10× risk model is illustrative; loss could exceed 0.5 USDT if gap/liquidation/unprotected fill.

**VERDICT: REAL_AUTHENTICATED_TRANSPORT_IMPLEMENTED / AUTO-LIVE_EXECUTOR_NOT_COMPLETED / NO-LIVE-GO.** No real orders; no alteration to main; no old task rearmed; no secret handling off operator PC. Do not run the old V05 ZIP again to try to enable orders; it cannot.

Test:
`python -m unittest discover -s engine/three_convex_v06 -p "test_*.py" -v`

Official API references:
- https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/get-open-positions
- https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/get-current-orders
- https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/place-tpsl-order-by-position
