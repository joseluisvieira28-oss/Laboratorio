# POB — BRTI OPERATOR HANDOFF V0.1

Date: 2026-09-28
Parent: PREDICTION-ORACLE-BASIS-001
Branch: prediction-oracle-basis-v0.1
Status: READY_FOR_OPERATOR_CREDENTIAL_STEP / NO_SECRET_IN_REPO

## Purpose

Minimize operator ambiguity for the only remaining source-access blocker.

This handoff does not create, rotate, inspect or store credentials. It only defines the exact secure operator step required before the frozen one-shot read-only BRTI probe can be activated.

## Official Kalshi key creation path

Kalshi documentation:
https://docs.kalshi.com/getting_started/api_keys

Operator steps:
1. Log in to the intended Kalshi environment.
2. Open Account & security / Account Settings.
3. Open API Keys.
4. Create a new API key only if the operator intends to authorize this research access.
5. Securely save both:
   - API Key ID
   - RSA private key file

Kalshi states that the private key cannot be retrieved again after the creation page is closed.

## Never place the private key in

- ChatGPT messages;
- Git commits;
- repository files;
- PR descriptions/comments;
- issues;
- workflow logs;
- artifacts;
- shell history when avoidable;
- screenshots.

## GitHub protected-secret names

Repository:
joseluisvieira28-oss/Laboratorio

GitHub Actions repository secrets must be named exactly:

KALSHI_API_KEY_ID
KALSHI_PRIVATE_KEY_PEM

GitHub documentation:
https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets

UI path:
Repository Settings
→ Secrets and variables
→ Actions
→ Secrets
→ New repository secret

KALSHI_API_KEY_ID:
- value = Kalshi Key ID.

KALSHI_PRIVATE_KEY_PEM:
- value = complete RSA private key PEM content, including BEGIN/END lines.

Do not add either value as a GitHub Actions variable. They must be Secrets.

## Existing fail-closed implementation

The source harness already:
- reads only KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY_PEM;
- signs timestamp + GET + /trade-api/v2/cfbenchmarks/values;
- excludes query parameters from the signature;
- uses RSA-PSS SHA-256 / MGF1 SHA-256 / digest-length salt;
- writes the private key only to a temporary chmod-0600 file for OpenSSL;
- deletes the temporary file;
- never prints or persists credential values;
- never calls account, balance, portfolio, position, order, fill, transfer, RFQ or mutation endpoints.

Frozen request:
GET https://external-api.kalshi.com/trade-api/v2/cfbenchmarks/values?id=BRTI

## What happens after both secrets exist

Do NOT immediately run repeated probes.

Next sequence:
1. Verify secret presence only.
2. Create/freeze the explicit activation receipt required by POB_BRTI_READONLY_SOURCE_ACCESS_AUTHORITY_V0.1.
3. Execute exactly one initial authenticated read-only BRTI source request.
4. Persist only metadata/schema/hash/presence fields; do not persist the numeric BRTI value in the initial access receipt.
5. Adjudicate:
   - BRTI_SOURCE_ACCESS_PASS
   - BRTI_AUTH_OR_ENTITLEMENT_BLOCKED
   - BRTI_SOURCE_SCHEMA_UNPROVEN
   - BRTI_SOURCE_TECHNICAL_FAILURE
6. Only after BRTI_SOURCE_ACCESS_PASS may the separate prospective economic protocol be frozen.

## Current state

BRTI_CREDENTIAL_ABSENT / SOURCE_ACCESS_NOT_EXECUTED / NOT_NO_EDGE.

No further operator-independent source attack is currently justified.
