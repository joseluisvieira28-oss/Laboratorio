# BTC 10M HISTORICAL SPOT/PERP EXECUTED TAKER FLOW — FINAL ECONOMIC CLOSEOUT, 2026-10-31

**FINAL: OFFICIAL BINANCE ARCHIVE SOURCE PASS; INDEPENDENT 2025 SOURCE-TO-LABEL REPLAY PASS; PRIMARY FLOW55 NO EDGE; STRICT FLOW60 NO EDGE; NO MEXC EVENT-FUTURES ECONOMIC GO.**

## Actual test vs original proposed 10m hypothesis
This is deliberately NOT a historical backtest of the frozen future OKX Spot/MEXC perp 3-snapshot TOP5 ORDERBOOK rule. The official Binance archives supply 1-minute executed taker-buy quote amounts and spot/perp prices, NOT order book depth and NOT historical MEXC Event Futures accepted open/settlement price/payout. Original Nov 2026 OKX/MEXC L2 model remains separate and scientifically unvalidated.

Pre-source scientific frozen commit 6dc39f6d46aa7401221ed6bff36203dafe0a1ba2; read-only historical GitHub Actions run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41232569305 completed successfully with exactly 24 official Binance BTCUSDT 1m monthly ZIP archives, 24 original CHECKSUM files, 24 valid SHA256 verifications, fixed 2024+2025 January/March/May/July/September/November on spot AND Binance USDT-M Futures. Original raw archives and all generated event/label JSONL preserved in artifact **13054236463**, artifact ZIP SHA256 **21139cdc53117aba957d6fa820ede0f875daf9a4b06a467c298d3163137427aa**, byte size 48,851,585.

A first run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41232464971 failed BEFORE any downloads due a missing synthetic-only always-up comparison field; repaired in code commit d2c316fa8d099f51acb7269b21bdc48a34ca4e9f with original date/rules unchanged and documented as synthetic errata. The successful run was therefore the first to open historical outcomes.

**Independent audit after results**: offline verification https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41232784116 independently decoded all 12 original 2025 monthly Binance source ZIPs, upstream SHA256 checksums, exact spot/perp 3-minute trade-buy shares, all original 10-minute UTC times/price labels/directions and hypothetical payoff math. No new market data requests. Verdict INDEPENDENT_ORIGINAL_SOURCE_REPLAY_PASS; audit artifact 13054670959 SHA256 9783b67d5c788864d1ff9e3ed061216dd10f1b8c468702148b9025333265bfa0.

## Original, unchanged model
For every UTC 10-minute boundary t, 3 fully CLOSED 1-minute spot and perpetual candles at t-3m, t-2m, t-1m determine venue aggressive taker buy ratio = SUM(taker_buy_quote)/SUM(quote_volume). H1 FLOW55 UP iff spot >=0.55 and perp <=0.45, DOWN inverse; else ABSTAIN. H2 FLOW60 strict UP spot >=0.60 and perp <=0.40, DOWN inverse; else ABSTAIN. Target is Binance SPOT 1-minute candle OPEN at t+600s versus OPEN at t; non-overlapping aligned 10m windows. An exact equality is TIE, assigned 0 illustrative payout (not MEXC actual settlement). Spot open at t assumes ideal instantaneous execution, not manual realizability.

## 2024 fixed historical development
H1 FLOW55: 2,467 signals, 1,224 wins, 1,241 losses, 2 ties; NON-TIE accuracy 49.655%; 184 days, q0.70 mean hypothetical payoff **-0.155736** stake units.
H2 FLOW60: 686 signals, 335 wins, 351 losses, 0 ties; 48.834% accuracy; 169 days, q0.70 mean payoff **-0.169825** stake units.

## 2025 fixed independent chronological OOS
Source samples: 26,483 eligible 10-minute slots across six 2025 months.
| Metric | FLOW55 PRIMARY | FLOW60 STRICT |
|---|---:|---:|
| Total signals | 3,385 | 1,247 |
| Correct / Wrong / Tie | 1,668 / 1,716 / 1 | 626 / 621 / 0 |
| Non-tie directional accuracy | **49.290780%** | **50.200481%** |
| Signal coverage among all slots | 12.7818% | 4.7087% |
| Distinct days with qualified signals | 184 | 183 |
| Mean signed 10m spot return | -0.0780 bps | +0.3182 bps |
| Hypothetical payout per stake, q=0.70 | **-0.16200886** | **-0.14659182** |
| Hypothetical payout per stake, q=0.80 | **-0.11273264** | **-0.09639134** |
| 97.5% DAILY BLOCK bootstrap lower bound for q=0.70 | -0.189528 | -0.195024 |
| Profitable months at synthetic q0.70 | **0 of 6** | **0 of 6** |

Hypothetical stake of 10 USDT per signal at CONSTANT q70 (never actual MEXC realized result): FLOW55 1,668*7 -1,716*10 +1*0 = **-5,484 USDT** across 3,385 independently reconstructed directional signals. FLOW60 626*7 -621*10 = **-1,828 USDT** across 1,247 signals. At constant q80 corresponding loss scenarios **-3,816** and **-1,202 USDT**. This does not establish that any user actually lost money; no orders or accounts were accessed.

The q=0.70 mathematical win threshold without ties/extra costs is >58.8235%; q0.80 threshold >55.5556%. Both actual 2025 source-proxy 49-50% hit rates fail by wide margins. Every 2025 month negative at q70 for BOTH schemes. No independent positive net edge, no cost or order-latency assumption could turn this synthetic q70 outcome into profitable trading.

## Methodology caveats and auditable criticism
- The original frozen spot-only SAME-SLOT baseline happens to give precisely the same direction as the cross-market H1 signal WHEN it qualifies: both follow the spot ratio. The equality of those two same-slot results is tautological; it is not an independent assessment of information added by the futures condition. This does not weaken the directly negative 2025 observed accuracy/payout result.
- 2025 is chronological OOS **for this pre-registered new hypothesis**; older Crypto Lab research had opened other unrelated historical outcomes, so do not claim a universal pristine 2025 lab-level holdout.
- The payout rates 70% and 80% are **scenario constants** and were NEVER historically measured for MEXC Event Futures. Binance spot open-to-open label cannot certify actual MEXC Event Futures payout settlement parity. BTC event product can change payouts dynamically; even fee-free manual submission would still lose under the scenario if accuracy stays at 49%.
- Statistical signals are not independent IID, hence day-block resampling; even a positive mean signed bps in the stricter branch is not a valid binomial winning edge at q70.
- Neither of the two H1/H2 thresholds may be retuned on already opened 2025 historical outcomes while claiming fresh OOS.

## Binding final decision
**STOP this historical aggressive trade-flow cross-market divergence as a BTC 10m manual trading/signal candidate**: sound original public data, sufficient n and days, independently verified negative out-of-sample q0.70 payoff and no robust directional hit-rate lift. Do not conduct threshold or month cherry-picking to rescue it. Preserve unchanged frozen Nov 2026 OKX/MEXC book test; the original L2 candidate remains distinct and not independently economically proven. No main merge, no live order, no user balance, no wallet or paid market source, no 2026 holdout opened.

**NEXT scientific path, if the operator still wants to examine the original L2 hypothesis historically, requires authentic historical OKX spot and MEXC Futures top5 book snapshots with subsecond time/cost provenance. The Binance candle archive cannot manufacture that missing L2 history.**
