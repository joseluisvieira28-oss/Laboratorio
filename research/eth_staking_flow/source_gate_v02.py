#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SOURCE_REPO = "https://github.com/etheralpha/validatorqueue-com.git"
TARGET_COMMIT = "4d6d9604a9aa4a126cedbc8c8cabff5295fffc8e"
START_DATE = date(2023, 5, 21)
END_DATE = date(2024, 12, 31)
EXPECTED_DAYS = (END_DATE - START_DATE).days + 1
EXPECTED_DAYS_FROZEN = 591
OUT = Path("eth_staking_flow_v02_source_gate_out")
CLONE = Path("_validatorqueue_source_repo")


@dataclass(frozen=True)
class QueuePair:
    entry: int
    exit: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(*args: str, cwd: Path | None = None) -> str:
    p = subprocess.run(
        list(args), cwd=str(cwd) if cwd else None, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return p.stdout


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


def expected_dates() -> list[date]:
    return [START_DATE + timedelta(days=i) for i in range(EXPECTED_DAYS)]


def int_nonnegative(v: object, label: str) -> int:
    if isinstance(v, bool):
        raise ValueError(f"{label}: bool is not a validator count")
    if isinstance(v, int):
        x = v
    elif isinstance(v, float) and v.is_integer():
        x = int(v)
    else:
        raise ValueError(f"{label}: not integer-like")
    if x < 0:
        raise ValueError(f"{label}: negative")
    return x


def load_json_bytes(data: bytes) -> list[dict]:
    obj = json.loads(data.decode("utf-8"))
    if not isinstance(obj, list):
        raise ValueError("historical_data.json top-level is not a list")
    return obj


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    receipt: dict = {
        "family_id": "ETH-STAKING-FLOW-001",
        "mve_id": "ESF-NETQUEUE-SNAPSHOT-7D-002",
        "phase": "SOURCE_DATA_GATE_ONLY",
        "target_source_repo": SOURCE_REPO,
        "target_source_commit": TARGET_COMMIT,
        "source_window_start": START_DATE.isoformat(),
        "source_window_end": END_DATE.isoformat(),
        "expected_daily_rows": EXPECTED_DAYS_FROZEN,
        "price_values_opened": False,
        "signal_series_computed": False,
        "discovery_event_count_computed": False,
        "returns_computed": False,
        "pnl_computed": False,
        "performance_statistics_computed": False,
        "access_2025": False,
        "access_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
    }
    manifest: dict = {"files": {}}

    try:
        if EXPECTED_DAYS != EXPECTED_DAYS_FROZEN:
            raise RuntimeError("Frozen expected-day count drift")

        if CLONE.exists():
            shutil.rmtree(CLONE)
        run("git", "clone", "--quiet", "--no-tags", SOURCE_REPO, str(CLONE))
        run("git", "checkout", "--quiet", TARGET_COMMIT, cwd=CLONE)
        resolved = run("git", "rev-parse", "HEAD", cwd=CLONE).strip()
        if resolved != TARGET_COMMIT:
            raise RuntimeError(f"Pinned commit mismatch: {resolved}")

        snapshot_path = CLONE / "historical_data.json"
        build_path = CLONE / "build.py"
        workflow_path = CLONE / ".github" / "workflows" / "update_validator_data.yml"
        for p in (snapshot_path, build_path, workflow_path):
            if not p.is_file():
                raise RuntimeError(f"Pinned provenance file missing: {p}")

        snapshot_bytes = snapshot_path.read_bytes()
        build_bytes = build_path.read_bytes()
        workflow_bytes = workflow_path.read_bytes()
        snapshot = load_json_bytes(snapshot_bytes)

        # Preserve exact pinned public source bytes.
        shutil.copy2(snapshot_path, OUT / "historical_data.pinned.json")
        shutil.copy2(build_path, OUT / "build.pinned.py")
        shutil.copy2(workflow_path, OUT / "update_validator_data.pinned.yml")

        for name, data in (
            ("historical_data.pinned.json", snapshot_bytes),
            ("build.pinned.py", build_bytes),
            ("update_validator_data.pinned.yml", workflow_bytes),
        ):
            manifest["files"][name] = {"bytes": len(data), "sha256": sha256_bytes(data)}

        # Semantics must be fixed by the pinned source code, not inferred from current code.
        build_text = build_bytes.decode("utf-8")
        workflow_text = workflow_bytes.decode("utf-8")
        required_build_tokens = [
            'queue_data["beaconchain_entering"]',
            'queue_data["beaconchain_exiting"]',
            'datetime.now(timezone.utc).strftime',
            'if date != all_data[-1][\'date\']',
            'all_data.append(todays_data)',
        ]
        missing_build_tokens = [t for t in required_build_tokens if t not in build_text]
        if missing_build_tokens:
            raise RuntimeError(f"Pinned build semantics drift: {missing_build_tokens}")
        if "cron: '*/6 * * * *'" not in workflow_text:
            raise RuntimeError("Pinned workflow cadence drift")
        if "git add historical_data.json" not in workflow_text:
            raise RuntimeError("Pinned workflow does not persist historical_data.json")

        # Snapshot coverage/schema audit. No market prices are present or accessed.
        by_date: dict[date, QueuePair] = {}
        duplicate_dates: list[str] = []
        for idx, row in enumerate(snapshot):
            if not isinstance(row, dict):
                raise ValueError(f"row {idx}: not object")
            d = parse_date(str(row.get("date")))
            if d.year >= 2025:
                raise RuntimeError(f"Protected-period row present in pinned snapshot: {d}")
            if d in by_date:
                duplicate_dates.append(d.isoformat())
                continue
            entry = int_nonnegative(row.get("entry_queue"), f"{d}.entry_queue")
            exit_ = int_nonnegative(row.get("exit_queue"), f"{d}.exit_queue")
            by_date[d] = QueuePair(entry=entry, exit=exit_)

        exp = expected_dates()
        missing = [d.isoformat() for d in exp if d not in by_date]
        extra_before = sorted(d.isoformat() for d in by_date if d < START_DATE)
        extra_after = sorted(d.isoformat() for d in by_date if d > END_DATE)
        window_dates = sorted(d for d in by_date if START_DATE <= d <= END_DATE)

        receipt.update({
            "snapshot_total_rows": len(snapshot),
            "window_unique_rows": len(window_dates),
            "window_first_date": window_dates[0].isoformat() if window_dates else None,
            "window_last_date": window_dates[-1].isoformat() if window_dates else None,
            "duplicate_dates": duplicate_dates,
            "missing_dates": missing,
            "extra_dates_before_window_count": len(extra_before),
            "extra_dates_after_window_count": len(extra_after),
            "snapshot_sha256": sha256_bytes(snapshot_bytes),
            "build_sha256": sha256_bytes(build_bytes),
            "workflow_sha256": sha256_bytes(workflow_bytes),
        })

        if duplicate_dates or missing:
            receipt["status"] = "DATA_FAILURE"
            receipt["reason"] = "Frozen daily coverage failed"
            raise AssertionError(receipt["reason"])
        if len(window_dates) != EXPECTED_DAYS_FROZEN:
            receipt["status"] = "DATA_FAILURE"
            receipt["reason"] = "Frozen row count failed"
            raise AssertionError(receipt["reason"])
        if window_dates[0] != START_DATE or window_dates[-1] != END_DATE:
            receipt["status"] = "DATA_FAILURE"
            receipt["reason"] = "Frozen window boundary failed"
            raise AssertionError(receipt["reason"])

        # Full Git-history point-in-time audit through the pinned commit.
        log_text = run(
            "git", "log", "--reverse", "--format=%H%x09%cI", TARGET_COMMIT,
            "--", "historical_data.json", cwd=CLONE,
        )
        commits: list[tuple[str, datetime]] = []
        for line in log_text.splitlines():
            if not line.strip():
                continue
            sha, iso = line.split("\t", 1)
            ts = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
            commits.append((sha, ts))

        first_seen: dict[date, tuple[datetime, QueuePair, str]] = {}
        mutated_after_first: list[str] = []
        parseable_versions = 0
        for sha, commit_ts in commits:
            try:
                raw = subprocess.run(
                    ["git", "show", f"{sha}:historical_data.json"],
                    cwd=str(CLONE), check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                ).stdout
                rows = load_json_bytes(raw)
            except Exception:
                continue
            parseable_versions += 1
            current: dict[date, QueuePair] = {}
            for row in rows:
                if not isinstance(row, dict) or "date" not in row:
                    continue
                try:
                    d = parse_date(str(row["date"]))
                except Exception:
                    continue
                if d < START_DATE or d > END_DATE:
                    continue
                try:
                    pair = QueuePair(
                        entry=int_nonnegative(row.get("entry_queue"), f"{d}.entry_queue"),
                        exit=int_nonnegative(row.get("exit_queue"), f"{d}.exit_queue"),
                    )
                except Exception:
                    continue
                current[d] = pair

            for d, pair in current.items():
                if d not in first_seen:
                    first_seen[d] = (commit_ts, pair, sha)
                elif pair != first_seen[d][1]:
                    mutated_after_first.append(d.isoformat())

        missing_first_seen = [d.isoformat() for d in exp if d not in first_seen]
        wrong_publication_day = []
        for d in exp:
            if d not in first_seen:
                continue
            commit_ts = first_seen[d][0]
            if commit_ts.date() != d:
                wrong_publication_day.append({
                    "source_date": d.isoformat(),
                    "first_commit_utc": commit_ts.isoformat(),
                    "first_commit_sha": first_seen[d][2],
                })

        receipt.update({
            "history_commits_touching_source_file": len(commits),
            "history_parseable_versions": parseable_versions,
            "history_dates_first_seen": len(first_seen),
            "missing_first_seen_dates": missing_first_seen,
            "mutated_after_first_dates": sorted(set(mutated_after_first)),
            "wrong_publication_day": wrong_publication_day,
        })

        if missing_first_seen or mutated_after_first or wrong_publication_day:
            receipt["status"] = "PROVENANCE_FAILURE"
            receipt["reason"] = "Append-only point-in-time Git provenance failed"
            raise AssertionError(receipt["reason"])

        receipt["status"] = "SOURCE_DATA_PASS"
        receipt["reason"] = "Pinned public snapshot passed coverage, schema, daily-publication and append-only provenance gates"
        return_code = 0

    except subprocess.CalledProcessError as exc:
        receipt.setdefault("status", "SOURCE_ACQUISITION_TECHNICAL_FAILURE")
        receipt.setdefault("reason", f"External Git acquisition command failed: {exc.cmd}")
        return_code = 2
    except AssertionError:
        return_code = 3
    except Exception as exc:
        receipt.setdefault("status", "PROVENANCE_FAILURE")
        receipt.setdefault("reason", f"Fail-closed exception: {type(exc).__name__}: {exc}")
        return_code = 4
    finally:
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
        (OUT / "source_manifest.json").write_bytes(manifest_bytes)
        receipt["source_manifest_sha256"] = sha256_bytes(manifest_bytes)
        receipt_bytes = json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8")
        (OUT / "source_gate_receipt.json").write_bytes(receipt_bytes)
        print(json.dumps(receipt, indent=2, sort_keys=True))

    return return_code


if __name__ == "__main__":
    sys.exit(main())
