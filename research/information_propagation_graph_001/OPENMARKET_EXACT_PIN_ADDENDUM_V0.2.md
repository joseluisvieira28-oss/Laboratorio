# OPENMARKET EXACT PIN ADDENDUM V0.2

Date: 2026-09-24
Lab: INFORMATION-PROPAGATION-GRAPH-001
Stage: SOURCE / NEGATIVE-CONTROL PREP

This addendum is additive. It does not rewrite the earlier receipt that correctly
recorded DATASET_REVISION_BLOCKED before the immutable Hugging Face revision
was resolved.

## Exact pins

OpenMarket source repository:
- repository: gregyoung14/openmarket
- exact source commit: 6e6cc240f32ab9fd2f8fa602bd0aba823b24bfee
- release family observed in source receipt: v0.5.2

OpenMarket synchronized dataset:
- repository: gregyoung14/openmarket-btc-polymarket
- semantic dataset version: v0.4.3-unified
- requested verified short revision: 7450246
- resolved immutable Hugging Face SHA: 74502466d1a7cef56395bfd8d0b465fbebc849cf
- files/siblings reported by API at this revision: 4253
- last_modified reported: 2026-07-31T02:05:24Z

## Verdict

SOURCE_CODE_PIN_PASS
DATASET_REVISION_PIN_PASS
OPENMARKET_NEGATIVE_CONTROL_SOURCE_PIN_READY

This authorizes only bounded method/clock negative-control work already defined
in OPENMARKET_NEGATIVE_CONTROL_V0.1.md.

It does NOT authorize:
- IPG predictive promotion;
- threshold rescue;
- ML V0.1;
- live trading;
- main merge.

No market outcome from IPG-001 was opened by resolving this pin.
