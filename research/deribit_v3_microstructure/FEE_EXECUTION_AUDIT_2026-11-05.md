# Fee and execution audit — 2026-11-05

Official references:
- https://support.deribit.com/hc/en-us/articles/25944746248989-Fees (page updated 2026-08-05)
- https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options (page updated 2026-06-12)

## Confirmed rules
- BTC_USDC linear options: trading fee MIN(0.0003 * index_price, 0.125 * option_price) * contracts * contract_size; BTC contract_size = 1. Verify account-specific discounts and any temporary promotions separately.
- **IMPORTANT CORRECTION:** option combo fee discounts require at least one BUY and one SELL leg. A long call + long put straddle has TWO BUY legs; it does **NOT** qualify for the published option combo fee discount. A combo quote may still reduce execution/legging risk, but no fee reduction can be assumed.
- The fee table lists BTC/ETH Daily Options at 0% delivery fee AND USDC Linear Options at 0.015% (capped at 12.5% of option value). The two category labels overlap for a BTC_USDC daily option. Do NOT assume either rate resolves the overlap.
- The linear USDC product guide explicitly says ITM linear options incur the usual delivery fee upon conversion into an expiring future, and the resulting futures position incurs no second delivery fee. Settlement uses a 30-minute index TWAP leading into expiry.
- Do not double-count an option delivery fee plus the futures settlement fee; do not assume fee=0 until product-specific classification is independently confirmed.
- Maker limit order is not necessarily maker unless post-only is enabled; posting does not prove a fill.

## Required before PnL or live decisions
Obtain an authoritative, date-effective fee classification for **BTC_USDC daily** (not generic BTC options), ideally from Deribit product support / product-specific documentation. Retain dated source and quote. Until then record delivery_fee_status=UNVERIFIED and net_pnl=null; optionally present 0% and 0.015% as **scenarios only**, not settled facts.

## Current execution status
The offline comparator and unit tests have been committed but no local Python execution has been observed in this chat. Historical source replay is diagnostic, not V3 forward evidence. No collector has been activated; V3 valid sessions remain 0/20.
