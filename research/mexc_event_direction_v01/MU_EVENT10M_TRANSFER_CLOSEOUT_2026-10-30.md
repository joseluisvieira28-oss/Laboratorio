# MU CASH → MUSTOCK Event-10M V0.1 — FROZEN HISTORICAL TRANSFER CLOSEOUT
Date 2026-10-30; research branch only. **SOURCE_PASS / TRANSFER_HYPOTHESIS_FAILED_IN_DISCOVERY / NO EXECUTABLE EVENT FUTURES EDGE / NO LIVE GO.**

## Authority chain
- Frozen source+signal scientific protocol commit 9e527cdc8a5a96c1a17504611519b10024607a6d; no prices opened prior to freezing signal transfer from independent NVDA model.
- [Source-only run #41013501292](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41013501292): exactly Oct28–29 public Yahoo MU cash 1m and MEXC MUSTOCK_USDT index 1m all required bars; TWO GETs each, 3/3 canonically identical, no raw SHA drift; all time-bar SHA committed before outcomes.
- [Frozen 24-slot historical proxy run #41013651717](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41013651717): 6/6 synthetic unit guards, 24/24 fixed NY 09:35–11:25 starts, 10m expiry proxy, exact frozen source hash verification PASS. Full all-slots + baselines in workflow artifact.

## Historical price-only outcomes, per unit staked and hypothetical q=.8
| Frozen mechanism | Signals | Win | Loss | Win rate | Unit EV (q0.80) |
|---|---:|---:|---:|---:|---:|
| MU actual cash impulse plus lag MEXC index, transferred unchanged | 5 | 1 | 4 | 20% | **−0.64** |
| MU cash-only impulse 10bps, across all 24 slots | 15 | 4 | 11 | 26.67% | −0.52 |
| Always UP 24/24 (diagnostic only) | 24 | 10 | 14 | 41.67% | −0.25 |
| Always DOWN 24/24 (diagnostic only) | 24 | 14 | 10 | 58.33% | +0.05 |
| Always UP on SAME 5 candidate-selected instants | 5 | 2 | 3 | 40% | −0.28 |
| Cash-only on SAME 5 candidate-selected instants | 5 | 1 | 4 | 20% | −0.64 |

By-day **candidate** Oct28 1W/2L (3) and Oct29 0W/2L (2): negative in both daily parts. The always-DOWN +0.05 is a superficial two-day drift, not certified economic alpha, and must NOT be selected retrospectively. The tested lag mechanism has not added value beyond its same-day baselines.

## Unsolved
- MEXC Event Futures historical 10m direction-specific payout at Oct28–29: NOT CAPTURED; q=0.80 hypothetical, not exact.
- Historical cash equity and MEXC index receipt **as-of** decision: not demonstrated. 1m historical close may have been delayed.
- Index OPEN(t), OPEN(t+10) proxies are 10sec ahead of hypothetical decision/expiry: price at server's Event Futures executed entry/settlement NOT proven. NO real PnL.
- Only two already-selected exploratory dates; 5 signals inadequate for generalization. NO independent OOS.
- Screenshot MLIUSDT identity still unknown, **NOT** equated to MU or MUSTOCK.
- Old NVDA forward Oct05–30 and September protected holdout stayed CLOSED. No trades, accounts, private APIs, spending, main merge, or live.

## Important separate scientific errata: SPCX LISTING
Earlier MU source freeze described SPCX as not having an equity-market primary reference. **That assertion is factually outdated**: the official SpaceX IR confirms the corporation's shares started trading on Nasdaq as SPCX June 12, 2026 (https://ir.spacex.com/faqs-and-contact/). Keep the initial freeze immutable for audit; this closeout publicly corrects that external fact. A distinct, source-first SPCX-equity-vs-MEXC-index gate is now justified, **not a retrospective alteration of MU signal or outcomes**. MEXC labels SPCXSTOCK_USDT as associated with SPCXON tokenized tracker; index-reference equivalence still must be proven separately.
