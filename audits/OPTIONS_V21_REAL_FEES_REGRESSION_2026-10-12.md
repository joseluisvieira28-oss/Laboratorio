# OPTIONS V2.1 — Real-fee regression custody (12 Oct 2026)

## Scope
Research/engineering only; branch based on `options-v21-fee-zero-totalfee-hotfix-v0.1-2026-09-29`. No trade, exchange-account read, deployment, science edit, or `main` merge.

## Finding
The September 29 hotfix already addresses MEXC order replies where `totalFee=0` despite a positive `takerFee`: take a strictly positive `totalFee` if present; otherwise sum nonzero component fees. The four historical positions (8 fills) were reconciled in the contemporaneous evidence receipt. Their old receipts remain immutable and still reflect the pre-fix accounting bug.

The existing evidence receipt records 0.05378003 USDT of attributable commissions and a corrected ledger sum -0.01174003 USDT using then-available hold-fee estimates. A separate October 12 local MEXC export reconciliation reports 0.05378005 USDT and -0.01155259 USDT after funding correction. The 0.00000002 USDT fee-total difference is source precision, not a new charge. Do not assert a new exchange reconciliation from tests alone.

## New regression coverage
`crypto_edge_radar/tests/test_options_v21_real_fee_receipts_regression.py` pins all eight fee amounts to the preexisting source receipt; tests MEXC `totalFee=0` fallback, protection against double-charging positive `totalFee`, and maker-component fallback.

## Required before any activation
1. Verify which code SHA is installed in the Windows Triple Fishing V03/V04 runtime; a fix on a September branch is not proof that an installed executable contains it.
2. Independently verify each fill-level actual fee and funding against the MEXC export by execution ID, symbol, volume and timestamp, with unambiguous timezones.
3. Reject unverified/suspicious zero-fee executed taker orders rather than silently claiming a reconciled trade; preserving valid zero-fee maker promotions requires route-aware evidence.
4. Reconcile full 12 fills / six positions, ensure no double-counted funding and no duplicate receipts across branches.
5. Run regression and integration suite on the intended runtime code revision, recording test output and SHA.
6. Keep all trading permissions disarmed. Accounting correctness does not establish positive net edge; no promotion to micro-live from six positions.

No original historical receipt was overwritten. This is an additive regression test and evidence note, not a fix deployed to Windows.
