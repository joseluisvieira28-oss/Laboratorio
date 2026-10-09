# TV Evidence Vault V0.1

Immutable snapshot tooling for the forward evidence chain of
`TV-FOOTPRINT-CALIBRATION-001`.

## Objectives

1. Parse structured `TVFP_RECEIPT` records from Render logs.
2. Recompute and verify every payload SHA256.
3. Reject malformed, pre-boundary, wrong-identity or conflicting receipts.
4. Deduplicate only exact duplicate deliveries by deterministic evidence key.
5. Check 5-minute continuity and report every missing slot.
6. Write a canonical JSONL corpus.
7. Build a per-record SHA256 hash chain and a corpus-level SHA256 manifest.

The vault performs **no market analysis** and computes no future returns.

## Scientific boundary

- Snapshotting does not change the calibration sample.
- Missing bars remain missing; they are never reconstructed from price data.
- Conflicting same-key payloads are a hard failure.
- Deduplication removes transport retries only.
- The vault cannot grant trading authority or sensor authority.

## Daily archival policy

Create one immutable daily snapshot from all available `TVFP_RECEIPT` records
for that UTC day. Do not overwrite a snapshot after publication. A correction
must use a new revision filename and document the reason.

Recommended archive path:

`tradingview_evidence_vault/archive/YYYY-MM-DD/`

Each snapshot consists of:

- `YYYY-MM-DD.jsonl`
- `YYYY-MM-DD.manifest.json`

The final seven-day calibration corpus is assembled from the archived daily
snapshots and re-verified before calibration.
