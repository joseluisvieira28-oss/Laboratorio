# CHF 56 Dream Account OS v2.3

Read-only data collector, market scanner and paper-shadow engine for MEXC. It contains no order, cancel, transfer, or
withdrawal code and requires no private API key.

## Commands

```bash
PYTHONPATH=src python -m dream_account.cli live-scan
PYTHONPATH=src python -m dream_account.cli fixture-scan
PYTHONPATH=src python -m unittest discover -s tests -v
```

`live-scan` fails closed if MEXC data is unavailable or malformed.
`fixture-scan` is strictly an offline regression test and never labels fixture
results as live market signals.

Outputs are written to `runtime/dream_account.sqlite3` and
`runtime/dashboard.html`.

The raw MEXC adapter is separated from the strategy engine by a normalized
snapshot contract. Only `VERIFIED` snapshots can reach signal evaluation; a
batch below 95% verified coverage fails closed.

Persistent Docker runtime:

```bash
docker build -t dream-account-os .
docker run --restart unless-stopped -p 8080:8080 -v dream-data:/var/data dream-account-os
```

Run `python scripts/network_diagnostic.py` inside the target runtime to test
DNS, TLS, Spot/Futures REST and Spot/Futures WebSocket independently.

The v2.2 data layer adds separate connection/read timeouts, bounded retries,
exponential backoff with jitter, rate-limit handling, circuit breaking,
endpoint health metrics and short metadata caching. WebSocket transport uses
heartbeat, reconnect, stale detection, timestamp/sequence validation and REST
reconciliation. MEXC Spot messages use Protobuf; a production decoder generated
from the official schemas is still required before live streaming can pass.
