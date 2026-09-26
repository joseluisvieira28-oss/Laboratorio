# L2R-OVERLAY-ETF-CME-001 — CLOUD SOURCE TRANSPORT AUTHORITY V0.1A

Date: 2026-09-27
Branch: `l2r-overlay-etf-cme-cloud-source-v0.1a`

## PURPOSE

Authorize a transport-only execution path for the already-frozen one-shot development test `L2R-OVERLAY-ETF-CME-001`.

This authority does **not** alter:
- the parent ETF-CME artifact or its SHA256;
- the canonical L2 2025 corpus identity;
- the overlay hypothesis;
- T0 definitions;
- R/Y cell definitions;
- alignment/opposition semantics;
- residual or delay-benefit arithmetic;
- sample gates;
- support gates;
- any protected-period boundary;
- the frozen overlay runner bytes.

## FROZEN IDENTITIES

- parent ETF artifact SHA256:
  `40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`
- parent ETF artifact source id: GitHub Actions artifact `10335473231`
- canonical L2 manifest SHA256:
  `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`
- canonical L2 object count: `8400`
- canonical L2 compressed bytes: `8975275014`
- overlay runner SHA256:
  `495129040193b01218d867bd8a29f50039e5229203d118571f38445746942b2a`

## AUTHORIZED TRANSPORT CHANGE ONLY

Instead of restoring the canonical 2025 L2 corpus from the private Google Drive backup, a GitHub Actions runner may reacquire the same official source bytes directly from the Hyperliquid requester-pays S3 archive by using the already-existing frozen parent acquisition functions:

- `stage_inventory`
- `stage_acquisition`

from:
`research/l2_resiliency/L2R_2025_BTC_VALIDATION_PIPELINE_V01B_FROZEN_SOURCE.py`.

The cloud path must stop fail-closed unless the reacquired manifest is byte-identical to the canonical manifest SHA256 above and the exact object count / compressed-byte totals match.

No schema normalization, validation outcome recomputation, trading result recomputation, or 2026 access is authorized during source transport.

## ONE-SHOT CONSUMPTION RULE

The one-shot is **not consumed** by:
- missing / expired AWS credentials;
- source inventory failure;
- body-acquisition failure;
- manifest SHA mismatch;
- object-count mismatch;
- byte-total mismatch;
- ETF artifact SHA mismatch;
- overlay-runner SHA mismatch;
- dependency / runner setup failure before the frozen overlay runner begins outcome evaluation.

The one-shot **is consumed** once all frozen identities pass and the exact frozen overlay runner begins its 2025 development outcome evaluation.

Its first valid terminal classification is immutable under this lineage:
- `DEVELOPMENT_OVERLAY_SIGNAL_SUPPORTED`
- `DEVELOPMENT_OVERLAY_NO_SUPPORT`
- `DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE`

## FIREWALLS

- 2025 only.
- 2026 closed.
- no live trading.
- no wallet access.
- no exchange mutation.
- no orders.
- no leverage deployment.
- no main merge.
- no post-outcome tuning.
- no cell rescue.
- no threshold rescue.
- no rerun rescue after a valid terminal one-shot classification.

This amendment exists solely to change transport from Drive restore to canonical first-party reacquisition while preserving the exact scientific experiment.
