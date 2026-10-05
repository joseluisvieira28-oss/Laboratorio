# Pre-outcome implementation amendment V0.2

Date: 2026-10-05. Classification: FROZEN_PRE_OUTCOME_IMPLEMENTATION_V0_2.

The V0.1 one-shot authority was committed but never consumed. Its first outcome-runner preflight stopped while parsing `parent_state_segment_01.csv.gz`: the previous parser treated `.csv` as part of the numeric segment identifier. The failure occurred before source revalidation completed, before the atomic one-shot marker was created and before any Binance price field was interpreted. The original attempt receipt and a separate boundary audit are committed alongside this amendment.

The runner now uses strict filename binding for `parent_state_segment_<integer>.csv.gz`; a regression test covers valid 01/11 names and rejects a malformed suffix. Eight conformance tests pass. This is an implementation-only correction. Parent semantics, all six cells, RR labels, timestamps, source universe, sample floors, timing tolerances, coverage gates, support rule and bootstrap procedure are unchanged.

The cache LRU correction and segment-name correction are both included in the V0.2 runner hash. The price-blind PASS receipts remain byte-bound and valid. The unused V0.1 authority is superseded; a replacement V0.2 authority must be committed and byte-verified before the sole outcome execution. No price has been opened and the consumed marker is absent.
