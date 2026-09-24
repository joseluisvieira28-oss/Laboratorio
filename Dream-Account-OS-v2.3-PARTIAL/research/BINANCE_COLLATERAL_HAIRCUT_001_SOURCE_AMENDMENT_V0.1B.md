# BINANCE-COLLATERAL-HAIRCUT-001 — SOURCE ENUMERATION TECHNICAL AMENDMENT V0.1B

Date: 2026-09-24

Official CMS catalog probe established:
- catalogId 48 = New Cryptocurrency Listing
- catalogId 49 = Latest Binance News

The generic article-list endpoint returns a multi-catalog snapshot rather than a complete chronological archive.

Technical correction:
- enumerate the official catalog-list endpoint for exactly catalogId 48 and 49;
- page each catalog backward until crossing 2024-01-01;
- union and deduplicate article codes;
- hydrate bodies only for retained 2024 articles whose title contains "collateral ratio" and "margin", plus the four pre-frozen controls;
- no market outcomes are opened.

Scientific hypothesis, source gate thresholds, event parser, 2024 Discovery protocol, 2025/2026 protection and all no-rescue rules remain unchanged.
