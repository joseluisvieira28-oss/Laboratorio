# BTC-SETTLEMENT-DEMAND-001 — SOURCE/DATA GATE V0.2 PASS

Classification: SOURCE_DATA_PASS
Family: BTC-SETTLEMENT-DEMAND-001
Source Gate: BSD-TXCOUNT-002
Branch: btc-settlement-demand-v0.2
Run: 34864390599
Job: 104044430184
GitHub artifact: 10355248843
Artifact ZIP SHA256: d58b3e06683d827f393760112927b8c9314cdfdfb6ae559fbf1301b29383f163
Drive evidence ZIP: 1BeD-hxSccO4n9XDiGmJ7gh1rZDJ4BNvk
Drive V0.2 authority: 1zSEtz0CWJAyV9CEF5JQHEF7QrJmf8dFV
Authority commit: 6e23b0df54db10e96294403c3d7c33460168bb4a

Frozen source: Blockchain.com Charts & Statistics API / n-transactions only.
Frozen request boundary: start=2017-01-01, timespan=2921days, format=json, sampled=false.

Result:
- rows: 2922
- unique UTC days: 2922
- first timestamp: 2017-01-01T00:00:00Z
- last timestamp: 2024-12-31T00:00:00Z
- distinct calendar years: 8 (2017-2024)
- missing dates: 0
- protected-period access: 2025=false, 2026=false
- raw source SHA256: e0488714ce6023589de3e9cd15524c5f1e643a0ae0028147c8cb830b313ffa7f
- source manifest SHA256: 108525b5d3c3f331f8aef4dbcfcec05c8ab0221ba7c8cbc179d8c944c239b9cd

Outcome guards remained closed:
- price_values_opened=false
- signal_series_computed=false
- returns_computed=false
- pnl_computed=false
- performance_statistics_computed=false
- live_trading=false
- exchange_mutation=false

Historical V0.1 status remains unchanged: BSD-TXCOUNT-001 is CLOSED as PROVENANCE_FAILURE because its 2922-day administrative boundary returned one non-price 2025-01-01 source observation before fail-close. V0.2 does not erase or reclassify that failure.

Scientific routing:
BTC-SETTLEMENT-DEMAND-001 is the first newly opened mechanism in the post-GAP-V2 frontier round to reach SOURCE_DATA_PASS. This pass proves source availability/provenance only; it is not evidence of predictive edge. No BTC market outcome has been opened. Before any return/price/PnL, a separate prospective pre-Discovery MVE authority must freeze transform, threshold, horizon, timing, costs and promotion gates.
