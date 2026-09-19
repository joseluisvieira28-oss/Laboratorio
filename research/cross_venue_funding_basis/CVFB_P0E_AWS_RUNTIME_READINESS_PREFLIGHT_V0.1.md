# CVFB P0E — AWS RUNTIME READINESS PREFLIGHT V0.1

Date: 2026-09-19
Branch: `cross-venue-funding-basis-provenance-v0.5`
Status: **FROZEN PRE-EXECUTION / ZERO-S3 / ZERO-COST**

## Purpose

Determine whether the existing frozen CVFB P0E requester-pays probe is operationally ready to execute, without making any AWS S3 request and without exposing credential material.

This preflight is not P0E execution and does not authorize or perform source access.

## Exact checks

1. The immutable P0E requester-pays authorization amendment exists and pins freeze blob:
   `3f4e3a43636ea9a17a1c9cbc60e25410bff6a6fe`.
2. The authorization amendment retains:
   - requester-pays charges authorized = true;
   - AWS credentials authorized = true;
   - execution authorized = true;
   - economic outcomes authorized = false;
   - primary replication reopened = false;
   - 2026 authorized = false.
3. The frozen P0E runner compiles.
4. The existing zero-S3 synthetic guard suite passes.
5. Repository/runtime secrets are checked only for non-empty presence:
   - `CVFB_P0E_AWS_ACCESS_KEY_ID`
   - `CVFB_P0E_AWS_SECRET_ACCESS_KEY`
   - `CVFB_P0E_AWS_SESSION_TOKEN` is optional.
6. No secret value, length, prefix, hash or derived identifier may be printed.

## Hard prohibitions

- no boto3/S3 client creation;
- no AWS API call;
- no requester-pays request;
- no source object listing/HEAD/GET;
- no raw historical object access;
- no market numeric values;
- no economic outcomes;
- no 2026 data;
- no live trading, wallet, exchange mutation or main merge.

## Terminal states

- `P0E_RUNTIME_READY`: mandatory access-key and secret-key secrets are present and all zero-S3 guards pass.
- `P0E_RUNTIME_CREDENTIALS_MISSING`: one or both mandatory secrets are absent.
- `P0E_PREFLIGHT_GUARD_FAILURE`: authorization/freeze/synthetic guard fails.

Only `P0E_RUNTIME_READY` means the already-frozen manual P0E workflow is operationally triggerable. It does not itself execute P0E.
