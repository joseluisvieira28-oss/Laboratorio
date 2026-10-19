# CRYPTO LAB — V06 EXIT L2 HISTORICAL BID / STOP-INTRABAR ADVERSARIAL VERDICT
Date: **19 October 2026**, two privately user-uploaded official OKX 400-level books. Source/risk method preregistered on this research-only branch BEFORE reading exit-bar books: `research/convex_okx_l2_v06/PRE_UPLOADED_EXIT_BID_BAR_RECONSTRUCTION_FREEZE_2026_10_19.md` (commit `439ac968`).

## Provenance, model semantics and fail-closed scope

Original immutable 2023–25 Binance V5 trade ledger from original run 38432883246, EXACT paper stop thresholds fetched without market changes from [original model source gate 39211274256](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39211274256): SOL 19.647448704 USDT and BNB 239.72960000000002 USDT. The original `STOP_INTRABAR` exit reason means **original 5m candle LOW touched stop**, and the simulator models raw-stop exit at `stop*(1-0.0002)`, with ledger timestamp at **5m bar END** (not broker trigger/fill).

- **SOL exit source:** `SOL-USDT-SWAP-L2orderbook-400lv-2023-06-05.tar.gz` user-provided privately, local SHA256 begins `57cbb8425c128e024262d1ff` (NOT supplier-signed).
- **BNB exit source:** `BNB-USDT-SWAP-L2orderbook-400lv-2023-11-21.tar.gz` user-provided privately, local SHA256 begins `e94bfbe6292ebf6808676138` (NOT supplier-signed).
- No raw book data, archive or provider download URLs were committed/pushed. The full locally derived, private source receipt includes six original five-minute checkpoints and SHA256 hashes. The human operator owns original archive files. No account / trade orders / capital / 2026 holdout.

Historical private local source reader processes EVERY update from day-start to the specific original stop bar end, with no future source book event applied:
- SOL: 2,238,201 total records read including the first future event, **29,942** book updates inside frozen 16:00–16:05 UTC; recent updates at each sampling checkpoint **6–7ms old**. Max inter-event gap into stop bar **30ms**.
- BNB: 2,040,780 total records read including first future, **27,766** updates inside frozen 17:40–17:45 UTC; recent checkpoint updates **4–5ms old**. Max inter-event gap into stop bar **160ms**.
- Six fixed checkpoint historical snapshots for each original 5m bar passed source freshness and observed **400 bid + 400 ask levels**. Actual historic `.data` source lacks `seqId/prevSeqId`, so update continuity/losslessness remains UNPROVEN. Chronological nearest-past source observation is not a real trading fill.

## Exact critical intrabar event findings

| Source field | SOL 1h (stop-bar June 5) | BNB 4h (stop-bar Nov 21) |
|---|---:|---:|
| Original Binance V5 paper stop (NOT OKX native stop) | **19.647448704** | **239.7296** |
| Original stop 5m bar UTC | 16:00:00–16:05:00 | 17:40:00–17:45:00 |
| First observed OKX **best BID <= Binance paper stop** INSIDE this bar | **16:02:06.963 UTC** | **17:44:17.735 UTC** |
| First crossing observed best bid | **19.625** | **239.7** |
| Full paper size hypothetical SELL BID VWAP at that instant | **19.62412405525** | **239.63377729878** |
| Static adverse multi-level SELL walk vs best BID | **0.4464 bps**, 2 bid levels | **2.7635 bps**, 2 bid levels |
| Entire provisional full-size qty visible in 400-level bid book? | **YES at first cross** | **YES at first cross** |
| Min best BID at ANY point in this five-minute bar | **19.24** | **238.6** |
| Max best BID in same bar | 20.104 | 250.3 |
| Best BID 1ms before recorded candle close | **19.3** | **240.1** |

**SIX frozen nearest-past exact reference BID snapshots**, all timestamp-age <=7ms:

| UTC minute inside original stop bar | SOL OKX best bid | BNB OKX best bid |
|---|---:|---:|
| T0+0:00 | 19.917 | 249.2 |
| T0+1:00 | 19.955 | 249.6 |
| T0+2:00 | 19.751 | 245.7 |
| T0+3:00 | 19.462 | 243.3 |
| T0+4:00 | 19.4 | 240.3 |
| T0+4:59.999 | 19.3 | 240.1 |

**Most important substantive falsification:** The original Binance stop bar CLOSE timestamp is NOT when the stop threshold first crosses in source OKX book. For BNB, the best bid dropped to 238.6 **inside** the bar and rebounded to 240.1 at the final millisecond, now above the original paper stop 239.7296. Thus an exit simulated at the 5-minute candle close would miss the path/depth/threshold. For SOL, the book dropped well below 19.647 threshold. Neither observation guarantees a broker-native order stop fill, slip, mark-price last-price trigger or remote latency response.

## Contract specs and new point-in-time governance blocker

The original OKX official public announcements: SOL perp launch Jan 2021 with **1 SOL/contract**; BNB perp launch Dec 2022 with **0.01 BNB/contract**. These are historical **launch-era** face values and not independently revalidated for precise 2023 stop times. Official OKX [tick-size adjustment notice November 4, 2023](https://www.okx.com/it/help/okx-to-adjust-tick-size-of-spots-margins-and-perpetual-swaps-2023-11-04) states BNB/USDT perp tick increased **0.01 -> 0.1 on November 10, 2023**, during the modeled BNB holding period (Nov 1–21); SOL/USDT perp tick adjusted separately that day, after the May/June SOL observations. The original BNB raw paper stop **239.7296** is NOT aligned to a **0.1 price tick** at the documented November 21 exit date. Actual broker stop trigger price semantics and accepted tick rounding were NOT tested. NEVER promote code that naively submits paper stop level exactly.

## What still makes this NOT a money machine

- Only two matched original entry+exit-date book series, original signal strategy built on Binance, reconstructed book on OKX. No continuous STOP handling for all 7- and 20-day holding intervals, so cannot state the first OKX stop crossing EVER occurred inside these final bars. No evidence that actual held OKX positions would match Binance original V5 trades.
- No independently signed original venue historical file digests nor seqId continuity guarantees.
- Conditional **source quote depth** enough in each first BID-cross snapshot, but queue/latency/concurrent market orders, precise historical contract lot increments, exchange trigger type, funding, actual fees, stop ACK/placement remain unproven. Do not present static ASK entry VWAP to static BID bar quote as executed PnL.
- No independent OOS 2026; historical years have already been viewed/tuned. No 10x LIVE GO.
- The trailing of original V5 can weaken on retracements. Broker-native monotonic stop child in V02 is a separate economic hypothesis that DID NOT outperform parent in closed historical 2023–25 replay.

## V06 final truth (October 2026)

- **OKX real original stop-date archived orderbook source: TWO parsed / six causal checkpoints per bar / full original-size displayed BID depth at first within-bar paper stop-level cross.**
- **Large intrabar price moves and BNB postcross recovery: CONFIRMED from user-supplied source.**
- **Cross-venue original STOP_INTRABAR price/time = actual real stop: FALSE / UNPROVEN.**
- **BNB original paper stop not tick-aligned at time: DOCUMENTED RISK.**
- **All-in after funding/fees independently profitable: NOT PROVEN.**
- **NATIVE STOP ACK, FUTURE OOS, LIVE GO: NO, NO, NO.**

Next rational attack: source-verify historically valid contract `ctVal`, `lotSz`, order trigger rounding and tick schedule; build a DIFFERENT pre-outcome-frozen venue-specific full *holding-path* sample before running more strategy test outcomes; maintain 2026 OOS seal. No retroactive strategy optimization.

Raw market data remains private and is not redistributable. Offline reproducible receipt script `research/convex_okx_l2_v06/exit_bid_5m_replay.py`; source-only synthetic Windows/Linux CI. No main merge, Render/Windows trading changes, account/wallet reads, real orders or money spent.
