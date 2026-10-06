# DUAL PRECURSOR V0.1 — FUTURES CATALOG DISCOVERY TECHNICAL REMEDIATION
Date: 2026-10-06
Status: PRE-SPOT-OUTCOME / SOURCE-ONLY

Run 37416310090 proved the Alpha side strongly (425 2025 identity rows, 406 unique symbols, 9 ambiguous tickers) but returned zero Futures launch rows because catalogId 161 was incorrectly reused from the separate Futures-delisting source architecture.

This is a source-router technical failure, not evidence that 2025 had zero Futures launches and not a predictive verdict.

Remediation frozen before Spot outcome inspection:
- derive the correct CMS catalog/category metadata from an official known 2025 Binance Futures launch article detail;
- use that discovered official catalog route to enumerate historical Futures launch metadata;
- preserve earliest official Futures launch announcement per symbol;
- do not query or classify Binance Spot outcomes;
- do not inspect market prices/returns;
- Alpha rules, identity rules, 2025 development boundary, 2026 closed boundary and all scientific gates remain unchanged.
