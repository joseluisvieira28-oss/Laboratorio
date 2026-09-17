# BINANCE-MARGIN-BORROW-ACCESS-001 — EVENT SOURCE SCHEMA CLOSEOUT V0.1

Date: 2026-09-17  
Branch: `binance-margin-borrow-access-v0.1`

## Verdict

**EVENT_SOURCE_SCHEMA_PASS**

This is an outcome-blind source-schema result only. No market outcome or economic performance was opened.

## Canonical run

GitHub Actions run: `35244826795`.

All four deterministic schema shards passed and resolved the frozen 69 structural source articles exactly once.

## Observed canonical article structure

Across the 69 official Binance Support payloads, the scientific article fields are stable at the top-level article object:

- `title` — canonical article title;
- `body` — canonical article body/content JSON;
- `publishDate` — official publication timestamp;
- `code` — canonical article identity.

The payload also contains non-scientific auxiliary fields such as `relatedArticles`, `riskWarning`, SEO fields and navigation metadata. Those fields can contain unrelated contemporary words such as Spot/Futures and must not be used to classify same-announcement confounds.

## Observed structural families

The frozen 69-article schema universe contains:

- 58 ordinary ADD-style margin access articles;
- 6 explicit `Will Delist ... Borrowable Asset(s)` removal articles;
- 4 `Will Add ... on Earn, Buy Crypto, Convert, Margin & Futures` bundled-access articles;
- 1 `Binance Margin Introduces Collateral Haircuts on Cross Margin` article whose generic phrase `borrowable assets` is not a new-borrow-access event.

These counts are structural/source observations only.

## Parser consequence

Production adjudication must:

1. classify only from canonical `title` + parsed `body` + `publishDate` + `code`;
2. exclude `relatedArticles`, `riskWarning`, SEO fields and auxiliary navigation content from event/confound semantics;
3. parse the JSON body into ordered article text rather than concatenating the entire payload;
4. classify explicit delist/removal articles as REMOVE before asset eligibility;
5. classify the collateral-haircut article as OTHER before asset eligibility;
6. preserve bundled Earn/Buy Crypto/Convert/Futures flags without automatically treating them as Spot-listing confounds;
7. fail closed when newly-borrowable Cross Margin asset identity cannot be recovered unambiguously.

## Safety

No prices, returns, basis, borrow rates, borrow inventory, account/authenticated API data, PnL, PF, win rate, drawdown, 2025/2026 scientific data, orders, wallets, live trading, alerts/webhooks or exchange mutation were opened.

## Next permitted phase

Freeze and execute the production event parser under `EVENT SOURCE ADJUDICATION AUTHORITY V0.1`. Discovery remains forbidden.