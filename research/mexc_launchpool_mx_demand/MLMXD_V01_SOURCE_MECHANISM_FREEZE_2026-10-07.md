# MEXC-LAUNCHPOOL-MX-DEMAND-001 — V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE MARKET OUTCOMES
Branch: mexc-launchpool-mx-demand-v0.1-source-2026-10-07

## Research question
Do official MEXC Launchpool announcements that explicitly create an MX staking pool produce a repeatable short-horizon demand effect in MX relative to BTC?

## Economic mechanism
MEXC Launchpool permits users to stake eligible tokens for project-token rewards. MX is an eligible staking token in relevant Launchpool events. An announcement that creates a new MX staking opportunity can temporarily increase MX demand/locking incentives.

## Event definition
An eligible event is an official MEXC announcement satisfying ALL:
1. official MEXC announcement source;
2. title/body identifies a Launchpool event;
3. body explicitly includes an MX staking pool or clearly states MX is eligible to stake;
4. publication timestamp is available from the official source;
5. event is not merely FAQ, product-upgrade, retrospective recap or generic Launchpool documentation;
6. duplicate announcements for the same project/event are collapsed to the earliest canonical announcement;
7. if multiple eligible announcements occur within 60 minutes, treat them as one information cluster.

## Discovery calendar
Primary source census: 2024-10-18 through 2026-09-30 UTC.

2026-10-01 onward is excluded from historical Discovery and preserved for future prospective work.

## Source gate
PASS requires:
- >=20 eligible asset-events;
- >=12 independent information clusters;
- >=2 calendar years represented;
- canonical timestamp available for every included event;
- source route is public/read-only and reproducible;
- no market-price outcome opened before a separate pre-outcome analysis freeze.

If the source gate fails, classify SOURCE_INSUFFICIENT_SAMPLE or SOURCE_BLOCKED. Do not lower thresholds.

## Outcome quarantine
Until a separate pre-outcome analysis freeze exists:
- do not fetch MX, BTC or any other market prices around eligible events;
- do not calculate returns, PnL, volatility or direction;
- do not select horizons from outcomes.

## Candidate identity
Candidate ID: MEXC-LAUNCHPOOL-MX-DEMAND-001

Potential market representation (NOT YET ACTIVATED):
MX relative to BTC, preferably by a reproducible public-market construction.

Exact entry, exit, costs, statistic and promotion gates MUST be frozen only after this source gate passes and before any market outcome is opened.

## Governance
Research-only.
No authenticated API.
No account read.
No orders.
No exchange mutation.
No wallet.
No spending.
No main merge.
No post-outcome tuning.
