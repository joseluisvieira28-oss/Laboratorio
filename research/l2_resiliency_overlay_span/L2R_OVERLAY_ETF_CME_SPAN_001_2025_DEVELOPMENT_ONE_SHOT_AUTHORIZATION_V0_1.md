# L2R-OVERLAY-ETF-CME-SPAN-001 — 2025 DEVELOPMENT ONE-SHOT AUTHORIZATION V0.1

Date: 2026-09-27
Status: **AUTHORIZED — EXACTLY ONE VALID 2025 SPAN DEVELOPMENT RUN**

## Bound identity

LAB_ID: `L2R-OVERLAY-ETF-CME-SPAN-001`

Protocol freeze:
`396992a03d67a4a960445acbd9b17b7a21171994`

Source/sample preflight:
`f59d584c195b9e6f78c78f32d9cd96450d98b8cb`

Implementation lock:
`d9cc256611e3d6583af716a03b4495fc0d242bea`

Runner SHA256:
`e3b965e3c072deb1aeeb18e7000ccb266786b484bcdeea3e5082e17cd552382a`

Implementation QA:
- Python AST parse: PASS
- Python compile/exec: PASS
- synthetic self-test: PASS
- exact UTF-8 SHA256 independently reproduced: PASS

ETF-CME immutable parent artifact:
- Actions run: `34815006815`
- artifact ID: `10335473231`
- SHA256: `40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`

L2 canonical 2025 manifest:
`767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`

## Authorization

Exactly one valid outcome-bearing execution of the frozen SPAN V0.1 runner is authorized against:
1. the exact immutable ETF-CME OOS 2025 artifact above; and
2. the exact already-open canonical L2 2025 corpus above.

The first valid resulting evidence bundle becomes the immutable V0.1 SPAN development outcome regardless of sign or classification.

A technical failure before any valid evidence bundle is produced may be repaired only if the correction is implementation-only, documented, re-QA'd and re-locked before another attempt.

## Frozen interpretation

2025 is **DEVELOPMENT ONLY** for this combined identity.

The R->Y span:
- may begin before ETF T0;
- ends after T0 by construction;
- is a causal state/response compatibility diagnostic;
- is NOT executable ETF entry PnL;
- is NOT independent OOS;
- cannot by itself promote the overlay or either parent.

## Frozen sample gate

Per cell:
- selected total >= 10;
- ALIGNED >= 3;
- OPPOSED >= 3.

Global:
- source-present ETF parent rows >= 40;
- at least 4/6 viable cells;
- each R family (R1/R5/R15) has >=1 viable cell.

Known pre-outcome inventory:
- R1_Y5 total selected = 6 => sample-insufficient by construction;
- R1_Y15 = 22;
- R1_Y60 = 38;
- R5_Y15 = 10;
- R5_Y60 = 34;
- R15_Y60 = 26.
Class balance and span-return signs were not opened before this authorization.

## Frozen directional gate

`DEVELOPMENT_SPAN_SIGNAL_SUPPORTED` only if:
1. global sample viability passes;
2. equal-weight separation across viable cells > 0;
3. at least 4 viable cell separations > 0;
4. R1/R5/R15 each have >=1 positive viable cell;
5. equal-weight ALIGNED mean PARENT_SPAN_BPS > 0;
6. equal-weight OPPOSED mean PARENT_SPAN_BPS < 0.

Otherwise, with valid sample:
`DEVELOPMENT_SPAN_NO_SUPPORT`.

If sample/source viability fails:
`DEVELOPMENT_SPAN_INSUFFICIENT_SAMPLE_OR_SOURCE`.

## No rescue after valid outcome

Do not:
- choose the best cell;
- drop a losing viable cell;
- change sample minimums;
- change RR threshold;
- change R/Y horizons;
- change active-event selection;
- change parent direction/horizon;
- use ETF seven-day PnL to tune the overlay;
- reinterpret span response as fill PnL;
- open 2026;
- switch venue inside this LAB_ID;
- rerun with modified rules.

## Firewalls

2026: **CLOSED**

No:
- orders;
- live trading;
- exchange mutation;
- wallet mutation;
- leverage/sizing change;
- production deployment;
- main merge.

PR #122 remains **DRAFT / NO MERGE**.
