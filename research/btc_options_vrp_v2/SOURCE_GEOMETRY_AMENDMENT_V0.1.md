# BTC-OPTIONS-VRP-001 V2 — SOURCE GEOMETRY AMENDMENT V0.1
Date: 2026-10-07
Status: FROZEN BEFORE FORWARD OUTCOMES

## Evidence
Current public Deribit source-health run 37659393449 captured 74/74 selected instruments with zero failures.
Artifact 11499987991, digest sha256:28ef9900094ef8c21a56d90a6c0e3caf4e219997140a13d67e970bde9f73fee5.
No returns, PnL, expectancy or future outcomes were computed.

The capture contained 37 same-strike call/put pairs, but zero pairs in the OLD rigid 25–35 DTE interval.
The observed available expiry was approximately 22.6 DTE.

## Scientific correction
The historical BBO MVE remains immutable.
The new V2 FORWARD MVE uses a different, source-robust expiry rule frozen now:

1. active BTC option expiries must be inside 14–60 DTE;
2. choose the expiry minimizing |DTE - 30|;
3. deterministic tie-break: earlier expiry timestamp;
4. within chosen expiry, choose the strike minimizing |ln(strike/index_price)|;
5. require both call and put at that exact expiry/strike;
6. require executable bid size >= 0.1 contract on both entry legs;
7. source timestamps must pass the per-request contemporaneous freshness check;
8. no alternate expiry/strike may be chosen because a later outcome looks better.

This change is permitted because only source geometry was inspected. No V2 forward performance outcome exists.

## Timestamp correction
The legacy collector stamped one common snapshot-start time before sequential API calls. Later book responses can therefore have source timestamps after that common start, creating meaningless negative "ages".

V2 records request_start_ms and response_received_ms for EVERY API call.
Freshness is evaluated at response receipt:
abs(response_received_ms - source_timestamp_ms) <= 30,000 ms.

This is a technical/provenance correction and changes no economic outcome rule.

## Power consequence
Legacy nuisance dispersion is inflated 50%, not 25%, because the V2 expiry geometry differs from the old executable episodes.
Activation target: 36 raw complete cohorts, blind N_eff >=30, planned power >=80%.
