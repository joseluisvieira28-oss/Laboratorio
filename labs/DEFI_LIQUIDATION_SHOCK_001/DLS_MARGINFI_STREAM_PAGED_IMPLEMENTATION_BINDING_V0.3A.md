# DLS MARGINFI STREAM-PAGED COLLECTOR — IMPLEMENTATION BINDING V0.3A

Date: 2026-10-02
Status: FROZEN BEFORE USE

Authority:
- program-only transport addendum commit: 82004a2c236198c284c33a12d62f8bf21a9b8b40
- stream-paged addendum commit: 73267e81a64fa203c111b86d681571fb2a96e899

Parent derived collector blob:
e136e109d7d3dd08fb4f208eaafd2ae41f9f7d55

Stream-paged collector:
- path: labs/DEFI_LIQUIDATION_SHOCK_001/source/collect_protected_2025_marginfi_stream_paged_v0_3a.py
- Git blob: f0cd93f46d1099f81c7e5adb79a26c5ce2d02180

Only additional change:
request_to = exact month end slot rather than min(month end, current + 9,999).
Continuation remains last observed block + 1.

No source semantics or science changed.
Market outcomes closed.
Trading authority: NONE.
