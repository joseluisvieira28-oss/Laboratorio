# LOR-RF-001 — TERMINAL DISCOVERY CLOSEOUT
Date: 2026-10-09
Status: **NO_EDGE_DISCOVERY / EXACT MVE CLOSED / NO PROMOTION**
Authority: Research-only, outcome-locked OOS 2025 and protected 2026 remain SEALED.

## Frozen-before-outcome provenance
- Original source/novelty audit: PR #167.
- Economic freeze: `research/lorenz_price_action/LOR_RF_001_ECONOMIC_PREOUTCOME_FREEZE_V0_1.json` (commit `1ebf1f46a29cbf0bdac73be9af6f3ad48126dfb7`).
- Engine exact SHA256: `f0c9ee10800a1a6f2f0693d81f163608cdaab3ff0987119aeae2ff339bcdd692`.
- Source-only+synthetic gate: run `37915073277`, terminal success, tests 16/16, official HEAD+checksum metadata 25/25. Artifact `11609176874`.
- One-time discovery trigger: commit `5b0a1d9015e0a13ea493afaf9699c4120d130ccc`.
- Canonical discovery run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37915166107
- Canonical discovery artifact: `11609281843`; uploaded ZIP sha256 `08806d95cbff3bd5868085f6fb81c9f3853a6bf8aadda4a6c7b4ce41561a9b7b`.
- Workflow jobs: source/test success, Discovery success; no trading/account mutation.

## Source and execution semantics
Binance Vision official BTCUSDT USD-M futures: 2023-12 1h for warmup, 2024-01..12 1h and 1m with matching ZIP CHECKSUM. All 25 bound official archives read and SHA-verified before classification. Timestamp continuity and OHLC constraints enforced.

Signal: mechanical interpretation of publicly attributed Fabrício Lorenz three-bar Realização Frustrada; long down/up/down, short up/down/up in EMA9/SMA21/SMA200 trend. 3-bar extrema stop-entry and protective stop; target 1R; entry limited to next 3h; 24h maximum hold, one-minute OHLC conservative collision handling, independent serialization.

The fixed 26-bps primary / 40-bps stress round-trip haircuts are research *hurdles*, NOT certified real Binance/MEXC account fees, maker/taker fills or funding. Even theoretical profitability would require separate executable-venue proof.

## Source-complete 2024 Discovery: RF primary
| Metric | Result |
|---|---:|
| RF entries/signals | See canonical JSON artifact |
| Executed trades | 108 |
| Distinct UTC trade dates | 100 |
| Distinct UTC trade weeks | 49 |
| Mean gross | +11.2038023746 bps |
| Mean net (fixed 26 bps) | **-14.7961976254 bps** |
| Mean stress (fixed 40 bps) | **-28.7961976254 bps** |
| Net profit factor | 0.7300342233 |
| UTC-week bootstrap net 95% CI | [-34.6527755790, +4.2599317149] bps |
| Positive mean-net quarters | 1 / 4 |
| Longest week positive-PnL share | 7.055942% |
| Exit reasons | STOP 45, TARGET 62, TIMEOUT 1 |

## Frozen trend-only counterfactual
- N = 427, 260 UTC dates, 53 weeks.
- Mean gross = +6.3004620060 bps.
- Mean base net = -19.6995379940 bps.
- Mean stress net = -33.6995379940 bps.
- Net PF = 0.7235303421.
- Positive quarters = 0/4.
- RF mean incremental net over baseline ~+4.9033403685 bps, below the frozen +5bps floor.
- Paired-week bootstrap uplift 95% CI = [-15.7920968476, +25.4114515315] bps, DOES NOT show positive incremental uplift.

## Gate-by-gate adjudication
- RF N >=100: PASS.
- Distinct UTC dates >=40: PASS.
- Distinct weeks >=16: PASS.
- Baseline N>=100 and dates >=40: PASS.
- RF net26 mean >0: FAIL.
- RF net40 mean >0: FAIL.
- RF net26 bootstrap lower95 >0: FAIL.
- RF net PF >=1.15: FAIL.
- >=3 of 4 quarters positive: FAIL (1/4).
- Incremental net >=5bps: FAIL (~4.90).
- Paired-week uplift bootstrap lower95 >0: FAIL.
- Max positive week <=25%: PASS (7.06%).

**Terminal scientific state: NO_EDGE_DISCOVERY** (not SOURCE_BLOCKED, not INSUFFICIENT_SAMPLE).
This is a negative economic result for *this exact fully pre-frozen mechanical translation*, not a proof that every possible Lorenz strategy, market, timeframe or execution venue has no advantage.

## Interpretation and limits
Gross mean +11.20bps is a descriptive effect, not a validated predictive mechanism: gross 95% CI implied by constant 26-bps shift includes zero (about [-8.65,+30.26]bps). Execution is 1m OHLC proxy, not actual queue/latency-aware fill. Favorable fills could be overstated when minute path is unknown. These limitations cannot rescue a failed net economic result.

## Anti-rescue / authority
- Do NOT lower assumed costs to rescue the exact MVE.
- Do NOT select only a positive quarter, profitable side, extra filter, target, duration or risk band after opening outcomes.
- Do NOT rerun with tuned rules under this identity.
- Do NOT unlock 2025 OOS or 2026 holdout for this failed development.
- Other distinct price-action families require separate provenance, non-duplication gate, new identity and a genuinely pre-frozen source/economic design; 2024 RF opened outcomes must be treated as prior information, never confirmatory for a tuned sibling.
- No micro-live promotion. No live orders. No main merge. No exchange mutation.

## Evidence
[Exact GitHub run](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37915166107)
[Immutable discovery artifact](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37915166107/artifacts/11609281843)
