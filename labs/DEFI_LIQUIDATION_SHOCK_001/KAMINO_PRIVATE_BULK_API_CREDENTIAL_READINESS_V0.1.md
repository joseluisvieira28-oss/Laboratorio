# DEFI-LIQUIDATION-SHOCK-001 — KAMINO PRIVATE BULK API CREDENTIAL READINESS V0.1

Date: 2026-09-22
Status: SOURCE-ONLY / ZERO-REQUEST / SECRET-PRESENCE ONLY

Purpose: determine whether the existing GitHub Actions environment already contains credentials that could authorize the official Kamino bulk market-transactions endpoint.

Official endpoint under evaluation:
POST /v3/kamino-market/{pubkey}/transactions

The Kamino OpenAPI marks this endpoint as private and requiring Basic Auth. This readiness check MUST NOT call Kamino, print/hash/transform any secret value, create credentials, create accounts, or contact Kamino for access.

It may test only whether candidate repository secret names are empty/non-empty.

Candidate names:
- KAMINO_API_USERNAME
- KAMINO_API_PASSWORD
- KAMINO_USERNAME
- KAMINO_PASSWORD
- KAMINO_BASIC_AUTH
- KAMINO_API_AUTH
- KAMINO_API_KEY

A credential-presence result is only transport readiness. It does not authorize outcome access and does not grant SOURCE_DATA_PASS.
