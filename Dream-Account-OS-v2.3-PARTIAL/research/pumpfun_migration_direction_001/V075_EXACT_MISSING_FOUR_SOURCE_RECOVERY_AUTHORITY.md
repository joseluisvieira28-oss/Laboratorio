# PMD-001 — V0.7.5 EXACT MISSING-FOUR SOURCE RECOVERY AUTHORITY

Date: 2026-09-18
Branch: `pumpfun-migration-direction-v0.1`
Status: **FROZEN BEFORE RECOVERY / SOURCE-ONLY TRANSPORT REMEDIATION**

## Trigger evidence

Canonical distributed full-source run `35320091340` reconstructed 1,008 of the frozen 1,012 manifest rows.

Its frozen V0.7.4 Source Gate receipt recorded:

- manifest rows: 1,012;
- returned rows: 1,008;
- unique mints: 1,008;
- source-complete rows: 1,003;
- feature-source-eligible rows: 1,003;
- minimum eligible rows: 1,000;
- eligible dates: 20 / minimum 20;
- malformed inputs: 0;
- duplicate mints: 0;
- field mismatches: 0;
- outcome wall intact: true;
- verdict: `CHAIN_EXACT_SOURCE_GATE_V074_TECHNICAL_INCOMPLETE`.

The missing evidence corresponds to the single matrix shard starting at manifest index 1000 with limit 4. That job received a runner shutdown/cancel signal. It did not produce a scientific/sample verdict.

Exact missing mints reported by the canonical Source Gate:

1. `2etvNMkNGKFqA1esxAq374wvTzrc2qr7kDXrh8tVpump`
2. `4BTVAptSHkq6gCZTDNPVBUitCz1eYuJkp7BYu3heXnmm`
3. `4mS3sL2HSmPZ8Emv9JXsqeWN1JH2mnZMkQrTDJGRpump`
4. `JB7GpuvEWq9L2aF6oPJRM1149wugdA7HfNd85gAjpump`

## Frozen recovery

Recover **only** manifest indices 1000, 1001, 1002 and 1003, each as an independent one-row source job using the existing frozen runner:

`source_rebuild_chain_exact_v07.py`

Unchanged:
- exact 1,012-row manifest and SHA256;
- exact V0.7 migrate + migrate_v2 boundary semantics;
- exact pre-boundary source window;
- block-first chain-exact source;
- public Solana RPC route;
- source-complete / feature-source-eligible definitions;
- >=1,000 eligible row threshold;
- >=20 eligible-date threshold;
- no missing-as-zero;
- no mint substitution;
- no window widening;
- no population/split changes.

Before source access, the rebuilt manifest MUST prove that indices 1000..1003 map exactly to the four missing mints above. Any mismatch fails closed.

## Stitch rule

After all four exact rows complete, combine:
- immutable primary distributed artifacts from run `35320091340`;
- only these four new one-row recovery artifacts.

Use the existing `stitch_chain_exact_source_v074.py`.

PASS requires:
- exactly 1,012 stitched summary rows;
- exactly 1,012 unique frozen mints;
- no identity/boundary conflicts;
- no unexpected mint;
- no missing mint;
- complete raw source evidence for every retained mint;
- all source rows remain outcome-blind.

Then rerun the **unchanged** `aggregate_chain_exact_source_gate_v074_distributed.py`.

This authority does not pre-judge PASS. The existing gate remains the sole adjudicator.

## Conditional V0.12.1 continuation

Only if the exact Source Gate returns `CHAIN_EXACT_SOURCE_GATE_V074_PASS`:

1. extract the already-frozen V0.12 feature family using the V0.12.1 official-IDL quote-aware decoder;
2. preserve W30/W60/W300 and all completeness semantics unchanged;
3. evaluate with the V0.12.1 eligibility plumbing and the already-opened frozen V0.8 exploratory outcomes;
4. apply the already-frozen BH-FDR, chronological-third, quintile and leave-largest-winner robustness gates.

Permitted terminal research labels remain:
- `V012_REPLICATION_CANDIDATE`;
- `V012_NO_ROBUST_FEATURE_SIGNAL`;
- `V012_DECODER_OR_SAMPLE_INSUFFICIENT`.

No V0.12/V0.12.1 result can directly become an edge, diamond, live setup or production strategy because V0.8 outcomes were already opened before this replication-candidate stage.

## Firewalls

- no new outcome definition;
- no new outcome horizon;
- no threshold tuning;
- no feature-family expansion;
- no favorable subgroup selection;
- no cost rescue;
- no live trading;
- no orders/wallets/exchange mutation;
- no merge to main.
