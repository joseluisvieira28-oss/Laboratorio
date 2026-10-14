# V05 — original three-CONVEX deterministic shadow execution core (2026-10-14)

Status: **IMPLEMENTED OFFLINE CORE / NOT MEXC LIVE EXECUTION / NO LIVE GO**.

This is a distinct operator-engineering child of the source-locked historical research, NOT an extension of the old Options V2.1 / BNB / DH03 Triple Fishing V03. It does not alter main or any original research closeout, OOS or locked 2026 outcomes. No API credentials, endpoints, wallets, account/private reads, exchange mutation or real-money orders are present.

## Scientific lineage

- Original recovered V5 signal: pinned git blob `19c8b8e2363f253458db42111b6701f3a3ef1f4b`, path `engine/three_convex_v05/vendor/V5_PARENT_PINNED_SOURCE.py.txt`, copied byte for byte from `labs/btc-convex-trend-capture-001/prospective_shadow_snapshot_v0_2_aggressive.py` at frozen commit `42d6748864dd78b911b5f1fc775ff1950b556d2b`. SHA fingerprint is checked before any signal calculation. Only `sma/stdev/rma/rsi/build_signals` AST function definitions run; never execute parent's module globals or network collectors. Signals: completed-close SMA200 regime, RSI14 Wilder <30, z <-2, close<BB lower 2std, volume>rolling SMA20, at least 3/4.
- SOL_CONVEX_NATIVE_5M: frozen child original SHA `af82deefd5634a77a7b49e7acec61ca21eb44a49`.
- SOL_CONVEX_1H, BNB_CONVEX_4H: frozen common-period original SHA `42d6748864dd78b911b5f1fc775ff1950b556d2b`.
- Exact historical signal source: **Binance USD-M continuous canonical 5m candles**, resampled locally for 1h/4h, NOT MEXC 5m source and NOT independently downloaded 1h. The V05 JSONL input 'source' label is asserted by its producer and NOT independently verified by this package. Use only for offline tests or a separately frozen prospective shadow; no protected 2026 holdout is opened by the initial CI.
- Trailing stop remains **original NONLATCHED**: entry×(1-4%); when its own completed TF close gains at least 5%, max(initial stop, peak recorded 5m high ×(1-12%)), else original stop; can WEAKEN. This is identified as a live safety blocker rather than silently converting to monotonic. The 5m simulation checks stops before applying a newly completed bar's high/trail. Gap-at-open pessimistically exits at gap price.

## Automatic offline state machine

- Processes both symbols in chronological order, three virtual signal lanes, two maximum simultaneous physical symbol exposures (SOL + BNB) under current policy. **Two independent SOL LONG positions are NOT claimed even when account reports HEDGE**; a second same-symbol signal is rejected while a SOL reservation or position exists. Simultaneous SOL 5m+1h signals are both rejected rather than assigned arbitrary priority.
- Signal availability at TF candle CLOSE, theoretical observation after close, first scheduled fill at **close + exactly one 5m candle**, as per historical V5. If that open is missed, BLOCK; no late chase. Full canonical 5m continuity; no duplicate or impossible OHLC; last incomplete aggregates discarded. Requires at least 250 complete TF bars as an operational source warmup, not a new signal threshold. It is insufficient to prove agreement with the historical full-length RSI: live-source parity remains UNPROVEN.
- Paper quantity 1 minimum-size contract: **SOL_USDT 0.1 SOL**, **BNB_USDT 0.01 BNB**, as supplied by the user after a dated MEXC public query. These contract specs and current bid/ask are NOT independently reverified by this engine. Observed hypothetical risk must be <=0.50 USDT per entry, aggregate <=1.50, SOL <=1.00, margin<=100 USDT at 10x. The model sizes at the Binance 5m candle opening, which is **NOT an MEXC executable ask**.
- Fee per side 8bps, slippage per side 2bps, one 5bps estimated funding reserve. All illustrative, historical fee evidence reexamined from September 2026 Drive: official MEXC API Futures schedule was 8bps taker floor, authenticated fee endpoint once reported 0 bps. The funding proxy here is NOT exact venue funding settlement and cannot establish net alpha. Rates are frozen for this stage, not tuned after outcomes.
- `run_offline.py` accepts source-asserted JSONL or `--synthetic-qa` and optionally emits an immutable directory of model report and SHA256 hash-chained event receipts. Existing output dirs are rejected, never silently overwritten.
- `DisabledBroker` intentionally raises `EXCHANGE_MUTATION_NOT_IMPLEMENTED_NO_LIVE_GO` for every attempted broker method. All runs, including full unit tests, produce no account reads or order requests. Nothing in this folder is a Windows live installer.

## Run safely

From the repository root, Python 3.11 or newer:

```powershell
py -3 -m unittest engine.three_convex_v05.test_engine_v05 -v
py -3 -m engine.three_convex_v05.run_offline --synthetic-qa
py -3 -m engine.three_convex_v05.run_offline --synthetic-qa --output-dir .\\evidence\\synthetic_case_001
```

For a separately authorized source-verified prospective shadow input, JSONL each row must contain `symbol` = SOL_USDT/BNB_USDT, `source` = BINANCE_USDM_CANONICAL_5M, integer UTC `t` = candle *open* milliseconds multiple 300000, `open/high/low/close/volume` finite OHLC. Both symbols require continuous 5m bars with long enough 4h source warmup. This package does not fetch market candles, enforce external publication times for user-supplied JSONL, monitor the PC in background or prove venue matching. A user-provided `source` string is not custody proof.

## Closed vs open gates

**Completed in this branch subject to CI:** exact pinned-parent signal extraction by AST, closed-bar aggregation and timing, deterministic 3-lane scheduler, physical same-SOL collision block, one-contract risk model and budget, 4%/conditional 12% original stop shadow simulation, pessimistic gap-at-open paper exits, chain-of-hash receipts, synthetic no-order tests on Windows/Linux.

**NOT completed** (must be solved before any possible live authorization):
1. True trusted 5m continuous collector with timestamp provenance, completed candle publication proof, stale/gap fail-close and original source parity. Source from the original archived canonical Binance USD-M cannot simply be presumed interchangeable with MEXC. Authenticated account fees/balance/open orders/current 10x isolated instrument-tier rights/positions are NOT observed by V05.
2. Real MEXC broker adapter with safe isolated 10x permission scope; order idempotency, entry ACK/fill verification, **immediate verified position-matched exchange-hosted 4% initial stop ACK**, amend/partial/reduce/cancel flows, protection gap minimization, late fills, and crash/clock/network recovery proven with offline protocol tests and controlled external evidence. Broker stop ACK cannot be faked by a simulated venue.
3. Original nonlatched trailing may WEAKEN. Preserving it with an actual broker amend needs bounded safety justification; freezing stop monotonically changes original economics and needs a separate preregistered economic fork and forward evidence. No silent substitution.
4. Exact MEXC fees+funding+bid-ask executable-spread, 2026 **prospective** source-gated shadow after valid pre-outcome freeze, independent sample, economic GO criteria, operator signoff. No early use of locked 2026 holdout.
5. Prior legacy Windows tasks disabled and user-supplied process name query returned no matches, but it does not prove no MEXC positions/resting orders or remote processes.

**Veredito: THREE_CANAS_V05_SHADOW_CORE_IMPLEMENTED; LIVE_EXECUTOR_INCOMPLETE / NO_LIVE_GO.** Not a money-printing claim. Keep old tasks DISABLED, never run any old Install/Switch/Ready-And-Arm just as a diagnostic. This is not a live connector.
