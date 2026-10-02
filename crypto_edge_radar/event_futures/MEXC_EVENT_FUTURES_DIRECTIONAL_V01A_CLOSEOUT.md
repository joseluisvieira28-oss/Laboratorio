# MEXC EVENT FUTURES — DIRECTIONAL V0.1A CLOSEOUT

Date: 2026-10-02
Branch: mexc-event-futures-multiasset-v01-2026-10-02
Status: DIRECTIONAL SURVIVORS FOUND / PRODUCT ECONOMIC EDGE NOT PROVEN

## Scope actually tested

Assets:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

Retrospective base data:
- MEXC public index-price Min5 klines.

Event settlement horizons:
- 10m
- 30m
- 60m
- 1d

Frozen lookbacks after source-only Transport Amendment 01:
- 5m
- 15m
- 60m
- 4h
- 1d

Signal families:
- MOMENTUM
- REVERSAL

Partitions:
- Development: 2026-07-01 through 2026-08-01 exclusive
- OOS: 2026-08-01 through 2026-09-01 exclusive
- protected holdout: 2026-09-01 through 2026-10-01 exclusive
- 2026-10-01 and later remained unopened by this experiment

Multiple testing:
- 200 Development cells
- Benjamini-Hochberg FDR q=0.05

## Integrity / source facts

The original Min1 retrospective runner failed closed before calculating any directional outcome because July Min1 history was unavailable from the chosen MEXC public index route.

A source-only transport diagnostic, with no prices printed and no outcome calculation, proved that Min5 and coarser intervals had the required historical availability. Transport Amendment 01 was committed before any retrospective directional outcome was calculated.

The 1m lookback therefore remains:
FORWARD_ONLY_V0.1

No 1m retrospective result may be inferred from V0.1A.

## Reproducibility receipts

Successful workflow run:
- 37023083661

Workflow artifact:
- 11233798995
- artifact ZIP SHA256: 3c80ace2c74ffec1552bdc73823a4e3581dfee2608d41c3a1bdb1262ae424b31

Source page manifest SHA256:
- e930ba54769d47880227af7da2ac7925bc1d3e8e1d4104e56fd81329f7e55093

Pre-holdout corpus SHA256:
- 16c8a89079a27bc588eb925ce8eaf181d81d53108cf8878bf6496a50826a375e

Holdout corpus SHA256:
- 6e83b70029c4455395b4b10f2a3857bcc75960931acdd2de7a4a081c645e2d19

Orders created:
- false

Private account endpoints used:
- false

## Frozen progression result

Development survivors:
- 19

OOS survivors:
- 17

Protected holdout survivors:
- 16

Therefore this family is NOT NO_EDGE at the directional-proxy layer.

## Protected holdout survivors

| Asset | Event H | Lookback | Family | N | Accuracy | Wilson 95% CI | Raw p |
|---|---:|---:|---|---:|---:|---:|---:|
| MUUSDT | 30m | 5m | MOMENTUM | 1408 | 57.457% | 54.858–60.016% | 2.41e-08 |
| MUUSDT | 10m | 15m | MOMENTUM | 4257 | 56.754% | 55.260–58.235% | 1.24e-18 |
| SPCXUSDT | 10m | 15m | MOMENTUM | 3651 | 56.231% | 54.616–57.833% | 5.35e-14 |
| MUUSDT | 10m | 5m | MOMENTUM | 4216 | 55.811% | 54.308–57.304% | 4.72e-14 |
| SPCXUSDT | 10m | 5m | MOMENTUM | 3359 | 55.076% | 53.389–56.751% | <0.05 |
| NVDAUSDT | 10m | 5m | MOMENTUM | 3562 | 54.941% | 53.303–56.569% | <0.05 |
| MUUSDT | 30m | 15m | MOMENTUM | 1421 | 54.821% | 52.223–57.392% | <0.05 |
| NVDAUSDT | 30m | 15m | MOMENTUM | 1323 | 54.800% | 52.108–57.464% | <0.05 |
| MUUSDT | 10m | 60m | MOMENTUM | 4278 | 54.465% | 52.969–55.952% | <0.05 |
| NVDAUSDT | 10m | 15m | MOMENTUM | 3783 | 54.454% | 52.863–56.036% | <0.05 |
| ETHUSDT | 30m | 60m | REVERSAL | 1437 | 54.349% | 51.766–56.910% | <0.05 |
| NVDAUSDT | 10m | 60m | MOMENTUM | 3925 | 54.217% | 52.655–55.770% | <0.05 |
| NVDAUSDT | 10m | 240m | MOMENTUM | 3966 | 52.925% | 51.369–54.475% | <0.05 |
| BTCUSDT | 10m | 5m | REVERSAL | 4310 | 52.715% | 51.222–54.202% | <0.05 |
| BTCUSDT | 10m | 60m | REVERSAL | 4315 | 52.700% | 51.208–54.187% | <0.05 |
| ETHUSDT | 10m | 60m | REVERSAL | 4310 | 52.413% | 50.921–53.901% | <0.05 |

No 60m-event or 1d-event cell survived the final holdout.

The survivor concentration is therefore primarily:
- 10m Event Futures horizon;
- secondarily 30m;
- shorter 5m/15m chart lookbacks;
- MU / SPCX / NVDA momentum, plus BTC / ETH short-horizon reversal families.

## Economic firewall

MEXC Event Futures use an asymmetric payoff:
- correct prediction: principal returned plus payout × principal;
- incorrect prediction: principal lost;
- tie: principal returned.

At fixed payout r, the break-even win rate is:

p_BE = 1 / (1 + r)

At an 80% payout:

p_BE = 55.555...%

Four protected-holdout directional point estimates exceeded 55.555%:

| Candidate | Holdout accuracy | Point-estimate EV at fixed 80% payout |
|---|---:|---:|
| MU H30 / L5 MOMENTUM | 57.457% | +3.423% stake/event |
| MU H10 / L15 MOMENTUM | 56.754% | +2.156% stake/event |
| SPCX H10 / L15 MOMENTUM | 56.231% | +1.216% stake/event |
| MU H10 / L5 MOMENTUM | 55.811% | +0.460% stake/event |

However, NONE has a Wilson 95% lower confidence bound above the 55.555% economic threshold.

More importantly, historical payout-at-entry has not been proven. MEXC payout is dynamic and freezes only when an Event Future is submitted.

Therefore:

DIRECTIONAL_HOLDOUT_SURVIVOR != EVENT_FUTURES_ECONOMIC_EDGE

and:

PRODUCT_EDGE_STATUS = NOT_PROVEN

No historical Event Futures PnL is claimed.

## Cross-partition continuity for the four >80%-BE point estimates

| Candidate | Development | OOS | Holdout |
|---|---:|---:|---:|
| MU H30 / L5 MOM | 54.699% | 57.624% | 57.457% |
| MU H10 / L15 MOM | 55.465% | 59.754% | 56.754% |
| SPCX H10 / L15 MOM | 52.512% | 55.161% | 56.231% |
| MU H10 / L5 MOM | 57.567% | 60.702% | 55.811% |

These four are legitimate candidates for a new prospectively frozen replication stage. They are not live-trading authorizations.

## Post-hoc robustness diagnostics

These diagnostics were performed only after the protected holdout result existed.
They MUST NOT change the V0.1A scientific verdict or be used to retroactively optimize it.

Balanced accuracy was close to raw accuracy for the four leading cells, so the effect is not explained merely by always predicting the majority UP/DOWN class.

Day-block bootstrap diagnostics also kept the directional 50% threshold above the lower 95% interval for the four leading cells, but did NOT keep the fixed-80%-payout 55.555% threshold above the lower interval.

A post-hoc US-session split produced a strong clue:

- MU H30/L5: approximately 49.3% during US regular hours vs 59.5% outside.
- MU H10/L15: approximately 47.3% during US regular hours vs 59.1% outside.
- MU H10/L5: approximately 47.5% during US regular hours vs 57.9% outside.
- SPCX H10/L15: approximately 51.5% during US regular hours vs 57.6% outside.

This is NOT a promoted filter because it was discovered after the holdout was opened.

It is a NEW V0.2 hypothesis only.

A plausible mechanism to investigate is that 24/7 stock-futures/index behavior outside the US cash session may differ materially from regular-hours price discovery. The experiment must distinguish genuine predictive persistence from index-update, stale-price, liquidity or microstructure artefacts.

## Frontend / payout-source investigation

Public frontend inspection established:

- the Event Futures page carries a public product state;
- product objects include cycle configuration;
- the UI/store contains currentPayout;
- the public websocket includes push.event.contract product updates;
- the page displays per-side payout fields such as upPayRate;
- private position/order routes are separate and were not called.

The exact defensible historical payout-at-entry route is still NOT PROVEN.

No private position endpoint and no order endpoint was called during this investigation.

## Formal verdict

V0.1A verdict:

DIRECTIONAL_SURVIVORS_FOUND

Strongest research candidates:
- MU 30m event / 5m momentum
- MU 10m event / 15m momentum
- SPCX 10m event / 15m momentum
- MU 10m event / 5m momentum

Product-economic verdict:

EVENT_FUTURES_EDGE_NOT_YET_PROVEN

Reason:
- payout is dynamic;
- historical payout-at-entry is not yet defensibly available;
- even under a hypothetical fixed 80% payout, the 95% lower confidence intervals do not clear economic break-even.

## Next legitimate attack

1. Freeze V0.2 before opening any new outcome.
2. Replicate the four leading cells on unseen forward data.
3. Treat the off-US-RTH effect as a separate prospectively declared hypothesis, never as a V0.1 rescue.
4. Start a forward 1m source collector because retrospective 1m history is insufficient.
5. Capture time-stamped public payout snapshots if a stable public route can be proven.
6. Require payout-specific economic validation before any Event Futures execution discussion.
7. Keep all Event Futures trading/order mutation prohibited unless a later explicit execution authority exists.
