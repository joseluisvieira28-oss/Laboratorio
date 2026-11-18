# MEME-DIAMANTE-002 — second-wave candidate (READ ONLY)

This folder is a **hypothesis test**, NOT a profitable trading system.

## Offline usage

Python 3.11+ (stdlib only):

    python -m unittest discover -s research/meme_diamante002 -p 'test_*.py' -v
    python research/meme_diamante002/second_wave.py PATH/TO/observed_trades.jsonl --output result.json

One JSON object per executed token-side trade; fields: `mint`, `timestamp` (Unix seconds), `tx` (unique signature), `wallet` (on-chain address), `side` (`buy`/`sell`), `price_usd`, `amount_usd`, `liquidity_usd`, `source`.

The input is **not included**. Synthetic unit tests must never be interpreted as empirical market evidence. A signature can include several legs: the data provider must normalize and document each token-side fill. Trades must be chronologically observed on the same pool with point-in-time provenance, plus launch-universe coverage; the script does not establish these facts.

Output has SHA-256 of input and explicit missing-entry/missing-exit outcomes. All 'profit' numbers, if any, are optimistic **trade-print proxies**, NOT marketable fill estimates.

No API calls, no monitoring schedule, no keys, no signing, no wallet connection, no orders. See [PROTOCOL.md](PROTOCOL.md) for the locked scientific gate. Until independent executable quotes and a held-out real dataset exist: **ECONOMIC NO-GO.**
