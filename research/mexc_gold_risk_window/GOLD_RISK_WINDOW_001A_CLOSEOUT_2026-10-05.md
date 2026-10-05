# MEXC-GOLD-RISK-WINDOW-001A — HISTORICAL 1m CLOSEOUT

Date: 2026-10-05
Branch: `gold-risk-window-001a-chat-attack-2026-10-05`
Scope: research-only. No trading, no account reads, no private endpoints, no merge to main.

## Verdict

**NO_EDGE_1M_MAGNITUDE_SCREEN** for the pre-registered conservative taker implementation.

This does **not** prove that no sub-minute microstructure effect exists. It kills the historical 1-minute close-based taker version tested here.

## Evidence corpus

Two pre-announced MEXC leverage-restriction windows:
- CPI, 2026-09-11: 12:20–12:35 UTC, macro release 12:30 UTC.
- FOMC, 2026-09-16: 17:50–18:05 UTC, macro release 18:00 UTC.

Three MEXC contracts:
- XAU_USDT
- XAUT_USDT
- SILVER_USDT (displayed by MEXC as SILVER(XAG)USDT)

For each event/instrument:
- 121 one-minute Last candles
- 121 one-minute Index candles
- 121 one-minute Fair candles
- funding history around the event

Coverage: complete. No missing aligned frames.

## Frozen cost screen

Official MEXC API Futures fee announcement effective 2026-06-01 states:
- Maker: 0.06% = 6 bps per execution
- Taker: 0.08% = 8 bps per execution
- API fee schedule takes precedence over website/app promotions.

Primary frozen screen:
- single-leg taker round trip = 16 bps before spread/slippage/funding
- two-leg XAU/XAUT taker round trip = 32 bps before spread/slippage/funding

Note: the same MEXC announcement contains a stale/inconsistent example below the updated table mentioning the prior 0.04%/0.06% schedule. This study uses the explicit updated fee table conservatively. Any future live authority must verify the actual authenticated account fee schedule before execution.

Source:
https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742

## Main quantitative results

### Maximum aligned 1m close dislocation

Across XAU_USDT, XAUT_USDT and SILVER_USDT:
- max |Last - Index| = **12.5293657009 bps**
- single-leg taker round-trip fee floor = **16 bps**
- therefore even the largest observed aligned 1m close dislocation fails the fee floor before spread/slippage.

For primary gold contracts specifically:
- XAU_USDT max |Last - Index| = **11.0452856713 bps**
- XAUT_USDT max |Last - Index| = **11.2301717280 bps**

### XAU-XAUT relative-value rail

Maximum absolute XAU-XAUT basis deviation from the PRE-window median:
- **15.7055829088 bps**
- two-leg taker round-trip fee floor = **32 bps**

This is less than half the conservative two-leg fee floor, before spread/slippage and execution mismatch.

### Restoration-convergence hypothesis

Median absolute dislocation in the 5 minutes before restoration vs the first 10 minutes after restoration:

CPI 2026-09-11:
- XAU Last-Index: 5.0681 -> 5.5698 bps (**worsened 9.9%**)
- XAUT Last-Index: 5.3066 -> 3.4460 bps (**compressed 35.1%**)
- XAU-XAUT basis deviation: 10.9776 -> 7.3195 bps (**compressed 33.3%**)

FOMC 2026-09-16:
- XAU Last-Index: 2.9745 -> 5.1605 bps (**worsened 73.5%**)
- XAUT Last-Index: 5.0794 -> 5.2050 bps (**worsened 2.5%**)
- XAU-XAUT basis deviation: 3.4732 -> 2.7648 bps (**compressed 20.4%**)

Conclusion: restoration compression is not directionally robust at the single-contract Last-Index level. The XAU-XAUT basis compressed in both events, but the observed magnitude is far below the two-leg taker cost floor.

### SILVER control

SILVER_USDT also stayed below the 16 bps taker round-trip threshold:
- maximum |Last - Index| across the tested events = **12.5293657009 bps**

No control instrument showed a 1m close dislocation large enough to rescue the primary taker hypothesis.

### Funding

Funding history was non-zero around both events for XAU/XAUT/SILVER. It is therefore incorrect to model these contracts as structurally funding-free during the tested period.

Observed funding magnitudes were small relative to the conservative trading fee floor for these short windows, but funding must be included whenever a simulated hold crosses a settlement.

## Scientific interpretation

What survives:
- the MEXC risk-window mechanism is real and pre-announced;
- the leverage cut/restoration can change market microstructure;
- XAU-XAUT basis visibly widened during CPI and compressed after restoration.

What does not survive:
- a 1-minute close-based taker strategy trading Last-vs-Index/Fair convergence;
- a two-leg taker XAU-XAUT convergence strategy at the observed 1m magnitudes;
- the claim that restoration consistently compresses single-contract Last-Index dislocation.

## Important limitation

One-minute candles can miss transient sub-minute dislocations. They also cannot reproduce bid/ask queueing, depth, fill probability, latency, or adverse selection.

Therefore the correct conclusion is:

**Kill the 1m taker version. Do not label the entire microstructure family NO_EDGE.**

A separate sub-minute forward test would need contemporaneous:
- L1/L2 order book
- trades
- Index
- Fair
- Last
- exchange timestamp and local receive timestamp
- clock-drift monitoring

It should be opened only as a **new pre-registered experiment**, not as post-outcome tuning of 001A.

## Next scientific decision

Do not spend more historical 1m effort on this exact GOLD risk-window implementation.

Priority should move to a structurally different hypothesis. If GOLD is revisited, use a new forward-only microstructure protocol with fixed thresholds and no reuse/tuning of the 001A outcomes.

## Audit artifacts

Generated under:
`research/mexc_gold_risk_window/results/`

Key files:
- summary.json
- manifest.json
- window_metrics.csv
- basis_metrics.csv
- restoration_compression.csv
- funding_near_events.csv
- per-event aligned 1m CSVs
- raw API JSON responses
