"""Fail-closed cloud wrapper for Deribit V3 public quote collection.

Not a scheduler. No orders, exchange keys, PnL or network in dry-run mode.
Evidence must live in ONE Git evidence branch, restored before each invocation.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

UTC = dt.timezone.utc
BRANCH = "evidence/deribit-v3-forward"
REL = Path("research/deribit_v3_microstructure/forward_evidence")
V3 = Path(__file__).resolve().parent


def canonical(data):
    return (json.dumps(data, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def immutable(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


def utc_now():
    return dt.datetime.now(UTC)


def phase(at):
    if at.tzinfo is None:
        raise ValueError("NAIVE_CLOCK")
    at = at.astimezone(UTC)
    start = dt.datetime.combine(at.date(), dt.time(8, 5), UTC)
    if at < start:
        return "BEFORE"
    if at >= start + dt.timedelta(minutes=5):
        return "MISSED_WINDOW"
    return "OPEN"


def clock_gate(clock=utc_now, sleeper=time.sleep, max_wait_seconds=190):
    """Never use old quotes; wait only if runner began near the frozen window."""
    first = clock().astimezone(UTC)
    start = dt.datetime.combine(first.date(), dt.time(8, 5), UTC)
    if first < start:
        delay = (start - first).total_seconds()
        if delay > max_wait_seconds:
            raise ValueError("TOO_EARLY_FOR_BOUNDED_WAIT")
        sleeper(delay)
    current = clock().astimezone(UTC)
    return current, phase(current)


def _check_attempt(folder):
    receipt_path = folder / "receipt.json"
    manifest_path = folder / "manifest.json"
    if not receipt_path.is_file() or not manifest_path.is_file():
        raise ValueError("INCOMPLETE_ATTEMPT_REQUIRES_RECONCILIATION")
    receipt = json.loads(receipt_path.read_bytes())
    manifest_raw = manifest_path.read_bytes()
    if sha(manifest_raw) != receipt.get("manifest_sha256"):
        raise ValueError("MANIFEST_TAMPER")
    manifest = json.loads(manifest_raw)
    if len(manifest) > 4 or len(set(m["name"] for m in manifest)) != len(manifest):
        raise ValueError("INVALID_SOURCE_MANIFEST")
    for item in manifest:
        name = item["name"]
        if name not in {"index", "instruments", "call", "put"}:
            raise ValueError("DISALLOWED_MANIFEST_SOURCE")
        raw_path = folder / (name + ".json")
        if "sha256" in item:
            if not raw_path.is_file() or sha(raw_path.read_bytes()) != item["sha256"] or raw_path.stat().st_size != item["bytes"]:
                raise ValueError("RAW_SOURCE_TAMPER")
        elif raw_path.exists():
            raise ValueError("UNHASHED_SOURCE")
    if receipt.get("net_pnl") is not None or receipt.get("orders") != 0 or receipt.get("live_go") is not False:
        raise ValueError("UNEXPECTED_TRADING_ECONOMICS")
    if receipt.get("status") == "TECHNICAL_PASS":
        if {m["name"] for m in manifest} != {"call", "put", "index", "instruments"} or any(
                "sha256" not in m for m in manifest):
            raise ValueError("INCOMPLETE_SUCCESSFUL_SOURCES")
        if receipt.get("mode") != "prospective" or receipt.get("prospective_v3") is not True or receipt.get("valid_technical") is not True:
            raise ValueError("INVALID_FORWARD_CLASSIFICATION")
    return receipt


def verify_existing(root):
    """Preflight restored cohort, fail closed on incomplete or altered evidence."""
    prospective = root / "prospective"
    if not prospective.exists():
        return 0
    claims = {p.stem for p in prospective.glob("*.claim")}
    attempts = [p for p in prospective.iterdir() if p.is_dir()]
    day_count = {}
    valid = 0
    for folder in attempts:
        receipt = _check_attempt(folder)
        day = receipt.get("session_utc")
        if day not in claims or not folder.name.startswith(day + "-"):
            raise ValueError("UNCLAIMED_ATTEMPT")
        day_count[day] = day_count.get(day, 0) + 1
        if day_count[day] > 1:
            raise ValueError("DUPLICATE_DAY_ATTEMPT")
        if receipt.get("prospective_v3") is True:
            valid += 1
    if claims != set(day_count):
        raise ValueError("ORPHAN_DAY_CLAIM")
    if valid > 20:
        raise ValueError("EXCESS_VALID_COHORT")
    return valid


def _git(repo, *args):
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError("GIT_FAILURE: " + " ".join(args[:2]) + ": " + proc.stderr.strip()[:350])
    return proc.stdout.strip()


def publish(repo, evidence_dir, label, branch=BRANCH):
    """Only commits forward_evidence; non-fast-forward push fails, never forces."""
    repo = Path(repo).resolve()
    if _git(repo, "symbolic-ref", "--short", "HEAD") != branch:
        raise ValueError("WRONG_EVIDENCE_BRANCH")
    if not (repo / REL).resolve() == Path(evidence_dir).resolve():
        raise ValueError("WRONG_EVIDENCE_ROOT")
    _git(repo, "add", "--", str(REL))
    staged = _git(repo, "diff", "--cached", "--name-only").splitlines()
    if not staged or any(not p.startswith(REL.as_posix() + "/") for p in staged):
        raise ValueError("NO_EVIDENCE_OR_STAGED_FOREIGN_FILES")
    _git(repo, "commit", "-m", "evidence: Deribit V3 " + label)
    local = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "origin", "HEAD:refs/heads/" + branch)
    remote = _git(repo, "ls-remote", "--heads", "origin", branch).split()
    if not remote or remote[0] != local:
        raise ValueError("EVIDENCE_REMOTE_ANCHOR_MISMATCH")
    return local


def execute(evidence_checkout, mode, clock=utc_now, sleeper=time.sleep, publish_fn=publish):
    """No automatic execution: caller must explicitly choose dryrun/prospective."""
    repo = Path(evidence_checkout).resolve()
    if _git(repo, "status", "--porcelain"):
        raise ValueError("DIRTY_EVIDENCE_CHECKOUT")
    if _git(repo, "symbolic-ref", "--short", "HEAD") != BRANCH:
        raise ValueError("WRONG_EVIDENCE_BRANCH")
    root = repo / REL
    root.mkdir(parents=True, exist_ok=True)
    prior = verify_existing(root)
    if mode == "dryrun":
        at = clock().astimezone(UTC)
        dest = root / "dryrun" / (at.strftime("%Y%m%dT%H%M%S%f") + ".json")
        immutable(dest, canonical(dict(kind="SYNTHETIC_STORAGE_TEST", at=at.isoformat(),
                                        prospective_v3=False, net_pnl=None, orders=0)))
        label = "dryrun"
        result = dict(mode=mode, prospective_v3=False, valid_sessions=prior, net_pnl=None, live_go=False)
    elif mode == "prospective":
        if prior >= 20:
            return dict(status="COHORT_COMPLETE", valid_sessions=prior, prospective_v3=False)
        at, status = clock_gate(clock, sleeper)
        if status == "BEFORE":
            raise ValueError("CLOCK_STILL_BEFORE_FROZEN_WINDOW")
        if status == "MISSED_WINDOW":
            path = root / "missed_windows" / (at.date().isoformat() + ".json")
            immutable(path, canonical(dict(status=status, utc=at.isoformat(),
                                           prospective_v3=False, orders=0, net_pnl=None)))
            label = "missed " + at.date().isoformat()
            result = dict(mode=mode, status=status, prospective_v3=False, valid_sessions=prior, live_go=False)
        else:
            sys.path.insert(0, str(V3))
            import collector
            attempt, receipt = collector.collect(root, mode="prospective", clock=clock)
            label = "capture " + at.date().isoformat()
            result = dict(mode=mode, status=receipt["status"], prospective_v3=receipt["prospective_v3"],
                          valid_sessions=prior + int(receipt["prospective_v3"]),
                          attempt=str(attempt.relative_to(root)), live_go=False, net_pnl=None)
            verify_existing(root)
    else:
        raise ValueError("INVALID_MODE")
    result["evidence_commit"] = publish_fn(repo, root, label)
    result["persistence"] = "PUSH_AND_REMOTE_SHA_VERIFIED"
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--evidence-checkout", required=True)
    p.add_argument("--mode", required=True, choices=["dryrun", "prospective"])
    args = p.parse_args()
    print(json.dumps(execute(args.evidence_checkout, args.mode), indent=2))
