# NVDA CASH→MEXC Event10M V0.1 — October 1–2 historical retrospective replay
Date 2026-10-29. PRE-OUTCOME FREEZE. No September holdout, no old NVDA October 05–30 sealed forward.

This replay is DISCOVERY ONLY on 2026-10-01 and 2026-10-02, dates previously exposed by the NVIDIA 1m source checks. It can neither validate nor tune the November paper forward, and MUST NOT alter source/model rules after opening outcomes.

## Frozen signal (identical to November V0.1 decision model, no edited thresholds)
NVIDIA_USDT only, cash stock NVDA public Yahoo 1-minute close vs MEXC standard perpetual INDEX 1-minute close. At each 10-minute interval t in NY-local 09:35,09:45,...11:25 (12/day, 24 fixed slots), use exactly the last two completed bar starts (t-4min and t-1min). Cash 3m signed return bps = 10000*(NVDA_close(t-1)/NVDA_close(t-4)-1). MEXC index 3m bps likewise.
A qualified paper forecast only when abs(cash_bps)>=10 AND abs(cash_bps-index_bps)>=5 AND cash_bps*(cash_bps-index_bps)>0. Side follows cash sign. Everything else ABSTAIN. Exactly 1 asset, 1 signal, 1 threshold pair, 1 horizon. No parameters selected after outcomes.

## Frozen diagnostic resolution (NOT exact MEXC Event Futures)
Decision hypothetical time t+10 seconds into interval, expiry hypothetical t+10m+10 seconds. Historical Yahoo candles have no actual time-of-receipt proof, and the MEXC standard INDEX 1-minute OPEN(t) and OPEN(t+10m) are *minute-boundary proxies* 10 seconds BEFORE the hypothetical decision/expiry; their equality to the actual Event Futures server-assigned openPrice/settlement is UNPROVEN. This is therefore a **retrospective minute-boundary index-price proxy diagnostic** only, not an executable Event Futures replay.
Outcome WIN if UP and OPEN(t+10)>OPEN(t) or DOWN and OPEN(t+10)<OPEN(t), LOSS opposite, TIE if equal. Unit EV +0.8/WIN, -1/LOSS, 0/TIE with fixed **hypothetical** symmetric q=0.80 (not historical actual payouts). Include q=0.85 ONLY as a supplementary sensitivity, never substitute it for the stated hypothesis; in Oct29 product 10m 0.80 was observed but this is NOT proven true at Oct1–2.

## Baselines, reporting and hard scientific interpretation
Record all 24 fixed slots and causes of abstentions, wins/losses/ties for qualified signals, per day, cash impulse sign, source bar and raw payload hashes.
Matched always-UP, always-DOWN and cash-only-direction baselines evaluated on exactly the SAME qualified slots. The cash-only direction on selected slots is by definition identical to candidate direction, hence cannot establish incremental effect of the lag filter; additionally report cash-only impulse abs>=10bps on ALL 24 slots (predeclared), with no source gaps imputed. Always-UP and always-DOWN also report all-slot context; do not promote these as strategies. No post-outcome trimming of session times, symbols, thresholds, proxies or day subsets.
Break even q.80 1/1.8=55.5556% non-tie; min prospective protocol 60 qualifying resolved signals / 15 distinct sessions cannot be met with only 24 historical decisions, so **certified economic edge impossible** regardless of result.
Require exact requested source date/asset, 1m aligned and positive finite opens/closes, no duplication and required minute coverage; if relevant source unavailable BLOCK outcomes. New V0.1 code is NOT called with an October date; historical replay simply applies the identical signed 3m feature formula + selection from source explicitly rather than bypassing its frozen November-only clock safety.
No account/private endpoints, orders, wallets, money, main merge or development using the Sept protected or NVIDIA Oct05–30 frozen validation.

## Source-only gate before any outcome evaluation
Public Yahoo query1.finance.yahoo.com/v8/finance/chart/NVDA exactly period1 2026-10-01 UTC, period2 2026-10-03 UTC, interval=1m, includePrePost=false. MEXC contract public INDEX Min1 NVIDIA_USDT exactly from 13:20 to 15:40 UTC for each date. Both US dates fall in EDT UTC-4 (09:35=13:35 UTC). Source stage checks expected timestamps and positive finite bars only; publishes raw response SHA256. Outcome runner can start only after this SOURCE gate passes and its immutable receipt has been inspected. No source fallback or date/asset substitution.
