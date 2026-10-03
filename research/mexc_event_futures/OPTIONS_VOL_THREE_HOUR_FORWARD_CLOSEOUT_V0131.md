# OPTIONS-VOL-FWD-001 — THREE-HOUR FORWARD BATCH CLOSEOUT V0.13.1

Date: 2026-10-03
Status: `INSUFFICIENT_N`
Edge verdict: NONE — no qualifying signal opened.

## Authoritative run

- Workflow: `MEXC V0.13.1 Options Frozen Forward Batch`
- Run: `37100393588`
- Job: `111138613471`
- Head: `4461052c0e58e9ec664d6473e80eaca440936180`
- Artifact: `v0131-options-frozen-forward-batch`
- Artifact id: `11269102793`
- Artifact digest: `sha256:1dfa717faa0081750767ce23eac8f8c3146ed55577f2321c99661db08c3caa7d`

## Frozen rule continuity

Rule hash remained:

`edd02c530398465cb35e481f96e336ebd0dcccc73235aaffe6c1d984c3986517`

Runtime preflight: PASS.

Preflight exact five-second joins:
- BTC_USDT: PASS on attempt 1, join 2990 ms;
- ETH_USDT: PASS on attempt 1, join 185 ms.

No scientific rule was relaxed.

## Forward collection result

- acceptance window: 10800 seconds;
- source rounds: 181;
- BTC valid matched option pairs: 173;
- ETH valid matched option pairs: 177;
- source-round exceptions: 0;
- qualifying frozen signals: 0;
- outcomes opened: 0;
- resolved N: 0;
- statistics run: false;
- final status: `INSUFFICIENT_N`.

Every attempted currency/minute ended `NO_SIGNAL_OR_INVALID_SOURCE`.

## Source-only skew feasibility observation

For valid matched pairs, the frozen signal quantity was:

`skew_pp = put mark_iv - call mark_iv`

Observed in this bounded source window:

### BTC
- valid pairs: 173
- minimum skew: -0.17 pp
- maximum skew: +0.56 pp
- maximum absolute skew: 0.56 pp
- frozen trigger magnitude: 5.0 pp
- trigger hits: 0

### ETH
- valid pairs: 177
- minimum skew: -0.36 pp
- maximum skew: +0.32 pp
- maximum absolute skew: 0.36 pp
- frozen trigger magnitude: 5.0 pp
- trigger hits: 0

This does NOT prove the 5 pp event can never occur and is not a no-edge verdict. It does prove that the original V0.1 rule was extremely inactive in this three-hour forward sample.

The threshold MUST NOT be retrospectively lowered inside V0.1. Any future source-calibrated threshold requires a new family version, a new prospective source-only calibration freeze and a new future boundary before outcomes.

## Safety

- no login;
- no Event Futures order;
- no private/account read;
- no trading;
- no outcome opened.

The Playwright `TargetClosedError` messages emitted during browser teardown occurred after the finalized clean receipt and did not change the run verdict or evidence ledger.
