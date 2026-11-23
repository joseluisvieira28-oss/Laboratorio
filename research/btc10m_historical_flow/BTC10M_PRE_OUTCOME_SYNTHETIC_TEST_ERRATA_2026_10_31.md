# BTC10M HIST V0.1 — PRE-MARKET SYNTHETIC FIXTURE ERRATA
Date 2026-10-31, after failed CI #41232464971, BEFORE ALL archived historical ZIP/price/outcome retrieval.

Original frozen source/trading hypothesis and all thresholds unchanged: official Binance monthly 2024/2025 two markets, prior-3min executed-taker buy share >=.55/<=.45 primary and >=.60/<=.40 secondary, q0.70 economics and always-UP/spot-only controls.
The original CI failed in synthetic-only unit test because the manually constructed test record used by summarize(fake) omitted its required 'always_up_side' comparison field. Traceback KeyError always_up_side. The workflow therefore SKIPPED download/evaluation step, and ran no official Binance archive requests. No historical outcomes were opened, nor signal rules modified.
Change committed d2c316fa8d099f51acb7269b21bdc48a34ca4e9f solely adds 'always_up_side':'UP' to synthetic fake record. Original CI remains failed; rerun is a new original official archive source attempt with exactly the same prespecified test and dataset. Do not treat a test PASS as market evidence.
