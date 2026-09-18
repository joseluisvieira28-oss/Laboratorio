# EXCHANGE-DELISTING-SHOCK-001 — V0.4.1 PARSER ERRATUM

Date: 2026-09-18
Parent run: 35311360854
Source gate ID: EDS-BINANCE-FULLTOKEN-SYMBOLIDENTITY-002

The first V0.4 execution produced 0 qualified events with 14 article-level
NO_OFFICIAL_NAME_SYMBOL_DELIST_LIST rejections.

Cause: the implementation regex ended the intended token(s)/tokens anchor with
a word-boundary assertion. For the common literal form "token(s) " the character
before the following space is ")" (non-word) and the space is also non-word, so
the word-boundary assertion cannot match.

This is a parser implementation defect, not a scientific/source-rule change.

Correction:
- replace the trailing word-boundary with an explicit lookahead for whitespace or colon;
- preserve official Name (SYMBOL) identity requirement;
- preserve exact-pair membership on either side;
- preserve SYMBOLUSDT market-route convention;
- preserve 30 events / 15 tokens / 2023+2024 minimums;
- preserve all outcome/protected-period firewalls.

No market price, return or PnL was opened in the parent run.
