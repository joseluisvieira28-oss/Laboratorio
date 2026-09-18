# CROSS-VENUE-DIAMOND-REPLICATION-001 — SOURCE TRANSPORT REMEDIATION CORRECTION 01A — 2026-09-18

Status: FROZEN_BEFORE_REMEDIATED_SOURCE_PROBE_AND_BEFORE_ANY_SIGNAL_OR_OUTCOME_CALCULATION
Supersedes only the OKX module-discovery wording in Amendment 01.

Correction:
The official OKX Python SDK exposes `module` as a string parameter. Therefore the Amendment-01 phrase allowing enumeration of integer values 1..10 is withdrawn before it is used.

Allowed metadata-only module discovery is now:
1. send one deliberately invalid sentinel module `__SOURCE_ENUM_PROBE__` to capture provider validation metadata/message if available;
2. test only semantic module strings supported by current official documentation/changelog terminology for the six historical modules: trade history, candlestick, funding rate, and 50/400/5000-level orderbook data;
3. for this experiment, only candlestick and funding-rate module metadata are scientifically relevant;
4. do not download archive payload bytes during module discovery;
5. persist the exact accepted module string and provider-returned archive metadata before any archive payload is opened.

Everything else in Amendment 01 and the parent freeze remains unchanged.
