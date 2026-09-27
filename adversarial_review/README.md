# Crypto Lab Adversarial Review System V0.1

This directory implements an additive, fail-closed scientific review layer for Crypto Lab candidates.

## Lifecycle

`FREEZE -> BLUE -> RED -> REFEREE -> FORWARD -> PROMOTION GATE`

This system does **not** replace the canonical Crypto Lab candidate registry, Promotion Policy V3, Diamond Test governance, candidate-specific freezes, sealed holdouts, or any stricter earlier authority.

## Roles

- **Blue Team** builds the strongest valid case for the frozen candidate: provenance, exact replication, costs, robustness, OOS/holdout compliance, execution feasibility, forward integrity and evidence-chain quality.
- **Red Team** attempts falsification using the frozen adversarial matrix. It must record PASS when a valid attack fails to break the candidate and may not tune a rescue.
- **Referee** checks authority, independence, coverage and rule compliance. It does not change strategy science.

## Anti-rescue invariant

After outcome access, changing a threshold, direction, horizon, universe, feature, sample floor, cost model, event filter or other scientific identity creates a **new candidate/version**. The current candidate receives no rescue credit from the diagnostic that inspired the change.

Purely technical repairs may remain in-line only when they cannot change scientific meaning, candidate selection or outcome interpretation and are independently documented.

## Fail-closed boundary

This layer never grants authority for:

- live trading or capital deployment;
- orders or authenticated exchange mutation;
- wallets, transfers or leverage changes;
- opening sealed holdouts;
- production activation;
- merge to `main`.

Those require separate controlling authority.

## Files

- `adversarial_matrix_v0_1.json` — permanent Blue/Red review matrix.
- `review_bundle_schema_v0_1.json` — portable bundle contract.
- `tools/validate_review_bundle.py` — zero-dependency fail-closed validator.
- `tests/test_validate_review_bundle.py` — policy regression tests.
- `pilots/BNB-LAUNCHPOOL-DEMAND-001/` — first registered pilot.
