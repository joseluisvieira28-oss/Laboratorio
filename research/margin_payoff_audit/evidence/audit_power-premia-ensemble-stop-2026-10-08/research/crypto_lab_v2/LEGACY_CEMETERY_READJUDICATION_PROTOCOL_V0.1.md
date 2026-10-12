# CRYPTO LAB V2 — LEGACY CEMETERY READJUDICATION PROTOCOL
Date: 2026-10-07
Status: TRIAGE-ONLY / NO RETROACTIVE PROMOTION

## Objective
Find legacy families that may have been mislabeled by V1 because:
- the design was underpowered for the economically relevant effect;
- the effect may have existed gross but failed only on execution/cost assumptions;
- source failure was confused with scientific failure;
- an inconclusive result was recorded as NO_EDGE.

This protocol must never manufacture a survivor from old outcomes.

## Step 1 — Freeze the legacy record
For each family capture:
- branch/commit;
- original hypothesis and direction;
- original source gate;
- original sample and clustering;
- original cost model;
- original primary metric;
- original verdict;
- whether any holdout/forward data remain untouched.

## Step 2 — Classify the old evidence
A. LEGACY_NEGATIVE_VALID_AT_H
Only if the old record supports an economically meaningful H and can exclude that H with defensible uncertainty.

B. LEGACY_NEGATIVE_POWER_UNKNOWN
Negative conclusion exists but no defensible ex-ante power/MDE/H record exists.

C. UNDERPOWERED_SUSPECT
Old confidence/uncertainty is wide enough that an operable H could not have been excluded.
This is triage only.

D. EXECUTION_BLOCKED
Gross mechanism/effect was supported but realizable net effect failed under the actual accessible cost/execution model.

E. SOURCE_BLOCKED
The treatment/signal/provenance could not be reconstructed defensibly.

F. MECHANISM_UNSUPPORTED
A non-price first-stage premise failed (e.g. the supposedly forced flow did not actually occur).

G. FORWARD_RETEST_CANDIDATE
May be assigned only as a priority label. It is NOT SURVIVES.

## Step 3 — Ranking criteria for new-data retest
Use legacy outcomes only to prioritize. Useful triage features:
- old result could not exclude H;
- strong first-stage/mechanism evidence;
- high attrition caused low N_eff;
- predicted sign was reasonably stable across independent clusters;
- a materially cheaper/realistic execution path now exists;
- enough genuinely new events are expected to accumulate in a reasonable horizon;
- untouched forward/venue/time data still exist.

Do not use a favorable old point estimate as confirmatory evidence.

## Step 4 — Re-entry rule
A legacy family can re-enter only through a NEW V2 pre-outcome gate.
Required:
- economic mechanism/accessibility PASS;
- source PASS;
- power PASS or UNDERPOWERED_PRE banking;
- new multiplicity ledger entry;
- untouched/genuinely new data boundary;
- no post-hoc parameter rescue.

## Step 5 — What not to do
Forbidden:
- rename an old failed subset and treat it as new;
- optimize H after seeing legacy returns;
- choose the new horizon because the old curve looked good there;
- exclude bad events that were originally eligible;
- promote an old candidate directly to micro-live.

## Initial audit priority
Priority is methodological, not a claim of edge:
1. legacy event studies with very small independent-event counts;
2. families killed mainly by cost/execution assumptions later shown to be unrealistic;
3. families with a valid first-stage but wide outcome uncertainty;
4. weak but mechanistically distinct signals that could enter a pre-registered ensemble;
5. source-blocked families ONLY if genuinely new provenance now exists.

The output of the cemetery audit is a reclassification ledger, not a survivor list.
