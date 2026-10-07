# GFIBR V0.1.2 SSR CATEGORY-IDENTITY REMEDIATION FREEZE
Date: 2026-10-07

Trigger:
- Run 37577807321 failed before event inspection with ssr_not_fee_category.
- The official SSR route /announcements/fee exposes listData.total=112 and the visible Fees page, but at least one visible first-page article carries a backend cate_id different from 55.
- No Gate mark/index values, funding-rate r values, returns or PnL were opened.

Allowed technical remediation:
- validate category identity from official Next.js route/query plus categories metadata:
  route category must be "fee";
  categories metadata must map slug "fee" to official category id 55.
- accept all articles that the official SSR itself renders on /announcements/fee, regardless of an individual article's backend cate_id.
- for API page 2+, retain the exact official client payload cate_name=fee, cate_level=2 and require successful pagination to the SSR-declared total.
- preserve all scientific/event/sample gates unchanged.

Forbidden:
- no outcome access;
- no funding-rate r field access;
- no search-engine-defined sample;
- no threshold/event-rule changes;
- no 2026;
- no main merge/trading/private endpoints.

Failed runs remain preserved.
