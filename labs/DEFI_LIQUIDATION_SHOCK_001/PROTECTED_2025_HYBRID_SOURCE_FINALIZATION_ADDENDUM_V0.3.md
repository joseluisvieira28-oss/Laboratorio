# DLS PROTECTED-2025 HYBRID SOURCE FINALIZATION ADDENDUM V0.3

Date: 2026-10-02
Status: FROZEN SOURCE-ONLY / OUTCOMES CLOSED

Purpose:
Finalize the exact canonical Protected-2025 source population from scientifically equivalent transport
partitions without rerunning already-PASS evidence.

Authorized partition composition is exactly:
A. 28 immutable canonical SQD monthly PASS receipts pinned by
   PROTECTED_2025_SOURCE_RECOVERY_MANIFEST_V0.3.json.
B. 8 exact missing non-Marginfi monthly partitions from
   DLS Protected 2025 Targeted SQD Recovery V0.3.
C. 12 exact Marginfi monthly partitions from the pre-frozen programId-only SQD transport V0.3.

All 48 receipts must:
- retain the original PROTECTED_2025_PROTOCOL_SOURCE_PASS classification;
- have exact protocol/class identity;
- have exact 2025 calendar-month window;
- have duplicate_count=0 and error_count=0;
- retain prices/returns/PnL/2026 firewalls false.

Finalization:
Use the existing scientific finalizer
source/finalize_protected_2025_source_v0_2.py unchanged.

It must observe exactly 48 unique protocol-month receipts and emit only:
PROTECTED_2025_SOURCE_AUTHORITY_PASS
or
PROTECTED_2025_SOURCE_AUTHORITY_BLOCKED.

No quarter/month manifest mixing beyond the exact monthly V0.2 schema is allowed.
No duplicate protocol-month may be silently chosen; duplicate file identity blocks finalization.

A PASS authorizes only the already-frozen 2025 economic holdout under
STRATEGY_TRANSLATION_FREEZE_V0.1 and PROTECTED_2025_ECONOMIC_HOLDOUT_IMPLEMENTATION_FREEZE_V0.1.

No market price may be read before source authority PASS.
No 2026 source/outcome is authorized.
No live trading/orders/wallets/exchange mutation/main merge.

Trading authority: NONE.
