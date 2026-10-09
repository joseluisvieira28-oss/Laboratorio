# SOURCE-FIRST SAMPLE CEILING — GOVERNANCE REPAIR V0.1
Date: 2026-10-09
Trigger: LOR-RLE-001 sample gate `37/100` failed AFTER one-time Discovery script had already computed and logged descriptive returns, although its receipt declared `economic_gate_unlocked=false`.
Incident: https://github.com/joseluisvieira28-oss/Laboratorio/blob/research/lorenz-rle-001-science-2026-10-09/audits/LOR_RLE_001_SAMPLE_GATE_CLOSEOUT_2026-10-09.md

## Rule
Before starting any **economic outcome resolver**:
1. Commit the source-only contract and freeze with immutable SHA-256 binding.
2. In an isolated source-only process, build candidate event counts and dates entirely from information available at signal time (not future prices, return fields, stop/target achievements or exit fills).
3. Run `source_first_sample_gate_v01.py` on that count-only receipt.
4. If any group's raw signal count is less than its frozen minimum count of **executed trades**, terminally stop without downloading/resolving outcomes. Executed N can never exceed raw signal N.
5. If raw counts pass, **do not automatically unlock outcomes**. Execute a separate, causal entry eligibility and date span census with strictly same pre-outcome boundary and lock; then create a new, explicit authorized outcome-only receipt after all sample/source/date gates pass.
6. No weakening sample floors, recategorizing previously opened data as pristine, or moving underpowered groups to a winning subgroup.

## Scope and caveats
- The reusable gate is a *necessary upper-bound check*, never sufficient approval for the economic run.
- It does not independently prove the upstream producer is causal, complete or truthful; SHA-256 must be calculated and attested by an independent source-only workflow.
- This governance repair does NOT sanitize the previous RLE metric exposure, reset opened 2022-24 outcomes, change Lorenz hypotheses, or authorize opening 2025/2026.
- `LOR-RLE-001` is CLOSED UNDERPOWERED; this generic tool is for future non-duplicative research hypotheses only.
- No trading or exchange mutation.

## Reproducible test
`PYTHONPATH=governance python -m unittest -v governance/test_source_first_sample_gate_v01.py`.
All synthetic fixtures, no prices, no private data.
