# FUNDING-SQUEEZE-001
## V0.3.1 BINANCE DATA-VISION IMPLEMENTATION ADDENDUM
Date: 2026-10-07
Status: FROZEN BEFORE 2025 CONFIRMATORY OUTCOME ACCESS

### Purpose
Freeze mechanical source/parsing details needed to execute V0.3 without changing its scientific rules.

### Official source files
Funding history used for causal threshold initialization and 2025 receipts:
- Binance Data Vision USD-M monthly fundingRate BTCUSDT
- months: 2024-01 through 2025-12 only

Confirmatory market prices:
- Binance Data Vision USD-M BTCUSDT 1h klines
- Binance Data Vision Spot BTCUSDT 1h klines
- months: 2025-01 through 2025-12 only

No 2026 URL may be requested.

### Checksum rule
Every ZIP used must have its official sibling .CHECKSUM sidecar downloaded first or alongside it.
- parse the first 64-hex SHA-256 token from the sidecar;
- compute SHA-256 of the downloaded ZIP bytes;
- exact equality required;
- any missing/mismatched checksum => SOURCE_BLOCKED before scientific verdict.

### Timestamp parsing
Binance archive timestamp units may differ by dataset/era.
Mechanical unit inference is frozen:
- absolute median >= 1e14 => microseconds;
- absolute median >= 1e11 and < 1e14 => milliseconds;
- otherwise => seconds.

Funding calc_time:
- preserve raw parsed UTC time;
- normalize to nearest UTC hour only for joins to hourly prices;
- require absolute raw-to-normalized offset <= 5 seconds;
- fail closed otherwise.

Kline open_time:
- preserve exact parsed UTC timestamp;
- require unique hourly open timestamps after deduplication;
- no interpolation.

### Coverage
Required:
- all 24 frozen funding ZIP months checksum-valid and parseable;
- all 12 frozen USD-M 1h kline months checksum-valid and parseable;
- all 12 frozen Spot 1h kline months checksum-valid and parseable;
- every 2025 calendar hour required by an eligible entry/exit or funding receipt must be directly present.

No missing-price interpolation or forward/back fill.

### Scientific identity
No change to:
- q90 signal;
- 540-settlement trailing history;
- 270 minimum history;
- 168h fixed hold;
- one-active-position rule;
- 20 bps primary cost;
- 25 bps stress;
- 2025-only confirmation;
- N/PF/bootstrap/chronological-half gates;
- verdict taxonomy.

### Outcome-access declaration
At this addendum freeze, no V0.3 2025 confirmatory funding/spot/perpetual outcome has been opened.
