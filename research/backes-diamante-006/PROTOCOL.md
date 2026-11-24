# BACKES-DIAMANTE-006 — Prospectivo shadow, dupla fonte, sem trading
**Congelamento PRE-FIRST-FUTURE:** 2026-11-24. O estudo histórico BACKES-005, PR #392, tem 0/6 candidatos para trading. Manter ECONOMIC NO-GO LIVE.

## Identidade e candidatos
- Duas estratégias do laboratório, **NÃO do método privado de Augusto Backes**: ROT_TREND40_VOL20 e MOM8_TREND40_VOL20. Parâmetros fixos: 40 fechos BTC, 12 retornos log semanais, 20% alvo vol anual, piso vol 10%, exposição máxima 100%, sem alavancagem.
- Referências congeladas: CASH (0% juros, sem depeg/custódia modelados), BTC buy-and-hold, BTC_TREND40, HALF_ROT e FROZEN002. Não selecionar em função dos primeiros resultados.
- Todas as datas antes da primeira observação futura são retrospectivas. Primeiro Monday elegível: **2026-11-30 00:00–06:00 UTC**. Uma execução em 24 Nov só pode ser PRE-FLIGHT tardia para Monday 23 Nov; não é amostra de rentabilidade futura.

## Sources and non-negotiable hashes
- BACKES004 archived run #45337852543 (artifact name backes-004-independent-venue-audit-45337852543), archive ZIP SHA256 73a3e5349930d8b8d8dab46fa69fb8989a118c79cb7f6f7a59260b2f50641d7b.
- WEEKLY_DATA.json SHA256 4e256e2f0d4359943f96e9b1eb87e7cfe8cd6d6ca07728db7d5aa2dd4800d828 ; ECONOMIC.json SHA256 aa7305b470b3e4623965216608ef80c932682ac072b254c75b1200771454beb2. Two original venues have 464 complete Monday–Sunday UTC weeks from 2018-01-01 through 2026-11-22.
- Binance: official public market-data-only https://data-api.binance.vision/api/v3/klines 1d for BTCUSDT ETHUSDT ETHBTC; bookTicker best bid/ask for each. No API key.
- Coinbase Exchange: public https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400 (ETH-USD, ETH-BTC similarly) and /book?level=1 public best bid/ask.
- Append ONLY newly completed daily candles from 2026-11-23 through the previous Sunday UTC; require every day, positive OHLC, exact UTC midnight, no duplicate, and direct traded ETHBTC markets. Aggregate 7 daily candles exactly to each Monday–Sunday. No proxies, imputation, partial or future candles. SHA256 every raw HTTP response and save UTC request start/end and URL. Cross-rate sanity and historical source integrity required separately per venue.
- Binance USDT and Coinbase USD are distinct numeraires; never pool absolute returns without identifying currency basis. If one venue fails, mark venue SOURCE_BLOCKED and entire dual-venue economic week invalid; do not reconstruct later using outcomes.

## FROZEN SIGNAL and defence formula
- At Monday t only use prices from completed Sunday t-1. FROZEN002 uses the unchanged 3-week left/3-week right confirmed ETHBTC swing lows and 4-week ETHBTC relative momentum (as in source), and MOM8 uses latest ETHBTC close > close 8 weeks earlier.
- BTC_TREND40: latest fully completed BTC weekly close > SMA of last 40 completed BTC close values.
- VOL12(symbol): sample standard deviation of 12 log changes between consecutively completed weekly closes of the *selected* BTC or ETH asset, annualized sqrt(52).
- If no trend, weight BTC=0 ETH=0 CASH=1. If trend, risky weight = min(1, 0.20/max(VOL12,0.10)) in selected BTC or ETH, rest CASH. If insufficient history, CASH. No other settings, leverage, stops or re-optimization.
- Freeze signals/weights into a JSON object timestamped BEFORE reading public books. Then read current book snapshots and store their separate timestamps, top bid/ask and quantities. Never call those post-decision quotes Monday open fills, never claim real execution without depth/fill.
- Record scenarios for costs 10/35/60/80/100bps and one vs two route legs; actual account fees are NOT known. Avoid double-counting observed spread. Portfolio value and realized PnL only computed from future separately verified observations. No profits, performance claims or DD from the preflight.

## Scheduling and gates
- Preflight (24 Nov): must be marked LATE_PREFLIGHT_ONLY and EXCLUDED from prospective economics; successful data retrieval is TECH PASS only.
- Prospective run accepted only on Monday UTC matching provided YYYY-MM-DD >= 2026-11-30, between 00:00 and 06:00 UTC; otherwise TIMING_BLOCKED with auditable failure report. Entry is at observed post-decision quotes, not fictional 00:00 open.
- Weekly source-and-signal GitHub Actions artifact is immutable. Before 8 consecutive future weeks: just coverage stats. At 8 valid weekly observations, conduct diagnostic review. At 26 valid weeks, evaluate net returns vs frozen benchmarks with fees/spread, DD and uncertainty. 26 weeks may still be insufficient for proof of edge.
- GitHub workflows on a DRAFT branch with schedule: triggers are NOT automatically run by GitHub cron unless the workflow is on the default branch. Do not merge just for scheduling. If no available external automation slot, this is prepared but not auto-scheduled.
- All research-only, no user trading credentials, API key, real orders, spending, subscriptions, trades, transfers, margins, deployment or production merges.

## Veredito
SOURCE/TECH PASS is not an economic GO. Until genuinely unseen future multi-venue net evidence, economic verdict remains NO-GO for real capital.
