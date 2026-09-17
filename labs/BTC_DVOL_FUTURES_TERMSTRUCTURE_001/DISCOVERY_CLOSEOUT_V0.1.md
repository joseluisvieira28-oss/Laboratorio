# BTC-DVOL-FUTURES-TERMSTRUCTURE-001 — BASIS CONVERGENCE DISCOVERY CLOSEOUT V0.1

Date: 2026-09-17
Discovery ID: DVOL-TS-CONVERGENCE-DISCOVERY-001
Canonical run: 35278588512
Canonical head SHA: 19421f20e334a3b096d0ba886f8ee51dd25c3473
Artifact ID: 10521099777
Artifact ZIP SHA256: 203468d445a4513670490b0f00a9a4b207973f1fdae65e8431d7cf9c6c65edf5
Source receipt SHA256: 81a497892f0ca627f7fcc4f079bb759bc658d1886c305fa435459d3b85f93b60

## FINAL CLASSIFICATION

DISCOVERY_PASS_BASIS_CONVERGENCE

## FROZEN RESULT

- confirmed contracts: 19
- contracts with eligible adjacent pairs: 19
- adjacent daily pairs: 536
- equal-weight mean per-contract signed convergence: +0.5539536981 DVOL points/calendar-day
- median per-contract mean signed convergence: +0.3745959596
- positive contract share: 18/19 = 94.7368%
- pooled pair hit rate: 63.2463%
- nonnegative expiration-quarter means: 7/7
- contract-cluster bootstrap 95% CI: [+0.3729802291, +0.7516595219]

Every frozen sample and statistical gate passed.

One contract, BTCDVOL_USDC-30OCT24, had a negative contract-level mean (-0.0519565). No contract was removed.

## INTERPRETATION

The historical BTCDVOL futures-minus-index basis exhibited robust next-observation convergence toward zero under the prospectively frozen daily sampling rule. This is a mechanism-level result, not yet a tradable-profit result: DVOL index movement can dominate a directional futures position even while the basis converges.

## FIREWALL

transaction costs opened: false
strategy PnL opened: false
strategy returns opened: false
2025 accessed: false
2026 accessed: false
live trading: false
exchange mutation: false
merge to main: false

## CANONICALITY

The earliest run produced after the frozen authority/workflow was created, run 35278588512, is canonical. Any later duplicate branch-push reruns use the same frozen authority but are non-canonical and cannot modify this verdict.

## RELEASE

This PASS authorizes only a separately frozen execution/cost MVE that tests whether the ex-ante basis sign predicts economically positive futures PnL with legitimate post-signal fills and fixed costs. No live trading is authorized.
