# BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001 — V0.1.2 DETAIL HTML PARSER TECHNICAL REMEDIATION
Date: 2026-10-05
Status: FROZEN BEFORE MARKET OUTCOMES

## Trigger
The hardened V0.1.1 source probe found 49 candidate metadata rows / 72 broad candidate rows but mechanically classified zero articles.

This conflicts with already source-proven official examples such as the known XEMUSDT/ORBSUSDT/LOOMUSDT automatic-settlement notice.

The failure is classified TECHNICAL_SOURCE_PARSER_FAILURE, not NO_EDGE and not an economic result.

## Root-cause hypothesis
The V0.1.1 classifier flattened raw CMS JSON/HTML and then required literal contiguous English phrases. CMS article body markup can interrupt those phrases.

## Frozen remediation
Before any market outcome is opened:
1. inspect only the official CMS article detail body/title;
2. HTML-unescape;
3. strip markup;
4. collapse whitespace;
5. require BOTH:
   - position-closing language: "close all positions"; and
   - automatic-settlement language within the same official article body: "automatic settlement" or "automatically settle";
6. extract USDⓈ-M symbols only from the normalized article body;
7. preserve announcement metadata and amendment/rebrand tags;
8. do not inspect price, mark, index, OI values, returns, basis, PnL or 2026 market outcomes.

A known qualifying XEM article is a source-parser self-test only. It cannot set any economic threshold or horizon.

Science/governance otherwise unchanged.
