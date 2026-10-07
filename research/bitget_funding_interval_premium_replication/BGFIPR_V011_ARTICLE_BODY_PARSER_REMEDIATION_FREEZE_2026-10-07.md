# BGFIPR V0.1.1 ARTICLE-BODY PARSER REMEDIATION FREEZE
Date: 2026-10-07

Trigger:
- Initial source-gate run 37580178354 enumerated the full official Futures archive through before 2024 and opened ZERO market outcomes.
- The runner falsely marked 499/499 in-window articles as candidates because BeautifulSoup page text included navigation/related-article titles containing funding terms.
- It also treated the adjustment-details schedule rows as additional effective timestamps instead of isolating the official "Adjustment time" field.

Allowed outcome-blind remediation:
- isolate article text beginning at the article H1 and ending before "Related articles" / footer content;
- candidate classification may use only article title + isolated article body;
- effective timestamp must be taken from the explicit "Adjustment time:" field or the equivalent sentence stating the adjustment occurs "on <date> at <time> (UTC±x)";
- ignore later schedule rows for T_effective;
- preserve calendar, old->new shortening definition, sample gates, controls reserved for later analysis, concentration gate and verdict taxonomy unchanged.

Forbidden:
- no premium/funding/mark/index/return/PnL values;
- no threshold changes;
- no event selection based on outcomes;
- no 2026;
- no main merge/trading/private endpoints.

Run 37580178354 remains preserved as parser-invalid, not a scientific source verdict.
