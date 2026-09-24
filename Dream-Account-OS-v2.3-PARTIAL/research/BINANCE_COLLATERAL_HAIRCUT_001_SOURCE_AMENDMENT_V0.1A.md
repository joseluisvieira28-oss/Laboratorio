# BINANCE-COLLATERAL-HAIRCUT-001 — SOURCE ENUMERATION TECHNICAL AMENDMENT V0.1A

Date: 2026-09-24
Reason: immutable Telegram archive provided complete 2024 temporal coverage but zero canonical Binance article codes for this announcement family.

No market price, return or PnL outcome has been opened.

## Transport correction only

Replace Telegram-link article-code enumeration with the public Binance CMS article-list endpoint used by the Binance announcement interface:

`https://www.binance.com/bapi/composite/v1/public/cms/article/list/query`

Rules:
- enumerate the CMS index deterministically by page;
- metadata outside 2024 may be traversed only as necessary to reach the frozen 2024 interval;
- do NOT hydrate article bodies outside 2024;
- retain only official-index articles whose release timestamp is within 2024;
- among those, hydrate every title containing both "collateral ratio" and "margin";
- canonical article-detail endpoint remains unchanged;
- the four pre-frozen positive controls remain mandatory;
- source gates, event parsing, Discovery hypothesis, sample thresholds and all outcome firewalls are unchanged.

This amendment changes only source enumeration transport. It cannot add/remove articles based on market outcomes because none have been opened.
