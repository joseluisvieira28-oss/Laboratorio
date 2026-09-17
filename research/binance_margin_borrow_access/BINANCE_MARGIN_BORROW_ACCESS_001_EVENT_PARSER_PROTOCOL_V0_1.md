# BINANCE-MARGIN-BORROW-ACCESS-001 — EVENT PARSER PROTOCOL V0.1

Date: 2026-09-17  
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**  
Preconditions: `SOURCE_CENSUS_PASS` V0.4 and `EVENT_SOURCE_SCHEMA_PASS` V0.1.

## Canonical fields

Only the official article object's `code`, `title`, `publishDate` and `body` may determine event semantics. `relatedArticles`, `riskWarning`, SEO fields, navigation metadata and recommendation content are excluded from scientific classification.

`body` is parsed as article JSON when possible. Ordered article text is produced only from article text nodes. URLs, attributes and unrelated payload fields do not define event semantics.

## Direction classification

Apply in this order before asset eligibility:

1. `REMOVE` — title contains an explicit delist/remove semantic for borrowable assets;
2. `OTHER` — title is the observed collateral-haircut mechanism or body lacks an explicit new-borrow-access statement;
3. `ADD` — canonical body explicitly introduces one or more **new borrowable assets on Cross Margin** (including Cross and Isolated Margin wording).

No removal/OTHER article may enter the clean access-event universe.

## Asset extraction

For ADD articles, extract only asset identities from the canonical body section that directly states new borrowable-asset access. Accepted forms include:

- `Binance has added <ASSET EXPRESSION> as a new/new borrowable asset(s) on Cross Margin`;
- `<ASSET EXPRESSION> as a new/new borrowable asset(s) on Cross and Isolated Margin`;
- `Binance Margin will add <ASSET EXPRESSION> as a new borrowable asset on Cross and Isolated Margin`;
- structured/table sections explicitly headed `New Borrowable Assets`, provided the Cross Margin row/cell is unambiguous.

Symbol extraction prefers explicit parenthetical symbols, then unambiguous uppercase/alphanumeric asset tokens in the same source clause/cell. Pair quote assets, section labels and generic words are excluded. If a clean Cross Margin asset list cannot be recovered deterministically, the article is `ASSET_PARSE_AMBIGUOUS` and fails closed for candidate eligibility.

## Same-announcement confounds

Confounds are evaluated only from canonical title + scientific body text, after generic risk/disclaimer material is stripped.

Record independently:

- new Cross Margin trading pair(s);
- Isolated Margin access/borrowing;
- explicit same-announcement Spot listing/trading start;
- Convert;
- Earn;
- Buy Crypto;
- Futures/perpetual access.

Bundled Earn/Convert/Buy Crypto/Futures access is retained as a flag and is not automatically excluded. Only inseparable same-announcement initial Spot listing/trading start is prospectively `ACCESS_CONFOUND` for the clean mechanism universe.

## Time semantics

- `event_information_time` = official `publishDate`;
- `effective_time` = explicit UTC activation timestamp in the scientific body when one is present and unambiguous; otherwise null.

Telegram timestamps are provenance cross-checks only and may not replace official publication time.

## Evidence receipt

For each article record store:

- code and official title;
- official publication time;
- direction;
- exact extracted Cross Margin borrowable symbols;
- confound flags;
- effective time when present;
- body SHA256;
- bounded source snippet around the new-borrow-access clause/table;
- parser route (`CLAUSE`, `TABLE`, or fail-closed route).

## Source-only terminal output of parser

The parser itself does not issue the final adjudication verdict. It emits:

- `EVENT_PARSE_PASS` when all 69 frozen structural articles are classified and every ADD article has deterministic source semantics; or
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE` / `PROVENANCE_FAILURE` when canonical source or identity fails; or
- `EVENT_PARSE_AMBIGUOUS` when one or more ADD article asset lists cannot be determined under the frozen parser.

Only an `EVENT_PARSE_PASS` permits prior-Spot proof execution.

## Safety

No prices, returns, basis, abnormal returns, borrow rates, borrow inventory, PnL, win rate, PF, drawdown, authenticated exchange/account API, orders, wallets, alerts/webhooks, exchange mutation, live trading or 2025/2026 scientific data.