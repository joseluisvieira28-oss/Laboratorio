#!/usr/bin/env python3
"""Fail-closed validator for CRYPTO_LAB_EDGE_CLASSIFICATION_V1.

On pull requests, pass --base and --head. Only newly introduced top-level
labs/<LAB_ID>/ directories are required to contain EDGE_CLASSIFICATION_V1.json.
Existing historical labs are not retroactively blocked by this gate.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ALLOWED_FAMILIES = {
    "TREND", "MR", "CARRY", "RV", "EVENT", "MICRO", "LEADLAG",
    "VOL", "FLOW", "SUPPLY", "MACRO", "CREDIT", "ACCESS",
}
ALLOWED_MATURITY = {f"M{i}" for i in range(9)}
REQUIRED = {
    "schema_version",
    "lab_id",
    "classification_frozen_at_utc",
    "primary_edge_family",
    "mathematical_engine",
    "mechanism_statement",
    "expected_sign_or_payoff_shape",
    "failure_mode",
    "regime_dependency",
    "source_authority",
    "execution_assumptions",
    "protected_holdouts",
    "validation_path",
    "promotion_policy_reference",
    "nearest_existing_family_or_lab",
    "material_difference_from_existing_work",
    "expected_correlation_bucket",
    "maturity",
    "scientific_verdict",
    "governance",
}


def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def new_lab_dirs(base: str, head: str) -> list[Path]:
    changed = sh("git", "diff", "--name-status", base, head, "--", "labs/")
    candidates: set[str] = set()
    for line in changed.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1]
        if not status.startswith("A") or not path.startswith("labs/"):
            continue
        bits = path.split("/")
        if len(bits) >= 2 and bits[1]:
            candidates.add(bits[1])

    result: list[Path] = []
    for lab_id in sorted(candidates):
        probe = subprocess.run(
            ["git", "cat-file", "-e", f"{base}:labs/{lab_id}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if probe.returncode != 0:
            result.append(Path("labs") / lab_id)
    return result


def nonempty_str(obj: dict, key: str) -> bool:
    return isinstance(obj.get(key), str) and bool(obj[key].strip())


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]

    missing = sorted(REQUIRED - set(data))
    if missing:
        errors.append(f"{path}: missing required fields: {', '.join(missing)}")

    if data.get("schema_version") != "CRYPTO_LAB_EDGE_CLASSIFICATION_V1":
        errors.append(f"{path}: schema_version must be CRYPTO_LAB_EDGE_CLASSIFICATION_V1")

    family = data.get("primary_edge_family")
    if family not in ALLOWED_FAMILIES:
        errors.append(f"{path}: primary_edge_family {family!r} not in {sorted(ALLOWED_FAMILIES)}")

    secondary = data.get("secondary_edge_family")
    if secondary is not None and secondary not in ALLOWED_FAMILIES:
        errors.append(f"{path}: secondary_edge_family {secondary!r} not allowed")

    maturity = data.get("maturity")
    if maturity not in ALLOWED_MATURITY:
        errors.append(f"{path}: maturity must be one of M0..M8")

    for key in (
        "lab_id", "classification_frozen_at_utc", "mathematical_engine",
        "mechanism_statement", "expected_sign_or_payoff_shape", "failure_mode",
        "regime_dependency", "validation_path", "promotion_policy_reference",
        "nearest_existing_family_or_lab", "material_difference_from_existing_work",
        "expected_correlation_bucket", "scientific_verdict",
    ):
        if key in data and not nonempty_str(data, key):
            errors.append(f"{path}: {key} must be a non-empty string")

    forensic = data.get("forensic_audit_reference")
    if forensic is not None and (not isinstance(forensic, str) or not forensic.strip()):
        errors.append(f"{path}: forensic_audit_reference must be a non-empty string when supplied")

    source = data.get("source_authority")
    if not isinstance(source, dict):
        errors.append(f"{path}: source_authority must be an object")
    else:
        for key in ("canonical_source", "point_in_time_requirement", "coverage_gate"):
            if not nonempty_str(source, key):
                errors.append(f"{path}: source_authority.{key} must be non-empty")

    execution = data.get("execution_assumptions")
    if not isinstance(execution, dict):
        errors.append(f"{path}: execution_assumptions must be an object")
    else:
        if not isinstance(execution.get("executable_strategy"), bool):
            errors.append(f"{path}: execution_assumptions.executable_strategy must be boolean")
        for key in ("cost_model", "entry_exit"):
            if not nonempty_str(execution, key):
                errors.append(f"{path}: execution_assumptions.{key} must be non-empty")

    if not isinstance(data.get("protected_holdouts"), list):
        errors.append(f"{path}: protected_holdouts must be a list")

    governance = data.get("governance")
    if not isinstance(governance, dict):
        errors.append(f"{path}: governance must be an object")
    else:
        expected = {
            "research_only": True,
            "fail_closed": True,
            "live_trading": False,
            "exchange_mutation": False,
            "post_outcome_tuning": False,
        }
        for key, value in expected.items():
            if governance.get(key) is not value:
                errors.append(f"{path}: governance.{key} must be {value}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    if bool(args.base) != bool(args.head):
        parser.error("--base and --head must be supplied together")

    targets: list[Path] = []
    if args.paths:
        targets = [Path(p) for p in args.paths]
    elif args.base and args.head:
        labs = new_lab_dirs(args.base, args.head)
        for lab in labs:
            classification = lab / "EDGE_CLASSIFICATION_V1.json"
            if not classification.exists():
                print(f"FAIL: new lab {lab} is missing EDGE_CLASSIFICATION_V1.json", file=sys.stderr)
                return 1
            targets.append(classification)
    else:
        targets = sorted(Path("labs").glob("*/EDGE_CLASSIFICATION_V1.json")) if Path("labs").exists() else []

    all_errors: list[str] = []
    for target in targets:
        if not target.exists():
            all_errors.append(f"{target}: file does not exist")
        else:
            all_errors.extend(validate(target))

    if all_errors:
        print("EDGE CLASSIFICATION GATE: FAIL", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"EDGE CLASSIFICATION GATE: PASS ({len(targets)} classification file(s) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
