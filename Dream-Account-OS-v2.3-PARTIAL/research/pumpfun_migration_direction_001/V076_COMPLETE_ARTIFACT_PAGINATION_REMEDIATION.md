# PMD-001 — V0.7.6 COMPLETE ARTIFACT PAGINATION REMEDIATION

Date: 2026-09-20
Status: **SOURCE-ONLY TRANSPORT REMEDIATION / SCIENCE UNCHANGED**

Canonical distributed source run `35320091340` exposes 254 artifacts over three GitHub API pages:
- 252 artifacts named `PMD-001-v074-fullsource-shard-*`;
- shard IDs span 0..252;
- exact missing shard ID: 250;
- shard 250 corresponds to frozen manifest indices 1000..1003.

V0.7.5 run `35389095184` independently recovered those exact four rows successfully, but its remote artifact-pattern download supplied only 200 primary shard artifacts to the stitch job. The resulting 800-row stitch is therefore a transport/pagination failure, not a scientific source verdict.

This amendment authorizes only:
1. enumerate ALL primary artifacts from run 35320091340 using paginated GitHub Actions API;
2. require exactly 252 primary shard artifacts, exactly IDs 0..252 except 250;
3. download all 252 immutable primary artifacts by artifact ID;
4. combine only the already-authorized four V0.7.5 recovery artifacts for indices 1000..1003;
5. rerun unchanged `stitch_chain_exact_source_v074.py`;
6. rerun unchanged `aggregate_chain_exact_source_gate_v074_distributed.py`.

If and only if the unchanged source gate returns `CHAIN_EXACT_SOURCE_GATE_V074_PASS`, the already-authorized V0.12.1 continuation from V0.7.5 may run unchanged.

No source definition, manifest, boundary, feature family, outcome, threshold, split, cost, horizon or promotion authority changes.
No new outcome is opened before source-gate PASS.
No 2025/2026, live trading, orders, wallets, exchange mutation or main merge.
