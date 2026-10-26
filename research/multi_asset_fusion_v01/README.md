# Multi-Asset Fusion Radar — Discovery only

Frozen protocol: commit `9273b1446977d23b4896d73d54d27d497fdc528c`, parent
`d4e7c542ebc67ec037ab2a1e86c8eaa07a9d8c96` from draft PR #271.
Branch: `research/multi-asset-fusion-discovery-2026-10-26`.
No candidate historical results were inspected before this protocol commit.
Inherited AVAX results were already exposed and are only a reference.

## Scope

SOLUSDT, ETHUSDT, BNBUSDT, XRPUSDT, LINKUSDT. No substitutions or tuning.
BTCUSDT Spot daily context; each asset uses Binance USD-M perpetual daily
trend and hourly execution proxies. No Spot altcoin or COIN-M substitution.

For calendar day D: `asset20 = sign(close[D-1]/close[D-21]-1)` and the same
formula for BTC20. Baseline enters every nonzero asset20. Fusion enters only
when its sign equals BTC20. Opposite context is a prespecified negative control,
never a replacement strategy. Nontrading days return zero and pay zero cost.
Entered-day gross bps: `asset20 * (open[D 02:00]/open[D 01:00]-1) * 10000`.
Subtract 0, 4, 8, 14 or 20 bps **once per roundtrip**, identically for all assets
and arms. UTC only; 730 calendar opportunities per asset. No compounding,
leverage, financing, funding, liquidation, bid/ask or capacity model.

## Causal chronology and custody

The daily candle labelled D-1 ends at D 00:00 UTC minus one millisecond;
the signal is modelled as known at D 00:00 and entry is D 01:00. D-21 to D-1
is exactly 20 days. The replay does not use the close of D or the 01:00 H1
close for entry. Exit is the **open** of the 02:00 H1 candle.
Monthly archives downloaded today may contain later corrections and do not
prove historical receipt, decision latency or an executable quote in 2022–23.
Checksum agreement proves archive/companion consistency from public HTTPS,
not an independently signed market-data attestation.

Only December 2021 warmup and January 2022 through December 2023 are in the
fixed URL inventory. No 2024–2026 candle endpoint or local protected dataset
is opened. Whole months must be complete, including irrelevant hourly bars;
missing data never becomes zero PnL. No interpolation or sample shortening.
All 319 ZIP/CHECKSUM pairs must pass before the economic report is emitted.
The listing register is a manually reviewed primary-source evidence record,
not automatically fetched exchange metadata. ETH, XRP and AVAX exact launch
clocks are unknown; midnight in JSON represents a day only. All documented
launches predate warmup. Archive continuity establishes available historical
candles, not continuous exchange uptime or regional/account eligibility.

## Reproduce

Python 3.12, numpy 2.3.5. No authenticated APIs or credentials are required.

```
python -m unittest -v test_replay test_end_to_end
python source_audit.py --cache archives --receipt source_audit.json
python replay.py --fetch --cache archives --out results-new
python audit.py --cache archives --out results-new
```

Without `--fetch`, replay is fully offline and requires the exact cached pairs.
Use a new output directory each time; existing report/gate/daily files are
refused to prevent stale PASS receipts after a failed rerun. A failed gate exits
2 and reports `NOT_REPORTED`; it must never be described as zero performance.
The source archive cache is deliberately excluded from Git. `manifest.json`
records every URL and the SHA256 of both ZIP and CHECKSUM. `fetch_receipts.json`
records fetch observations. A second implementation, `audit.py`, reads raw ZIP
CSVs and reconstructs all ledger signals, gross bps and 450 grouped totals using
Decimal arithmetic. It is another arithmetic check, not independent research.

## Reports and interpretation

`daily.csv` contains all six assets, causal times, directions, prices and masks.
`report.json` separates five candidate assets from the exposed AVAX reference.
Every arm/cost reports trades, daily and per-trade mean, summed noncompounded
bps, profit factor, hit rate, drawdown proxy, year/direction and removal of the
largest 1/3/5 winning trades. Direction diagnostics keep the calendar denominator.

Primary descriptive comparison is Fusion minus baseline mean net bps per
calendar day. Year-stratified paired moving-block bootstrap uses length 30,
10,000 draws, seed 271, common date draws across assets/costs. Blocks do not
cross years; start positions 0 through 335 are sampled with replacement and
13 blocks truncated to 365 days. This noncircular scheme has boundary weighting
and only two years; its intervals and centered two-sided approximate bootstrap
p-values are conditional exploratory diagnostics. Holm adjusts the 25 primary
asset/cost comparisons. Subgroups, negative control and concentration checks
are descriptive and have no confirmatory p-value claims. Holm does not account
for unknown prior experiments or asset selection.

Calendar-aligned correlation includes flat days as zero; it does not condition
on simultaneous trades. The equal-weight five-asset basket is a research
diagnostic with total notional one, not six units. AVAX is excluded from basket,
leave-one-asset-out comparisons and multiplicity calculations. Basket active
days mean at least one nonzero net contribution, not an order count.

Selection of surviving, currently familiar liquid assets is not a random
sample of the 2022 investable universe. Delisted/failed assets are omitted.
Shared BTC context and common crypto shocks reduce effective diversification.
Per-trade means alone are selection biased. A filter can improve a losing
baseline simply by avoiding fees. A positive delta does not prove positive
standalone profitability; positive Discovery PnL does not prove independent
edge, manual executability, zero-fee availability or a LIVE GO.

No existing strategy is reactivated. No trading, orders, accounts, secrets,
deploy, paid service, workflow dispatch, main merge or holdout release occurs.
