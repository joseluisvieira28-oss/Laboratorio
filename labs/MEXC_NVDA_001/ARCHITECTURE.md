# NVDA architecture freeze — 2026-10-05

Base: fetched GitHub main f263c6c6f3a57f26666a7aee28e782f2cbd08418. Public GET only. No account or exchange mutations.

## Official chronology and evidence limits

- 2025-07-21 launch announcement: USDT perpetual exposure, US cash market hours, 5x maximum and temporary zero funding/trading fees. https://www.mexc.com/announcements/article/new-feature-mexc-to-launch-stock-futures-enjoy-0-fees-for-a-limited-time-in-the-u-s-stock-market-17827791526192
- 2025-12-11 MEXC guide describes Ondo tokenized-stock index anchoring, 24/5 hours, isolated margin and early settlement for corporate actions. This is dated product evidence, not proof of today's component weights or an exact migration date. https://blog.mexc.com/crypto-knowledge/how-to-buy-stock-futures-with-usdt-on-mexc/
- 2026-03-06 NVDA/MRVL upgrade: 24/7, cross and isolated margin, maximum 100x; circuit-breaker and corporate-action exceptions. https://www.mexc.com/announcements/article/stock-futures-upgrade-17827791534091
- 2026-06-03 08:20 UTC: NVDA 100x to 50x. https://www.mexc.com/en-GB/announcements/article/maximum-leverage-adjusted-for-muusdt-and-nvdausdt-futures-jun-3-2026-08-17827791535906
- 2026-06-04 05:35 UTC: NVDA 50x to 100x. https://www.mexc.com/announcements/article/mexc-increases-maximum-leverage-for-mu-sp500-and-8-other-futures-pairs-jun-4-2026-05-17827791535931
- 2026-06-04 04:10 UTC: funding to eight-hour settlement, cap +/-3%, first listed settlement 16:00 UTC. https://www.mexc.com/zh-TW/announcements/article/adjustment-to-nvdausdt-funding-rate-settlement-frequency-jun-4-2026-04-17827791535933
- Current public contract/detail: NVIDIA_USDT / display NVDA, USDT settlement, size 0.01, tick 0.01, integer lots, minimum one lot, maximum 200x subject to risk tiers. indexOrigin=[BINANCE_FUTURE,BITGET_FUTURE,BINANCETICKER,PYTH,KAIKO]. Save full snapshot, not just selected fields. Source labels do not establish actual active weights or instrument mapping. NVD and NVDL are leveraged ETFs, NOT interchangeable NVDA rails.

## Methodology and cost boundary

General MEXC FAQ describes a weighted index with stale-source exclusion and deviation protection; fair is median of funding-premium, mid-price-basis fair and Last. This general description does not resolve NVDA-specific weights, fallback rules, historical migrations or publication latency. https://www.mexc.co/support/article/faq-on-index-price-fair-price-and-last-price-7950960183961

API fee announcement effective 2026-06-01 08:00 UTC specifies maker 0.06%, taker 0.08%, overriding app/web promotions. The illustrative paragraph retains old rates; the dated before/after table is authoritative for this study. No later fee change has been confirmed in this review. Snapshot zero rates are not used as API fees. Primary fee floor 16 bps round trip; maker 12 bps diagnostic only. https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742

Ondo confirms NVDAon total-return exposure including reinvested dividends; raw token/share level equality is not assumed. Current mint/redemption availability must not be backdated. https://ondo.finance/ondo-stocks and https://app.ondo.finance/assets/nvdaon

Unresolved: exact NVDA index constituent instruments/weights through time; Ondo-to-current transition; historical full trading-status/corporate-action ledger. Historical OHLC observations cannot resolve these facts. Earliest creationTime is metadata, not guaranteed first tradable bar.

Public API market docs: https://www.mexc.com/api-docs/futures/market-endpoints . Klines have maximum 2000 points; segmented daily requests avoid truncation. Recent trades (max100) and last-N depth lack arbitrary historical time access. Full historical L2/ticks cannot be reconstructed from those routes.
