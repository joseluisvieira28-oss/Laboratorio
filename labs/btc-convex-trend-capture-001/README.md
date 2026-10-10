# BTC-CONVEX-TREND-CAPTURE-001

**Opened:** 2026-09-23  
**Status:** RETROSPECTIVE_SEED_ONLY / EDGE_UNPROVEN / SOURCE_CODE_MISSING  
**Mode:** research-only, fail-closed  
**Live trading:** FORBIDDEN  
**Main merge:** NOT AUTHORIZED

## Objective

Determine whether the user-supplied TradingView strategy `Quant Trailing v5 (Payoff Invertido)` contains a reproducible economic mechanism that can survive independent validation.

The seed exports cover BTCUSDT perpetual on inferred 5m, 15m and 4h resolutions. They are retrospective evidence and have already been inspected. They may describe the seed mechanism but may not be used to tune a new rule and then count that same history as independent validation.

## Seed findings frozen at lab open

- Direction: long-only in all supplied trades.
- Position allocation: ~94.9% of account equity per trade.
- Normal losing exit: price stop is almost exactly -4.000%.
- Normal winning exit: price exits cluster almost exactly ~12% below the maximum favorable price, strongly indicating a ~12% trailing stop.
- The trailing activation rule is not identified from the export alone.
- Entry rule is unknown because Pine/source code was not supplied and no matching source exists in the repository.
- 5m and 15m monthly PnL are highly redundant (correlation ~0.87); they are not independent confirmations.
- All three closed backtests become net negative when their single best historical winner is removed.
- 2025-2026 closed-trade performance deteriorates materially on 5m and 15m.
- Large fractions of eventual losers first reached positive MFE, making profit-protection scientifically interesting, but any thresholds inferred now are contaminated on this BTC history.

## Current classification

**MECHANISM_PRESENT / EDGE_UNPROVEN / NO PROMOTION CREDIT**

The exports are sufficient to justify a laboratory. They are not sufficient to justify execution, Tier promotion, or a claim of edge.

## Workstreams

1. **ENTRY-SIGNAL RECONSTRUCTION**
   - recover exact Pine/source/configuration;
   - prove non-repainting / no lookahead;
   - reproduce entry timestamps and fills.

2. **REGIME ROBUSTNESS**
   - no post-hoc BTC regime filter receives scientific credit;
   - any new regime rule must be frozen before testing on untouched evidence (cross-asset or prospective).

3. **EXIT / PROFIT-PROTECTION**
   - preserve original ~4% hard stop and inferred ~12% trailing as seed facts;
   - identify the exact trailing activation rule;
   - new BE/profit-lock thresholds are new hypotheses and require untouched evidence.

4. **RISK NORMALIZATION**
   - separate signal quality from the original ~95% allocation;
   - sizing experiments are risk engineering, not proof of edge.

## Required blocker removal

The most important missing artifact is the exact Pine Script or equivalent source/configuration that generated the exports. Until it is recovered, ENTRY-SIGNAL validation remains blocked.

No live trading, exchange mutation, paid data purchase, post-outcome rescue, or merge to main is authorized by this lab.
