# CRYPTO EDGE RADAR — RUNTIME HARDENING HANDOFF V0.5

V0.4 is frozen as the passed Render canary baseline.

Baseline code commit: `06ce0a381280e2c4af3eedcd71dbdd5d7a170d45`  
Canary closeout commit: `24812cf96c70b71c5af07819b43d75eda42f7819`  
Canary verdict: `CANARY_PASS / NOT_DURABLE_24_7_READY`

V0.5 scope is infrastructure-only:

- add durable remote evidence-store option;
- preserve SQLite for local/CI fallback;
- fail closed when configured remote persistence is unavailable;
- pin runtime compatibility;
- preserve PUBLIC_SHADOW_ONLY and zero exchange mutation;
- no strategy/science changes;
- no main merge;
- no authenticated exchange APIs;
- no live orders.

Free Render Postgres validation datastore created in Frankfurt:
`dpg-dalqi4qd0e5s738a77kg-a`

It expires on `2026-10-17T08:47:15Z`; therefore it is a 30-day validation/soak datastore, not permanent production storage.
