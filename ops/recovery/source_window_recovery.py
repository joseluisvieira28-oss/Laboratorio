"""Operational transport only. Frozen scientific collectors are never edited."""
import argparse, json, os, runpy, subprocess
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

US = "Dream-Account-OS-v2.3-PARTIAL/research/us_open_shortvol_fwd_001_collector.py"
AAVE = "Dream-Account-OS-v2.3-PARTIAL/research/aave_hf_crowding_001_calibration.py"
EXPECTED = {"usopen": (US, "7fb57c214b4e8dd250bbb24337d48f4afedf439a"),
            "aave": (AAVE, "3e505b4cc85cbcd25c4e9a5e9e426c5090227eda")}
BRANCHES = {"usopen": "ops/usopen-window-recovery-2026-10-12",
            "aave": "ops/aave-daily-source-recovery-2026-10-12"}

def phase_at(now):
    if now.tzinfo is None:
        raise ValueError("Timezone required")
    local = now.astimezone(ZoneInfo("America/New_York"))
    if local.weekday() >= 5:
        return "NONTRADING_DAY"
    minute = local.hour * 60 + local.minute
    if 540 <= minute <= 550:
        return "ENTRY"
    if 660 <= minute <= 670:
        return "EXIT"
    return "OUTSIDE_FROZEN_WINDOWS"

def checked_source(mode):
    path, expected = EXPECTED[mode]
    actual = subprocess.check_output(["git", "hash-object", path], text=True).strip()
    if actual != expected:
        raise RuntimeError("FROZEN_COLLECTOR_IDENTITY_MISMATCH")
    return path

def terminal_already_recorded(mode):
    if mode == "usopen":
        path = Path("Dream-Account-OS-v2.3-PARTIAL/runtime/usopen_shortvol_fwd_001/ledger.json")
        terminals = {"FORWARD_SHADOW_SHORTVOL_SURVIVES", "FORWARD_SHADOW_SHORTVOL_NO_EDGE"}
    else:
        path = Path("Dream-Account-OS-v2.3-PARTIAL/runtime/aave_hf_crowding_001_calibration/ROLLUP.json")
        terminals = {"HF_CROWDING_Q90_READY_TO_FREEZE"}
    return path.exists() and json.loads(path.read_text())["classification"] in terminals

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=EXPECTED, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REF_NAME") != BRANCHES[args.mode]:
        raise RuntimeError("RECOVERY_BRANCH_REQUIRED")
    source = checked_source(args.mode)
    now = datetime.now(timezone.utc)
    os.environ.pop("FORCE_PHASE", None)
    if terminal_already_recorded(args.mode):
        print(json.dumps({"status": "TERMINAL_ALREADY_RECORDED_NO_REOPEN", "mode": args.mode}))
        return
    if args.mode == "usopen" and phase_at(now) not in {"ENTRY", "EXIT"}:
        print(json.dumps({"status": "NOOP_OUTSIDE_FROZEN_WINDOWS", "received_utc": now.isoformat()}))
        return
    runpy.run_path(source, run_name="__main__")
    print(json.dumps({"status": "ORIGINAL_COLLECTOR_RETURNED",
                      "mode": args.mode, "original_collector_blob": EXPECTED[args.mode][1],
                      "orders": False, "science_changed": False}))

if __name__ == "__main__":
    main()
