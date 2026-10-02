# MEXC EVENT FUTURES LAB — PROSPECTIVE PRODUCT COLLECTOR V0.12 CLOSEOUT

Date: 2026-10-03
Status: COLLECTOR VALIDATED / FORWARD-ONLY
Verdict: `PROSPECTIVE_SNAPSHOT_PASS`

## Authoritative hardened run

- Workflow: `MEXC Event Futures Prospective Product V0.12`
- Run: `37071442675`
- Job: `111051579379`
- Head: `879b6dcaba86e60409ccef8c8b880ae7e805cca7`
- Artifact: `mexc-event-futures-prospective-product-v012`
- Artifact id: `11254878424`
- Artifact digest: `sha256:fe6310800bde18d6644452c49c87b02dea54adac13b2b632f855f7067574adac`
- Exact detail source body SHA-256: `fef1f0c5501ac154e332938fc0bbab601582758d4e035f9d59841eae03fee9cd`
- Observation time: `2026-10-02T22:15:23.989405Z`

## Validation result

The hardened forward collector captured:

- 9 products;
- 32 product-cycle rows;
- exact `upPayRate` / `downPayRate`;
- product state and contract id;
- min/max investment amounts;
- precision metadata;
- source URL and source hash;
- deterministic break-even probabilities `1/(1+payout)`.

All schema assertions passed.

Safety assertions:

- NO_AUTH = PASS
- NO_ORDERS = PASS
- NO_MUTATION = PASS
- NO_PRIVATE = PASS
- GET_ONLY_TRANSMITTED = PASS

## Race-condition correction

The first V0.12 attempt failed closed with `BLOCKED_DETAIL_SCHEMA` because the page can emit more than one matching detail response and the original handler accepted the first HTTP 200 before requiring a valid JSON product body.

This was an implementation race, not a scientific/source failure.

The hardened collector now records detail-response candidates and accepts a capture only when all of the following are true:

- HTTP 200;
- JSON object;
- `success == true`;
- non-empty `data` product list.

Invalid/empty duplicate responses no longer terminate the capture.

## Scientific boundary

This PASS validates the exact-product forward collector only.

It does NOT prove:

- any directional edge;
- any payout mispricing;
- any historical payout sequence;
- exact hypothetical entry/target price at an arbitrary decision timestamp;
- exact expiry-label generation;
- any trading authorization.

The V0.12 forward boundary remains in force. Failed pre-validation attempts are diagnostic evidence and are not backfilled into the prospective dataset.

## Next dependency before Event-Conditioned Edge

For a defensible exact-product outcome label, the lab must bind Event Futures to an exact public index-price stream.

The live Event Futures bundle already shows that the Event Futures page subscribes to:

- `sub.event.contract`
- `sub.index.price` for the current Event Futures symbol

and listens to `push.index.price`.

MEXC's public Futures websocket documentation independently documents `sub.index.price` / `push.index.price` as a public index-price stream.

The next source gate should therefore prove a read-only public index-price capture and preserve source timestamps before V0.13 begins outcome evaluation.
