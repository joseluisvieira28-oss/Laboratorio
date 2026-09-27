#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

BLUE = {"PASS", "FAIL", "INCONCLUSIVE", "BLOCKED"}
RED = {"SURVIVES", "CHALLENGED", "FALSIFIED", "BLOCKED"}
REF = {"PROCESS_PASS", "PROCESS_FAIL", "BLOCKED", "NEW_VERSION_REQUIRED"}
ATTACK_RESULTS = {"PASS", "FAIL", "CHALLENGE", "BLOCKED", "NOT_APPLICABLE"}

BOUNDARIES = (
    "live_trading_authorized",
    "main_merge_authorized",
    "exchange_mutation_authorized",
    "sealed_holdout_open_authorized",
)

FREEZE_FIELDS = (
    "complete",
    "mechanism",
    "failure_mode",
    "controlling_authority",
    "source_manifest",
    "code_commit",
    "parameters",
    "entry_exit_rules",
    "cost_model",
    "protected_periods",
    "promotion_gates",
    "scientific_identity_changed_after_outcome_access",
)

def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)

def nonempty(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True

def validate(bundle, matrix):
    errors = []

    for key in ("candidate", "freeze", "blue", "red", "referee", "boundaries", "evidence"):
        if key not in bundle:
            errors.append(f"missing top-level field: {key}")

    if errors:
        return errors

    candidate = bundle["candidate"]
    for key in ("id", "version"):
        if not nonempty(candidate.get(key)):
            errors.append(f"candidate.{key} is required")

    freeze = bundle["freeze"]
    for key in FREEZE_FIELDS:
        if key not in freeze or not nonempty(freeze.get(key)):
            if key in ("complete", "scientific_identity_changed_after_outcome_access") and key in freeze:
                continue
            errors.append(f"freeze.{key} is required")

    blue = bundle["blue"]
    if blue.get("verdict") not in BLUE:
        errors.append("invalid blue.verdict")
    if not isinstance(blue.get("checks"), list):
        errors.append("blue.checks must be a list")

    red = bundle["red"]
    if red.get("verdict") not in RED:
        errors.append("invalid red.verdict")
    if red.get("attack_plan_prepared_before_blue_conclusion_review") is not True:
        errors.append("red attack plan independence gate failed")

    attacks = red.get("attacks")
    if not isinstance(attacks, list):
        errors.append("red.attacks must be a list")
        attacks = []

    by_id = {}
    for attack in attacks:
        aid = attack.get("id")
        if aid in by_id:
            errors.append(f"duplicate red attack: {aid}")
            continue
        by_id[aid] = attack
        result = attack.get("result")
        if result not in ATTACK_RESULTS:
            errors.append(f"{aid}: invalid result")
        if result == "NOT_APPLICABLE" and not nonempty(attack.get("reason")):
            errors.append(f"{aid}: NOT_APPLICABLE requires reason")
        if result in {"PASS", "FAIL", "CHALLENGE"} and not nonempty(attack.get("evidence_ref")):
            errors.append(f"{aid}: evidence_ref required for {result}")

    mandatory = {x["id"] for x in matrix["red_attacks"] if x.get("mandatory")}
    missing = sorted(mandatory - set(by_id))
    for aid in missing:
        errors.append(f"missing mandatory red attack: {aid}")

    referee = bundle["referee"]
    if referee.get("verdict") not in REF:
        errors.append("invalid referee.verdict")
    if referee.get("higher_precedence_authority_reconciled") is not True:
        errors.append("higher-precedence authority not reconciled")

    boundaries = bundle["boundaries"]
    for key in BOUNDARIES:
        if boundaries.get(key) is not False:
            errors.append(f"{key} must be false in adversarial-review authority")

    if freeze.get("scientific_identity_changed_after_outcome_access") is True:
        if referee.get("verdict") != "NEW_VERSION_REQUIRED":
            errors.append("post-outcome scientific change requires NEW_VERSION_REQUIRED")

    if referee.get("verdict") == "PROCESS_PASS":
        if freeze.get("complete") is not True:
            errors.append("PROCESS_PASS requires freeze.complete=true")
        if blue.get("verdict") != "PASS":
            errors.append("PROCESS_PASS requires BLUE PASS")
        if red.get("verdict") not in {"SURVIVES", "CHALLENGED"}:
            errors.append("PROCESS_PASS requires RED SURVIVES or CHALLENGED")
        for attack in attacks:
            if attack.get("result") == "BLOCKED" and attack.get("id") in mandatory:
                errors.append(f"PROCESS_PASS forbidden with blocked mandatory attack: {attack.get('id')}")
            if attack.get("result") == "FAIL" and attack.get("hits_frozen_failure_gate") is True:
                errors.append(f"PROCESS_PASS forbidden after frozen-gate failure: {attack.get('id')}")

    if not isinstance(bundle["evidence"], list) or not bundle["evidence"]:
        errors.append("evidence must contain at least one immutable reference")

    return errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("bundle")
    p.add_argument("--matrix", default=str(Path(__file__).resolve().parents[1] / "adversarial_matrix_v0_1.json"))
    args = p.parse_args()

    try:
        bundle = load_json(args.bundle)
        matrix = load_json(args.matrix)
    except Exception as exc:
        print(f"BLOCKED: cannot read input: {exc}", file=sys.stderr)
        return 2

    errors = validate(bundle, matrix)
    if errors:
        print("ADVERSARIAL REVIEW VALIDATION: FAIL_CLOSED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("ADVERSARIAL REVIEW VALIDATION: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
