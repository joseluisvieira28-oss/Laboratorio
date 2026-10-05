# V0.2 TECHNICAL REMEDIATION — BITGET PAGINATION AMENDMENT 3
Date: 2026-10-05
Status: LOCKED BEFORE OUTCOME RE-RUN

A source-only forensic probe proved BOME and PNUT have Bitget spot coverage approximately 24h before T0, immediately pre-T0, and event-window candle presence. Their prior SOURCE_FAIL is therefore a retrieval defect.

Locked correction:
- Bitget retrieval uses independent 60-minute windows and deduplicates by timestamp.
- KuCoin fallback unchanged.
- Same 12 frozen observations, T0, venue hierarchy, aliases, endpoints, metrics and gates.
- Exact P0 and +1/+5/+15/+60 timestamps required.
- Original source witness rule and wall-clock volume buckets retained.
- No filtering, outlier deletion, gate changes, venue shopping, or 2025+ outcome access.
