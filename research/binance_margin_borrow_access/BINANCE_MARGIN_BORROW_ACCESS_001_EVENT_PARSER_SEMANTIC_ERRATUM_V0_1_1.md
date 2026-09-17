# BINANCE-MARGIN-BORROW-ACCESS-001 — EVENT PARSER SEMANTIC ERRATUM V0.1.1

Date: 2026-09-17  
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**

## Trigger

V0.1 resolved all 69 source articles technically, but canonical aggregation identified four ADD records with no deterministic asset list. Inspection of the already-authorized official source schema evidence showed that the issue was not missing data; it was an over-broad Cross-Margin proximity test.

No market outcome, price, return, PnL, borrow rate or inventory was inspected.

## Frozen correction

An article is `ADD` only when the **borrow-access clause itself** explicitly attaches the new borrowable asset(s) to:

- `on Cross Margin`; or
- `on Cross and Isolated Margin` / equivalent `Cross & Isolated Margin`.

A nearby statement about **trading pairs** on Cross Margin is not evidence that borrowing itself was enabled on Cross Margin.

Therefore these source forms are prospectively non-eligible for this mechanism:

- `new borrowable assets on Isolated Margin, as well as new trading pairs on Cross and Isolated Margin` -> `OTHER`;
- `new borrowable asset on Margin, with new trading pairs on Cross and Isolated Margin` -> `OTHER`;
- `new borrowable asset as well as new margin pairs on Cross Margin` -> `OTHER` unless the canonical source separately and explicitly attaches the borrowable asset to Cross Margin.

This is a semantic tightening to match the original frozen hypothesis, not a relaxation or rescue.

## Exact-asset fail-closed rule

The adjudication authority requires exact newly-borrowable Cross Margin asset identities. A source clause containing an unresolved open-ended expression such as `and more as new borrowable assets` cannot be represented as a complete exact asset list solely by extracting the named symbols preceding `and more`.

Such an article is `ASSET_LIST_OPEN_ENDED` and is excluded from the clean candidate universe unless the same canonical article contains an authoritative structured section that closes the list exactly. It does not invalidate other deterministic articles.

## Known V0.1 diagnostic cases

The four V0.1 ambiguous articles are source-semantically non-Cross-borrow ADDs under this erratum:

- `3fc2f02aef2d4d3fbac2524f301027a2` — ALPINE/BAR/CITY/PSG: borrowable on Isolated Margin only;
- `07d0c50b9bff4e92a8035d158aa94dd4` — DCR: borrowable on Isolated Margin only;
- `541daaa5499d4b34a737c97c50c8547e` — TRU: borrowability venue not explicitly attached to Cross; Cross applies to margin pairs;
- `b4eb91b68a1a4dc1b2a2f45d7b8f1a1e` — NTRN: generic `on Margin`; Cross/Isolated applies to pairs.

One additional canonical ADD clause is open-ended and must fail closed for exact asset identity unless closed elsewhere in the article:

- `32cce2a500ef4af5be01c8edf02977f3` — `AC Milan Fan Token (ACM), FIO Protocol (FIO), IQ (IQ) and more as new borrowable assets on Cross and Isolated Margin`.

## V0.1.1 terminal semantics

`EVENT_PARSE_PASS` requires every retained ADD article to have an explicit Cross-borrow clause and a closed exact asset list. Articles classified `REMOVE`, `OTHER`, or `ASSET_LIST_OPEN_ENDED` do not enter the clean candidate universe and do not by themselves make the parser fail.

Coverage/identity/source acquisition failures remain fail-closed terminal failures.

## Safety

Still forbidden: prices, returns, basis, abnormal returns, borrow rates, borrow inventory, authenticated account/API data, PnL, win rate, PF, drawdown, 2025/2026 scientific data, orders, wallets, alerts/webhooks, exchange mutation and live trading.