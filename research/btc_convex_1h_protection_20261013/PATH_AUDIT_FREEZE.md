# BTC-CONVEX 1H — EXIT GIVEBACK PATH FORENSICS FREEZE
**2026-10-13 UTC. Research-only, descriptive known 2021–25 outcomes.**
This contract is frozen before computing the path-level forensics, and intentionally does not propose or test new thresholds on seen BTC data.

## Immutable reference, no signal/exit alteration
Re-use solely the 77 1h BASE and 78 1h STRESS CLOSED ledger observations from completed run 38426153613 / artifact 11828479302, cross-check price and timestamps exactly.
Reacquire the same official public Binance USD-M BTCUSDT 5m calendar months 2021-01 through 2025-12 inclusive, verify official monthly .CHECKSUM and **exact SHA256 parity** against V02 existing archived market source manifest. Any missing month, mismatch, noncontiguous 5m bars or trade-exit non-reconciliation -> SOURCE_BLOCKED, no partial promotion. Never use 2026 or independent protected holdout.

## Intratrade measurements, all predefined
On each ORIGINAL 1h trade:
- reconstruct actual V02 5m stop chronology (entry at recorded slip-adjusted proxy, initial stop -4%; after each completed 1h close profit >=+5% activate original nonlatched 12%-from-running-high trailing, otherwise revert to initial stop).
- Check first hit of active stop exactly matches recorded exit timestamp and proxy exit price (BASE slip 2bps, STRESS 5bps); failure -> CODE_OR_SOURCE_DIVERGENCE_BLOCKED.
- before exit 5m bar (to avoid inventing OHLC high-vs-stop ordering) track verified prior 5m high, peak runup percent from recorded entry, maximal completed 1h close profit; compute peak-to-exit giveback IN PERCENTAGE POINTS (not money captured under an alternate policy). Track total activation counts, **activation that actually raised protective stop above initial**, falling below activation threshold, stop weakening/reset counts, whether any trade with positive peak ended losing money, duration. Include open final position as UNKNOWN/excluded, not fictional closed result.
- report metrics overall, winning trades and losing trades separately, per exit year, and top3 original winning trades from F1 fee/funding ledger for concentrated-tail patterns.
- No after-the-fact parameter choice/exit simulation, no alternative stop comparison, no live execution edge; 5m OHLC high can overstate realizable MFE, bid/ask and 1m ordering remain absent.

## Clean hypotheses for future, not selected based on outcome
If the original nonlatched trailing appears vulnerable, compare against the **existing prior H1 sticky-trail** scientific closeout before contemplating any fresh child. No duplicate H1 promotion. If no verified superior new hypothesis exists, keep original Parent unchanged and funding/source validation as priority.
No trade, private API, wallets, account, expenditure, main merge, Render, or 2026 holdout.
