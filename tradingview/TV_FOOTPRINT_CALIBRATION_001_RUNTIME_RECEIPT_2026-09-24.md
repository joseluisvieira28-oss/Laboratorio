# TV-FOOTPRINT-CALIBRATION-001 — TradingView Runtime Receipt

Observed: 2026-09-24 13:39 Europe/Zurich (11:39 UTC)
Evidence source: operator-provided TradingView screenshot in the active Crypto Lab session.
Branch: `tradingview-market-microscope-v0.1`
Instrument: `SRC Crypto Lab — Market Microscope V1`

## Runtime gate

PASS — Pine v6 compiled and added to chart successfully under the requested context.

Visual/runtime state observed:

- Chart: Bitcoin / TetherUS, Binance
- Timeframe: 5 minutes
- Dashboard title: SRC CRYPTO LAB / MARKET MICROSCOPE V1
- Lab: `TV-FOOTPRINT-CALIBRATION-001`
- Status: `INSTRUMENT CALIBRATION`
- Forward: `FORWARD ACTIVE`
- Footprint: `AVAILABLE`
- TV delta %: 14.29%
- POC migration: -5.27 bps
- LTF efficiency: 0.583
- LTF bars: 5
- Telemetry: `MEASUREMENT ONLY`
- Trading authority: `NONE`
- Forward-start marker: `TVFP START` visible

## Scientific interpretation

This receipt clears the previously external runtime/platform gate:

- Pine compiler compatibility: PASS
- TradingView footprint availability: PASS
- 1-minute intrabar retrieval on the 5-minute chart: PASS
- dashboard/state rendering: PASS
- forward boundary marker/state: PASS

This is **not** a sensor-calibration PASS and is **not** an edge result.

The terminal calibration remains locked until the frozen minimum evidence exists:

- 2,016 matched closed forward 5-minute bars
- Binance BTCUSDT aggTrades comparator
- frozen PASS_STRONG / PASS_LIMITED / FAIL_SENSOR thresholds

No parameters may be changed to influence the future result.

## Next operational gate

Do not route TradingView directly to an exchange.

Before enabling webhook telemetry, create and validate a research-only ingest endpoint that:

1. accepts the Market Microscope JSON schema;
2. rejects unknown lab/sensor identities;
3. persists the raw payload and receive timestamp;
4. enforces idempotency on symbol/timeframe/bar_close;
5. rejects pre-forward-boundary observations;
6. performs no trading or exchange mutation;
7. exposes receipts for later Binance-vs-TradingView calibration.

State after this receipt:

`RUNTIME_PASS / FORWARD_CALIBRATION_ACTIVE / SENSOR_VERDICT_PENDING / TRADING_AUTHORITY_NONE`
