# MEXC DEPTH V1.1 — independently checked real source receipt
2026-11-04 UTC. Original immutable run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41873154369

- Source-only protocol frozen at commit f3f3ef4cba6a702657166a4d6daa14bd9a63e0af before run.
- Artifact #13346670234; downloaded ZIP SHA256 7dce838df2c90ace437aec8f485009aa26c53d54c6b2cc3f52d24d3ce6c83309, same as GitHub digest.
- Original raw NDJSON SHA256 638de22c7984c90ab2b10a0ad910c3cd634d2e101f0bb6bf28e22d0dc9bc6aea, same as receipt.
- 120.242s, 483 frames overall, 427 MEXC public BTC_USDT push.depth.full snapshots, 46 push.ticker events, 8 pong and two successful subscription acknowledgments.
- Depth snapshots: 427 fresh publisher timestamps, 0 stale, 425 accepted after three-consecutive-fresh initialization (including third snapshot), age min 57ms max 103ms; no parser errors or transport disconnections.
- Control ticker on same socket: only 14/46 fresh by frozen 1500ms maximum, remaining 32/46 stale. Depth is a clearly better *observed quote feed* in this single source window.
- This proves a public MEXC full-depth message source is available and temporally fresh for this bounded observation. Does NOT certify full order fills, time-skew across exchanges, 60-second outcomes, broker access, actual user fee rate, profitability or live trading.
- Verdict MEXC_DEPTH_SOURCE_WINDOW_TECHNICAL_PASS / ECONOMICS_NOT_TESTED / NO_LIVE_GO.
