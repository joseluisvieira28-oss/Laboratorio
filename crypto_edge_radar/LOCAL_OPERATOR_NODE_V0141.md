# LOCAL OPERATOR NODE V0.14.1 — RESILIENT SEVEN-MOTOR BOOTSTRAP

Status: **RESEARCH / PUBLIC SHADOW ONLY — NO CAPITAL — NO ORDERS**

Build: `v0.14.1-win-seven-motor-resilient-bootstrap`
Registry: **3.6**
Motors: **7**

## Why V0.14.1 exists

V0.14 correctly protected the scientific and execution boundaries, but its Windows bootstrap still invoked a legacy single-provider MEXC local-node preflight before the multi-motor cockpit was served. A DH03 clock failure or that legacy MEXC preflight could therefore terminate the process before `127.0.0.1:8787` became available, hiding the exact blocker behind a generic localhost timeout.

V0.14.1 changes only operational bootstrap and diagnostics.

## Corrected architecture

The cockpit is always served on loopback once the packaged registry passes.

Each research component then owns its fail-closed state:
- DH03 clock preflight failure => DH03 BLOCKED / collector not started / activation boundary not persisted.
- Five-engine forward supervisor failure => affected local forward runtime BLOCKED.
- Render sentinel failure => sentinel state visible in the cockpit.
- Registry desync => control plane REGISTRY_DESYNC.

One public source failure no longer blacks out diagnostics for unrelated motors.

The legacy MEXC single-provider `local-node` preflight is not used to gate the seven-motor Windows cockpit. This does not weaken any strategy source gate, cost model, timing rule, or execution rule.

## Scientific invariants

Unchanged:
- registry 3.6 identities and scientific classifications;
- all assets, timeframes, directions, thresholds and costs;
- all forward activation boundaries;
- DH03 pre-arming Binance clock budget: absolute offset <=500ms and RTT <=1000ms;
- no reconstruction of missed DH03 exact-minute paths;
- CED1D remains external T+3;
- no automatic Tier1 or micro-live;
- no authenticated exchange API, orders, wallets, exchange mutation or capital.

## Expected local states

Healthy:
- control room reachable at http://127.0.0.1:8787;
- registry 3.6 / 7 of 7 loaded;
- forward supervisor RUNNING + forward health OK;
- DH03 BOOTSTRAPPING then COLLECTING;
- Render sentinel RUNNING and OK (or explicit review state);
- no focus motor BLOCKED.

If a motor fails, the cockpit remains reachable and exposes the exact status/error.
