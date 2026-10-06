# BINANCE-PERP-MARGIN-TIER-FORCED-DELEVERAGING-001
## V0.1.1 SOURCE PARSER REMEDIATION FREEZE
Date: 2026-10-06

### Trigger
The first V0.1 source-gate execution returned SOURCE_BLOCKED with:
- official_articles_in_window = 0
- list_endpoint = null
- list_pages = [{"page":1,"ok":false}]

This is a source-transport/parser failure, not a scientific or sample verdict.

### Allowed remediation
Before any market outcome access:
- inspect HTTP status, content type, response top-level keys, safe text prefix and article-metadata field names from Binance public announcement-list endpoints;
- switch between documented/public Binance announcement-list endpoint generations;
- adapt parsing to the actual public response envelope;
- preserve all scientific eligibility/sample rules from V0.1 unchanged.

### Forbidden
- no market prices/returns/volatility/volume/funding/liquidation/PnL;
- no event selection using outcomes;
- no changing sample gates, calendar, mechanism, confound exclusions or verdict thresholds;
- no 2026 market outcomes;
- no main merge/change;
- no authenticated/private endpoints.

### First-run preservation
Workflow run 37495168876 and artifact 11427895083 remain preserved as the broken source-parser run.

### Outcome declaration
No new-family market outcome has been opened.
