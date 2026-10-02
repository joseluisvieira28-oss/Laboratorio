# OPTIONS XRP — HISTORICAL STRIKE ENCODING AMENDMENT 01

Date: 2026-10-02
Status: FROZEN BEFORE SOURCE-GATE RERUN
Type: TECHNICAL PARSER AMENDMENT ONLY

## Evidence

The outcome-blind source-format diagnostic on 2024-03-12 observed canonical historical XRP option names such as:

- XRP_USDC-13MAR24-0d645-P
- XRP_USDC-29MAR24-0d7-C
- XRP_USDC-29MAR24-1-C

The token `d` is a decimal marker in these historical XRP strike strings.

## Frozen parser correction

For XRP_USDC option instrument names only:

- strike token containing exactly one `d` is normalized by replacing `d` with `.`;
- the resulting token must parse as a finite positive float;
- strike tokens without `d` continue to parse normally;
- any other malformed strike token fails closed.

Examples:

- `0d645` -> 0.645
- `0d7` -> 0.7
- `1` -> 1.0

No other field is changed.

## Scientific invariants

This correction changes no DTE band, moneyness band, IV aggregation, signal sign, horizon, outcome definition, cost, risk rule or pass/fail threshold.

No skew, signal, forward return or PnL was inspected to derive this amendment.

The previous XRP SOURCE_GATE_FAIL_DATA from the generic-float parser is therefore classified as TECHNICAL_PARSER_BLOCKED, not as a scientific source rejection.

The source gate must now be rerun from the committed parser amendment.
