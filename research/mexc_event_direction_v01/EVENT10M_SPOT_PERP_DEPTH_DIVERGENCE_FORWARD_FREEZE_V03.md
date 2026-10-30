# BTC/ETH Event Futures 10m — SPOT vs PERP DEPTH DIVERGENCE V0.3
FROZEN 30 Oct 2026. Source-only evidence precedes this freeze; **ZERO future market 10m outcomes opened for this rule**. New economic mechanism, not cash-stock lag, 1m futures ROC, news, or directions always UP/DOWN.

## Causal economic hypothesis
Persistent visible buy-side (or sell-side) order-book notional pressure at OKX SPOT vs opposite visible pressure at MEXC PERPETUAL FUTURES could predate the direction of the MEXC INDEX in the next 10min. This is falsifiable: orderbook depth can spoof/cancel, spot and perp need not lead-lag, source receipts can lag, and Event Futures exact server-assigned entry/settlement may differ from the public MEXC perp index. There is NO profitability claim.

## Frozen conditions (exactly one family, 2 assets)
BTC_USDT and ETH_USDT only, regardless of liquidity, on UTC aligned 10-minute slots beginning 2026-11-01 00:00 UTC through 2026-11-30 23:59 UTC. Decision when slot clock seconds 20–40 inclusive; no late decisions. Three separate pairs of public 5-level NOTIONAL weighted book imbalance snapshots, with between-receipt start gaps 4–8 seconds, spanning 8–16seconds, all received BEFORE decision, all last observations <=2sec old:
- OKX SPOT BTC-USDT or ETH-USDT from GET /api/v5/market/books: server market timestamp within 2sec of local receipt. Independent from MEXC.
- MEXC FUTURES BTC_USDT or ETH_USDT from GET /api/v1/contract/depth, local receipt recorded, valid top5, no as-of depth server timestamp guarantee.
- Each of **three** spot top5 signed imbalance >=+0.25 for UP, <=-0.25 for DOWN.
- Each of **three** MEXC futures top5 imbalance of OPPOSITE SIGN with magnitude >=0.25.
- If any single snapshot fails or does not meet all conditions -> ABSTAIN (not another strategy variant).
- Eligible Event Futures exact same contract 10m ONLINE, payout per chosen side >0 captured <=10sec before decision. Index price at decision must be a recent MEXC public standard futures index tick <=2seconds old, raw sha256 and server clock validated. Still not verified identical to exact Event Futures server price.
- No other market data, hindsight filters, adapted thresholds, candle indicators or conditional models.
- Forecast direction = sign persistent OKX SPOT imbalance. Target = exact decision_ts + 600000 ms. The code returns only SHADOW_FORECAST_NOT_EVENT_EXECUTION.

## Analysis gates
Collect every eligible slot, including failures, and pin decision artifact before outcome to independent GitHub Action artifact+server hash, never retroactively manufacture. Record dynamic exact qUP/qDOWN; WIN unit payoff +q vs LOSS -1 and tie as MEXC rules, but only IF the Event Futures exact server price parity is independently certified; otherwise merely SHADOW_INDEX_WIN vs LOSS, not monetary EV.
Prospective minimum >=300 resolved non-tie forecast observations and >=20 distinct calendar days (minimum not significance guarantee), chronological final-third untouched holdout, daily block bootstrap lower 95% confidence bound on mean real payout >0, proper multiple comparisons with other variants, and robust against cancellation/latency; no parameter selection after seeing outcomes. If fewer samples by cutoff, status INSUFFICIENT_FORWARD_DATA rather than cherry-pick a shortened sample.
No automated collector scheduled or default branch merge by this freeze. Existing Github Actions workflows on branch only, not live source-runner. Public source gate pass from Oct30 is merely source readiness; historical Sep protected and old NVIDIA Oct05–30 forward untouched. No accounts, keys, orders, funds, live or API trading, default branch merge.
