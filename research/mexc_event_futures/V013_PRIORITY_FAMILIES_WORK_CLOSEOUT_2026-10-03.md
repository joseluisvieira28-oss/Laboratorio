# V0.13 priority families — legitimate source and shadow closeout

Date: 2026-10-03 Europe/Zurich.
Requested branch: mexc-event-futures-event-conditioned-v0.13-prereg-2026-10-03.
Starting head: 196e5df3ba50de84e03c91faeccf0e6df7db4f29.
Required handoff and V0.11.6/V0.12/V0.12.1/V0.13 freezes read before work.
All upstream scientific freezes, original registry and evaluator are unchanged.

## Verdicts

| Family | Source verdict | Current scientific state |
| --- | --- | --- |
| OPTIONS-VOL-FWD-001 | SOURCE_GATE_PASS: BTC 3/3, ETH 3/3 real matched pairs | Pre-outcome activation freeze committed; runtime preflight PASS; N=0, INSUFFICIENT_N |
| LIQUIDATION-FLOW-FWD-001 | NO_EVENTS_OBSERVED: subscription/heartbeat healthy; BTC 0, ETH 0 in 600s | No family activation; no threshold calibration; extended source-only probe preregistered |

Neither family has a demonstrated edge or promotion. No Event Futures outcomes were
opened. The quiet liquidation window is not NO_EDGE or a failed hypothesis.

## Immutable authority chain

Source gates preregistered in a277123b29ab2e7028a7b2858845170f6f583ac6.
Source run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37073818293

Options activation freeze committed in 76d39bf40eb7922d930523ad8b53738b172d4b33,
before the first bounded forward run. Activation boundary: 2026-10-02T22:50:51Z
(2026-10-03T00:50:51+02:00), epoch 1790981451000ms.
Canonical rule SHA256: edd02c530398465cb35e481f96e336ebd0dcccc73235aaffe6c1d984c3986517.
Frozen direction FOLLOW_INSURANCE_SKEW; skew >=5pp DOWN, <=-5pp UP, otherwise no
signal. Exact 10-minute horizon, 5-second freshness, first-only unresolved overlap,
minimum N=100 per symbol, one batch at boundary+30 days, unchanged V0.13 statistics.

Forward smoke: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37074644170
Preflight observed a fresh exact passive browser payout response and public index
ticks for BTC/ETH satisfying the source-join gate, with both direction payouts checked.
Three valid source rounds per currency. No eligible >=5pp absolute skew appeared:
all six source attempts were NO_SIGNAL, not source failures. Opened=0, resolved=0.
No significance/returns evaluation ran. Signal-to-decision and expiry paths remain
untested with real eligible events; this smoke does not prove their end-to-end behavior.
The 120-second bounded collection is complete and is NOT a continuous collector.

## Independent evidence audit

| Artifact | ZIP SHA256 | Independently verified entries |
| --- | --- | --- |
| Options source, 11255507173 | 9fd39ca56bbd4de1cfffafa1ba07e4b9b3b81905c4afa79a9019c6b7b73eb5f2 | 36/36 raw response bodies |
| Liquidation source, 11255353214 | dd22bc831c7eca3be57d4d98d6c5a1fa679d98f7d48e276d4f5230abe5e46da0 | 30/30 raw messages |
| Options smoke, 11255948065 | c4e5379eeebfc99a4109872d8e50005137e3b9377986791259a9a9dbb69b4ebe | 105/105 raw/ledger manifest entries |

ZIP hashes, every manifest SHA256 and every byte length passed. Local source attempts
are preserved separately: options PARTIAL_SOURCE (BTC 2/3, ETH 3/3; stale BTC quotes
exceeded 5 seconds in one round), liquidation SOURCE_BLOCKED at websocket upgrade.
No failing local row was replaced by a runner row or pooled into a PASS.

## Safety

No login, Event Futures credentials, private requests, account reads, wallets, orders,
trading, paid data, main merge/change or September holdout opening.
Public browser blocked 239 non-GET requests and 15 sensitive GETs before transmission;
zero authenticated requests transmitted. Browser websocket connections were blocked;
the separate index client subscribed only to the two frozen public index topics.
Every future shadow decision must use its actual direction-specific payout q and raw
source body, with p_BE=1/(1+q), WIN=+q, LOSS=-1, TIE=0. No fixed 80% assumption.
Public research index is never an executed openPrice.

## Next work, already bounded by authority

Liquidation: launch the preregistered 3600-second public source-only extension. It
must receive real BTC/ETH events before PASS. Then acquire the separately specified
24-hour healthy-bin calibration and commit actual numeric thresholds/new activation
boundary before any Event Futures outcomes. No source PASS or calibration result is
claimed in advance.

Options: before any additional forward run, supply a persisted ledger/continuity receipt,
pin the original activation boundary and preserve the same rule/hash/batch. Do not
rerun the initial smoke as an independent ledger or reset its boundary. A durable
collector is a separate operational implementation task; branch-only cron is invalid.
There is no automatic 24/7 observation or promised background audit from this smoke.
