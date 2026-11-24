# BACKES-DIAMANTE-004B — Kraken source recovery (2026-11-24)
**SOURCE_PASS for a strictly limited 2025–2026 execution-price replication. ECONOMIC NO-GO.**

## Scope and verified evidence
- BACKES-004B separate draft PR #391: https://github.com/joseluisvieira28-oss/Laboratorio/pull/391
- GitHub Actions SUCCESS: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45338605927
- Immutable artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45338605927/artifacts/14895131290
- ZIP SHA256 verified: 76dc3ceae04f8150496bc03eaa5d10cbae79687789f58dffc783c7c7a3862a75
- 2/2 offline lag, switching and fee-drag checks PASS, acquisition/replay success.
- Kraken direct traded spot pairs XBTUSD, ETHUSD, ETHXBT, interval=1440 minutes via 3 *public* REST GET calls; 686 consecutive daily candles per pair aggregated UTC Monday–Sunday into **98 weeks 2025-01-06..2026-11-22**.
- 384 Binance official public source ZIPs independently re-read, same frozen BTC/ETH allocation derived from the full Binance ETHBTC history and unchanged FROZEN002 original rule; source URLs and SHA256 per receipt in artifact RESULT.json.
- Relative traded ETHBTC closing quotes: median Kraken/Binance absolute price divergence 0.03564%, maximum 0.26479% across comparable weekly closes.
- The signal originates from **Binance** and is identical on both execution-price series. This is **NOT independent Kraken signal replication**, not 2018–26 Kraken original strategy verification and not any influencer's private track record. USD vs USDT numeraires differ.

## Modelled spot returns 2025–2026 with identical source-frozen positions
| Hypothetical costs / traded fraction | Kraken USD ROT | Binance USDT ROT | Kraken BTC hold | Binance BTC hold |
|---:|---:|---:|---:|---:|
| 10bps | -4.15152% | -4.01065% | -37.83824% | -37.77190% |
| 35bps | -4.86930% | -4.72949% | -37.99380% | -37.92762% |
| 60bps | -5.58350% | -5.44473% | -38.14936% | -38.08335% |
| 80bps | -6.15227% | -6.01434% | -38.27380% | -38.20793% |
| 100bps | -6.71875% | -6.58166% | -38.39825% | -38.33251% |

- At 10bps, maximum drawdown Kraken rotation -52.05%, Binance rotation -51.97%.
- At 80bps, maximum drawdown Kraken rotation -52.38%, Binance rotation -52.31%.
- The fixed BTC position has a max drawdown -51.85% on Kraken. Rotation did NOT materially reduce maximum drawdown despite recent better terminal NAV.
- These are all retrospectively computed next-Monday-open fills, not records of accessible orderbook depth or actual fills.
- As of 2026-11-24, the published Kraken Pro starter taker fee is 80bps before spread/slippage; official reference https://www.kraken.com/pro/fees, but historic 2025 actual account tier/fees have not been established.

## Scientific verdict
**Kraken price source is independently consistent with Binance for the 98-week period**, with the same frozen Binance signal producing very similar outcomes. This reduces concern of a Binance-only price artifact in 2025–26 but adds **no evidence of independent predictive edge**.
No actual trades, API keys, account access, subscriptions, margin, purchases, transfers, production releases or changes to the frozen predecessor. Never claim this report is a prospective out-of-sample win.

**NO-GO economic/live;** further work limited to properly frozen future shadow data and realistic account fees.
