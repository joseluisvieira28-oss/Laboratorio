# POB — BRTI PARSER + BOUNDARY HARDENING V0.1

Date: 2026-09-28
Parent: PREDICTION-ORACLE-BASIS-001
Branch: prediction-oracle-basis-v0.1
Status: TECHNICAL_HARDENING / SYNTHETIC_ONLY / NO_ECONOMICS

## Purpose

Harden the source-access path before any legitimate authenticated BRTI request exists.

No hypothesis, threshold, market selection, payoff rule, source identity or economic criterion is changed.

## Parser risk found

The previous generic source parser could satisfy the finite-numeric test from an unrelated numeric field elsewhere in a JSON response. It also did not accept numeric BRTI values represented as strings.

Both behaviours are unsafe for a fail-closed source gate.

## Remediation

The source parser now requires BRTI identity, a timestamp and a finite index value to occur in the same observation branch.

Accepted value forms are finite numbers or finite numeric strings under explicit value-like keys.

The parser also supports the documented structural form in which a benchmark observation is carried as JSON text inside a data field.

HTTP 401/403 remain AUTH_OR_ENTITLEMENT_BLOCKED.
Other non-2xx states, including 503, classify as SOURCE_TECHNICAL_FAILURE rather than credential failure.

## Adversarial synthetic parser cases

PASS cases:
- direct BRTI observation with numeric string value;
- wrapped BRTI value_usd observation;
- BRTI identity encoded as a map key;
- embedded raw JSON BRTI observation.

FAIL cases:
- BRTI identity + timestamp + unrelated status code;
- numeric value belonging to a different index record;
- NaN value.

These tests use no network and no real credential.

## One-cent boundary safety test

Frozen authority requires:
- Polymarket: strict > nominal strike;
- Kalshi: threshold encoded one cent below displayed nominal strike;
- classification: MATCHED_HOURLY_STRIKE_TIME_REFERENCE_DIFF_TIE_1C;
- never EXACT_EXCEPT_ORACLE.

Synthetic cent-grid cases preserve the critical mismatch:
- one cent below nominal: both NO;
- exactly nominal: Polymarket NO, Kalshi YES;
- one cent above nominal: both YES.

This is only a semantic safety test. It is not evidence of profitability, arbitrage or predictive edge.

## CI

A dedicated synthetic-only workflow runs:
- RSA signing self-test;
- parser adversarial fixtures;
- one-cent boundary semantics fixtures;
- firewall checks proving zero network requests, zero quote comparison, zero outcomes, zero economics and zero orders.

## Scientific state

UNCHANGED:
BRTI_CREDENTIAL_ABSENT / SOURCE_ACCESS_NOT_EXECUTED / NOT_NO_EDGE.

The hardening prevents false PASS and protects the later one-shot source gate. It does not advance the scientific verdict.
