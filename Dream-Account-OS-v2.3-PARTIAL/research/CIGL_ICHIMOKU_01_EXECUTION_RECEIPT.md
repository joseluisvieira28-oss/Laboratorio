# CIGL-ICHIMOKU-01 — EXECUTION RECEIPT

Authorized by user on 2026-09-13.

Authority: Google Drive document `CIGL-ICHIMOKU-01 — PRE-DISCOVERY IMPLEMENTATION FREEZE — 2026-09-13` (`1VhaxxJ_qnvOi6kKfkImmpB1a9h7eU683W900LX2-6BM`).

Frozen implementation:
- canonical Ichimoku 9 / 26 / 52;
- forward displacement 26 interpreted using only the cloud visible at bar t from raw spans at t-26;
- cloud-breakout signal only;
- primary 1H, robustness-only 4H;
- entry next bar open, hold 4 completed bars;
- costs 10 / 14 bps;
- same six-asset universe;
- no tuning, stacking, coin selection or cost rescue.

Phase firewall:
- execute Discovery 2022-2023 exactly once;
- open 2024 exactly once only if the frozen pooled 1H Discovery gate passes;
- never open 2025 or 2026;
- no live trading;
- no exchange mutation;
- no merge to main.

Freeze commit: `d1780d70e0794f81a77d26ea5bfc7a14f9ee237c`
Runner commit: `9f89bb944b207930eaeb7af035a1093b148b6341`
Workflow commit: `8b3882e7ed287b77f6bc1fd4f053599ac17cf22a`
