# GFIBR V0.1.1 ARCHIVE ENUMERATION REMEDIATION FREEZE
Date: 2026-10-07

Trigger:
- Source-gate run 37577701081 completed source-only with EXTERNAL_SOURCE_BLOCKED.
- Its page-1 POST response reported total=2 and caused early termination.
- Prior outcome-blind official-site probe run 37577576936 demonstrated the exact store payload on page=2 returns total=112 and 15 Fees-category rows.
- SSR of https://miniapp.gate.com/announcements/fee independently exposes official listData total=112 and the official first 15 rows.
- No Gate mark/index values, funding-rate r values, returns or PnL were opened.

Allowed remediation:
- obtain page 1 and authoritative total from the official Gate Next.js __NEXT_DATA__ SSR payload for /announcements/fee;
- require SSR listData.total >= first-page row count and Fees category identity;
- enumerate page 2+ through the already-discovered official POST /api/web/v1/portal/announcement/list_article using frozen store payload:
  cate_name=fee, size=15, tags="", timer="", cate_level=2;
- deduplicate by article id;
- continue until the expected official total is reached or fail source-closed;
- preserve every scientific/event/sample gate unchanged.

Forbidden:
- no market outcomes;
- no funding-rate r field access;
- no search-engine-defined sample;
- no threshold changes;
- no 2026;
- no main merge/trading/private endpoints.

Failed run 37577701081 remains preserved.
