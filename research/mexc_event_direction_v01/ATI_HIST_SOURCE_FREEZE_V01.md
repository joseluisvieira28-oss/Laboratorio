# Event Futures ATI Source Gate V0.1 (29 October 2026)

SOURCE_ONLY / NO OUTCOMES / NO EDGE / NO TRADING.

## Identity and pre-read gate
- Exact historical source: official Binance Vision USD-M Futures daily aggTrades, BTCUSDT and ETHUSDT, 2026-04-01 UTC, public ZIP + publisher SHA256 CHECKSUM.
- Source period April 2026 already exposed in the prior Event Futures Discovery study. It is not independent OOS. Never open protected September 2026.
- Require HTTP 200, checksum basename equality, exact ZIP SHA256, one CSV entry, non-decreasing source event milliseconds and aggTrade IDs, valid schema, valid isBuyerMaker flag and >0 price/quantity.
- Require minimum 1,000 rows and 600 active minutes per asset; reject rather than filling missing minutes or substituting sources.
- Derive signed minute taker flow by price*quantity; isBuyerMaker=true is taker SELL, false is taker BUY. Source-only minute bins have no labels or predictions.
- Preserve raw ZIP SHA, URL, and derived compressed minute-bin SHA. Historical files can be revised and their publication is later than the event; not evidence of capture available at that instant.
- If any source fails, fail closed and do not open returns.

## Anti-duplication
Previous static L2 extreme imbalance, LVAC depletion, liquidation cascade LICP-001, PR170 absorption, Event Futures V0.3.1 and 18-cell April index-only baseline failed or remained insufficient in their exact scopes. This source gate tests a distinct continuous **aggressor execution flow input**, not a renamed resurrection of prior winners.
No signal direction, threshold, model, horizon or economic target is authorized in this phase. Only after SOURCE PASS may a distinct scientific freeze be designed, before opening index outcomes. All April results would remain Discovery; a new future untouched validation period is required.
No main merge, orders, account reads, private endpoints, wallets, fees, paid sources, September 2026 history, live trading or account mutation.
