# Deribit V3 — isolated cloud evidence test

This branch is a **staging-only** destination for synthetic dry-run storage checks.
No Deribit public market requests, real trades, or prospective sessions are authorized here.
Every synthetic receipt must declare `prospective_v3=false`, `net_pnl=null`, and `orders=0`.
Never use this branch for the 20-session cohort or as an economics source.
