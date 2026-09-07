# DREAM ACCOUNT OS v2.2 — VALIDATION REPORT

**Validation time:** 2026-09-07 17:52 UTC  
**STATUS:** PARTIAL — LIVE DATA FAIL-CLOSED

## API HEALTH

| Metric | Spot REST |
|---|---:|
| Request count | 3 |
| Success rate | 0.00% |
| Retries | 2 |
| Timeouts | 1 classified read timeout + 2 URL timeouts |
| HTTP 4xx | 0 |
| HTTP 5xx | 0 in final run |
| Latency p50 / p95 | unavailable; no successful request |
| Last successful snapshot | none |

The reliability layer performed bounded retries with exponential backoff and
jitter. No failed request became an empty market or a valid signal. The scan
ended `FAIL_CLOSED`.

**DATA COVERAGE:** 0.00% — rejected as insufficient.  
**WEBSOCKET:** FAIL — both official public endpoints timed out during opening
handshake in this runtime.  
**REST FALLBACK:** Reliability/retry/circuit framework passed deterministic
tests; no second officially supported Spot REST hostname was documented, so no
unverified mirror was invented.

## REAL MARKET SNAPSHOT

| Field | Result |
|---|---:|
| Pairs discovered | 0 |
| Pairs validated | 0 |
| Failed pairs | unavailable because universe bootstrap failed |
| Fast filter | 0 |
| Deep filter | 0 |
| A+ | 0 |
| A | 0 |
| B | 0 |
| Rejected | 0 market candidates; whole snapshot rejected |

**CURRENT REGIME:** UNVERIFIED / FAIL CLOSED  
**TOP 10:** unavailable  
**TOP 3:** unavailable

## SOL/BTC LIVE REGRESSION

**SOL STATUS:** UNVERIFIED. The historical close above $107 and retest of
$106.50–107 cannot be classified STILL VALID, UPDATED or INVALID without live
MEXC candles. The old level was not preserved as an active trigger.

**BTC STATUS:** UNVERIFIED. The historical $80,500 confirmation cannot be
classified without live MEXC candles. The old level was not preserved as an
active trigger.

## WEBSOCKET AND CANDLE INTEGRITY

Implemented:

- official Spot and Futures connection addresses;
- heartbeat/ping timeout;
- reconnect with bounded exponential delay;
- stale-stream detection;
- monotonic timestamp checks;
- sequence-gap detection;
- mandatory REST reconciliation on connect and sequence gap;
- no assumption of continuity after reconnect;
- UTC candle boundaries for 1m/5m/15m/1h;
- separation of open and closed candles;
- missing-candle/gap detection;
- breakout logic restricted to closed candles;
- look-ahead rejection tests.

The MEXC Spot stream currently uses Protobuf. Transport was implemented, but a
generated decoder from official `.proto` schemas and a successful live
handshake are required before WebSocket status can pass.

## FUTURES INTELLIGENCE

Public adapters now cover:

- current funding;
- real `collectCycle` / funding interval;
- next settlement time;
- funding history;
- `holdVol` as the documented holdings/open-interest field;
- fair/mark price;
- index price.

OI changes over 15m/1h/4h are designed to be calculated from persisted
snapshots. They remain unverified because the Futures REST and WebSocket hosts
were inaccessible. No 8-hour funding assumption is hard-coded.

## PAPER VALIDATION

**Paper trades open:** 0  
**Paper trades closed with real data:** 0  
**Deterministic full-lifecycle trades closed:** 1

The automated regression completed:

`DISCOVERED → WATCHING → ARMED → ACTIVATED → PAPER_OPEN → TP1_HIT → TP2_HIT`

It persisted entry, stop, targets, risk, estimated costs, score, tier, regime,
MFE, MAE, exit time, exit price, exit reason and realized R. Restart recovery
was verified. Invalid state jumps are rejected. This proves lifecycle mechanics,
not market edge.

**SYSTEM EXPECTANCY:** INSUFFICIENT SAMPLE

## TEST RESULTS

**18/18 automated tests passed.** Coverage includes v2.1 invariants plus candle
boundaries/gaps, stale-safe behaviour, cache/health metrics, impossible state
transitions, complete paper lifecycle and persistence after restart.

**FAILED TESTS:** none in the deterministic suite.

## DEFINITION OF DONE

| Requirement | Status |
|---|---|
| Complete real MEXC snapshot | FAIL |
| Data coverage reported | PASS |
| WebSocket operates and recovers live | FAIL; mechanics tested only |
| REST fallback | PARTIAL |
| Candle-close integrity | PASS deterministic; live blocked |
| Funding/OI verified live | FAIL |
| Full paper trade cycle | PASS deterministic |
| SQLite history after restart | PASS |
| Stale data fails closed | PASS |
| No execution capability | PASS |
| Dashboard reflects actual state | PASS |
| SOL/BTC live regression | FAIL — no live data |

## KNOWN LIMITATIONS

- Network policy/proxy blocks direct REST and WebSocket access to MEXC.
- No live MEXC snapshot can be certified from this runtime.
- Spot Protobuf decoder generation remains pending.
- OI deltas require multiple successful time-separated snapshots.
- The 20-resolved-paper-trade checkpoint has not started because accepting
  unverified market data would invalidate the experiment.

## CURRENT BEST MOVE

**NO TRADE.** Preserve all CHF 56. Do not activate SOL, BTC or any replacement
candidate until a runtime obtains verified MEXC data with adequate coverage.

