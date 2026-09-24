# OPENMARKET PIN RECEIPT V0.1

Date: 2026-09-24
Lab: INFORMATION-PROPAGATION-GRAPH-001

## Source code pin

PASS

- repository: gregyoung14/openmarket
- release/tag: v0.5.2
- exact commit: 6e6cc240f32ab9fd2f8fa602bd0aba823b24bfee
- release title: OpenMarket v0.5.2 public launch integrity release

The release/public record identifies v0.4.3-unified as the recommended deduplicated dataset and documents 727,098,247 rows / 202 snapshots.

## Dataset pin

BLOCKED_EXACT_REVISION

- dataset: gregyoung14/openmarket-btc-polymarket
- semantic version: v0.4.3-unified
- public dataset card requires reporting the Hugging Face dataset revision used.
- a full immutable revision hash corresponding unambiguously to the intended v0.4.3-unified corpus has not yet been proven in this gate.
- current/main UI commit identifiers are not accepted as a substitute unless the exact immutable revision is recorded and its content manifest reconciles.

## Consequence

Do NOT execute the OpenMarket negative-control experiment yet.

Allowed:
- source-code method review pinned to 6e6cc240f32ab9fd2f8fa602bd0aba823b24bfee;
- dataset metadata inspection;
- revision discovery.

Not allowed:
- claim reproduction PASS;
- compute timing/forecast results and call them canonical;
- silently use Hugging Face main.

Verdict: SOURCE_CODE_PIN_PASS / DATASET_REVISION_BLOCKED.
