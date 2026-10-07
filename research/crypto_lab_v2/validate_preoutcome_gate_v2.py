#!/usr/bin/env python3
"""
Crypto Lab V2 pre-outcome gate validator.
Stdlib-only. Validates semantic invariants that JSON Schema alone does not enforce.
It does NOT open market outcomes and does NOT execute trading actions.
"""
from __future__ import annotations
import json
import pathlib
import sys

REQUIRED_TOP = {
    "schema_version","family_id","economic_class","stage","mechanism",
    "accessibility","source_gate","power_gate","multiplicity","freeze","decision"
}

def fail(msg: str) -> None:
    raise ValueError(msg)

def require_text(obj, key, min_len=3):
    val = obj.get(key)
    if not isinstance(val, str) or len(val.strip()) < min_len:
        fail(f"{key}: missing/too short")
    return val

def validate(path: pathlib.Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED_TOP - set(data)
    if missing:
        fail(f"missing top-level keys: {sorted(missing)}")
    if data["schema_version"] != "2.0":
        fail("schema_version must be 2.0")
    if data["stage"] != "PRE_OUTCOME":
        fail("stage must be PRE_OUTCOME")

    mech = data["mechanism"]
    for k in ("service","risk","persistence_friction","bilateral_rationale","competition_barrier"):
        require_text(mech, k, 5)
    if mech.get("status") not in {"MECHANISM_PASS","MECHANISM_UNSUPPORTED","ACCESSIBILITY_UNRESOLVED"}:
        fail("invalid mechanism.status")

    acc = data["accessibility"]
    for k in ("capture_path","data_access","execution_access","capacity_constraint","estimand","hurdle_units","hurdle_rationale"):
        require_text(acc, k, 3)
    H = acc.get("hurdle_h")
    if not isinstance(H, (int,float)) or H <= 0:
        fail("accessibility.hurdle_h must be > 0")
    if acc.get("status") not in {"ACCESSIBLE_PASS","EDGE_EXISTS_BUT_INACCESSIBLE","ACCESSIBILITY_UNRESOLVED"}:
        fail("invalid accessibility.status")

    src = data["source_gate"]
    for k in ("enumerability_rule","timestamp_rule","treatment_binding"):
        require_text(src, k, 8)
    if src.get("outcome_derived_inclusion") is not False:
        fail("source_gate.outcome_derived_inclusion must be false")
    if not isinstance(src.get("sources"), list) or not src["sources"]:
        fail("source_gate.sources must contain at least one source")
    if src.get("status") not in {"SOURCE_PASS","SOURCE_BLOCKED","DESIGN_INVALID_PRE"}:
        fail("invalid source_gate.status")

    p = data["power_gate"]
    if p.get("outcomes_opened") is not False:
        fail("power_gate.outcomes_opened must be false")
    alpha = p.get("alpha")
    target = p.get("power_target")
    power = p.get("power_at_h")
    n_eff = p.get("n_eff_estimate")
    if not isinstance(alpha, (int,float)) or not (0 < alpha <= 0.2):
        fail("power_gate.alpha must be in (0, 0.2]")
    if not isinstance(target, (int,float)) or not (0.5 <= target <= 0.99):
        fail("power_gate.power_target must be in [0.5, 0.99]")
    if not isinstance(power, (int,float)) or not (0 <= power <= 1):
        fail("power_gate.power_at_h must be in [0,1]")
    if not isinstance(n_eff, (int,float)) or n_eff <= 0:
        fail("power_gate.n_eff_estimate must be > 0; there is deliberately no universal minimum N")

    mult = data["multiplicity"]
    for k in ("economic_hypothesis_id","primary_claim_id","policy"):
        require_text(mult, k, 3)
    if not isinstance(mult.get("trial_index"), int) or mult["trial_index"] < 1:
        fail("multiplicity.trial_index must be >= 1")

    fr = data["freeze"]
    require_text(fr, "frozen_at_utc", 10)
    require_text(fr, "outcome_boundary", 5)
    if fr.get("single_shot") is not True or fr.get("no_rescue") is not True:
        fail("freeze.single_shot and freeze.no_rescue must be true")

    decision = data["decision"]
    if decision == "TEST_AUTHORIZED":
        if mech.get("status") != "MECHANISM_PASS":
            fail("TEST_AUTHORIZED requires MECHANISM_PASS")
        if acc.get("status") != "ACCESSIBLE_PASS":
            fail("TEST_AUTHORIZED requires ACCESSIBLE_PASS")
        if src.get("status") != "SOURCE_PASS":
            fail("TEST_AUTHORIZED requires SOURCE_PASS")
        if p.get("status") != "TEST_AUTHORIZED":
            fail("TEST_AUTHORIZED requires power_gate.status TEST_AUTHORIZED")
        if power < target:
            fail(f"TEST_AUTHORIZED forbidden: power_at_h {power} < target {target}")
    elif decision == "UNDERPOWERED_PRE":
        if power >= target:
            fail("UNDERPOWERED_PRE inconsistent with power_at_h >= target")
    elif decision == "SOURCE_BLOCKED":
        if src.get("status") != "SOURCE_BLOCKED":
            fail("SOURCE_BLOCKED decision requires source_gate.status SOURCE_BLOCKED")
    elif decision == "EDGE_EXISTS_BUT_INACCESSIBLE":
        if acc.get("status") != "EDGE_EXISTS_BUT_INACCESSIBLE":
            fail("inaccessible decision requires matching accessibility.status")
    elif decision != "KILL_PRE":
        fail("invalid decision")

def main() -> int:
    paths = [pathlib.Path(x) for x in sys.argv[1:]]
    if not paths:
        paths = list(pathlib.Path("research").glob("**/PREOUTCOME_GATE_V2.json"))
    if not paths:
        print("CRYPTO_LAB_V2_GATE: no PREOUTCOME_GATE_V2.json files found; nothing to validate")
        return 0
    failed = 0
    for p in paths:
        try:
            validate(p)
            print(f"PASS {p}")
        except Exception as e:
            failed += 1
            print(f"FAIL {p}: {e}", file=sys.stderr)
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
