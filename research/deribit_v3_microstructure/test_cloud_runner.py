"""Offline cloud staging tests. Uses a local bare Git remote, never Deribit."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import cloud_runner as r

UTC = dt.timezone.utc
DAY = dt.datetime(2026, 11, 9, 8, 6, tzinfo=UTC)

def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

def repo(tmp):
    base = Path(tmp)
    bare = base / "remote.git"
    work = base / "working"
    git(base, "init", "--bare", str(bare))
    git(base, "init", "-b", r.BRANCH, str(work))
    git(work, "config", "user.name", "Cloud Test")
    git(work, "config", "user.email", "cloud-test@example.invalid")
    git(work, "remote", "add", "origin", str(bare))
    (work / "README").write_text("evidence branch only\n")
    git(work, "add", "README")
    git(work, "commit", "-m", "test evidence bootstrap")
    git(work, "push", "origin", "HEAD:refs/heads/" + r.BRANCH)
    return work, bare

def add_receipt(root, day="2026-11-09", valid=True):
    prospect = root / "prospective"
    prospect.mkdir(parents=True, exist_ok=True)
    (prospect / (day + ".claim")).write_bytes(r.canonical(dict(day=day)))
    path = prospect / (day + "-fixture")
    path.mkdir()
    manifest = []
    for name in ("call", "put", "index", "instruments"):
        body = r.canonical(dict(testnet=False, result=dict(fixture=True)))
        (path / (name + ".json")).write_bytes(body)
        manifest.append(dict(name=name, bytes=len(body), sha256=r.sha(body)))
    data = r.canonical(manifest)
    (path / "manifest.json").write_bytes(data)
    (path / "receipt.json").write_bytes(r.canonical(dict(
        manifest_sha256=r.sha(data), session_utc=day, status="TECHNICAL_PASS" if valid else "INVALID_ATTEMPT",
        mode="prospective", prospective_v3=valid, valid_technical=valid,
        live_go=False, net_pnl=None, orders=0)))
    return path

class CloudRunnerTests(unittest.TestCase):
    def test_frozen_window_edges(self):
        for at, expected in [(DAY.replace(minute=4, second=59), "BEFORE"),
                             (DAY.replace(minute=5), "OPEN"),
                             (DAY.replace(minute=9, second=59), "OPEN"),
                             (DAY.replace(minute=10), "MISSED_WINDOW")]:
            self.assertEqual(r.phase(at), expected)
        with self.assertRaisesRegex(ValueError, "NAIVE_CLOCK"):
            r.phase(DAY.replace(tzinfo=None))

    def test_bounded_wait_and_late_fail_closed(self):
        ticks = iter([DAY.replace(minute=2), DAY.replace(minute=5)])
        delays = []
        at, status = r.clock_gate(lambda: next(ticks), delays.append)
        self.assertEqual(status, "OPEN")
        self.assertEqual(delays, [180])
        with self.assertRaisesRegex(ValueError, "TOO_EARLY"):
            r.clock_gate(lambda: DAY.replace(hour=7))
        self.assertEqual(r.clock_gate(lambda: DAY.replace(minute=11))[1], "MISSED_WINDOW")

    def test_dryrun_push_survives_fresh_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, bare = repo(tmp)
            result = r.execute(work, "dryrun", clock=lambda: DAY)
            self.assertEqual(result["persistence"], "PUSH_AND_REMOTE_SHA_VERIFIED")
            self.assertFalse(result["prospective_v3"])
            self.assertEqual(result["valid_sessions"], 0)
            fresh = Path(tmp) / "fresh"
            git(tmp, "clone", "-b", r.BRANCH, str(bare), str(fresh))
            files = list((fresh / r.REL / "dryrun").glob("*.json"))
            self.assertEqual(len(files), 1)
            self.assertEqual(json.loads(files[0].read_bytes())["prospective_v3"], False)
            self.assertEqual(git(work, "rev-parse", "HEAD"), result["evidence_commit"])

    def test_late_run_never_contacts_market(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, _ = repo(tmp)
            with patch("collector.collect", side_effect=AssertionError("MARKET_FORBIDDEN")):
                result = r.execute(work, "prospective", clock=lambda: DAY.replace(minute=10))
            self.assertEqual(result["status"], "MISSED_WINDOW")
            self.assertFalse(result["prospective_v3"])
            self.assertEqual(len(list((work / r.REL / "prospective").glob("*.claim"))), 0)
            self.assertEqual(len(list((work / r.REL / "missed_windows").glob("*.json"))), 1)

    def test_restored_attempt_tamper_and_orphan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = add_receipt(root)
            self.assertEqual(r.verify_existing(root), 1)
            (path / "manifest.json").write_text("tamper")
            with self.assertRaisesRegex(ValueError, "MANIFEST_TAMPER"):
                r.verify_existing(root)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "prospective").mkdir()
            (Path(tmp) / "prospective" / "2026-11-09.claim").write_text("{}")
            with self.assertRaisesRegex(ValueError, "ORPHAN_DAY_CLAIM"):
                r.verify_existing(Path(tmp))

    def test_invalid_attempt_kept_and_does_not_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            add_receipt(root, valid=False)
            self.assertEqual(r.verify_existing(root), 0)
            (root / "prospective" / "2026-11-09-fixture" / "receipt.json").unlink()
            with self.assertRaisesRegex(ValueError, "INCOMPLETE_ATTEMPT"):
                r.verify_existing(root)

    def test_wrong_branch_and_dirty_checkout_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, _ = repo(tmp)
            (work / "new.txt").write_text("untracked")
            with self.assertRaisesRegex(ValueError, "DIRTY_EVIDENCE"):
                r.execute(work, "dryrun", clock=lambda: DAY)
            (work / "new.txt").unlink()
            git(work, "checkout", "-b", "do-not-use")
            with self.assertRaisesRegex(ValueError, "WRONG_EVIDENCE_BRANCH"):
                r.execute(work, "dryrun", clock=lambda: DAY)

    def test_push_conflict_not_marked_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, bare = repo(tmp)
            other = Path(tmp) / "other"
            git(tmp, "clone", "-b", r.BRANCH, str(bare), str(other))
            git(other, "config", "user.name", "Cloud Test")
            git(other, "config", "user.email", "cloud-test@example.invalid")
            (other / "race").write_text("remote advanced")
            git(other, "add", "race")
            git(other, "commit", "-m", "concurrent update")
            git(other, "push", "origin", "HEAD:refs/heads/" + r.BRANCH)
            with self.assertRaisesRegex(RuntimeError, "GIT_FAILURE"):
                r.execute(work, "dryrun", clock=lambda: DAY)

    def test_refuses_twenty_or_more_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, _ = repo(tmp)
            root = work / r.REL
            for i in range(20):
                day = (DAY.date() - dt.timedelta(days=i+1)).isoformat()
                add_receipt(root, day=day)
            self.assertEqual(r.verify_existing(root), 20)
            git(work, "add", str(r.REL))
            git(work, "commit", "-m", "fixture complete")
            result = r.execute(work, "prospective", clock=lambda: DAY)
            self.assertEqual(result["status"], "COHORT_COMPLETE")
            self.assertNotIn("evidence_commit", result)

    def test_staging_branch_cannot_collect_market(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, _ = repo(tmp)
            with self.assertRaisesRegex(ValueError, "PROSPECTIVE_REQUIRES_PRODUCTION_BRANCH"):
                r.execute(work, "prospective", clock=lambda: DAY,
                          branch="evidence/deribit-v3-staging-2026-11-09")

    def test_exclusive_day_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            add_receipt(root)
            with self.assertRaises(FileExistsError):
                r.immutable(root / "prospective" / "2026-11-09.claim", b"replace")

if __name__ == "__main__":
    unittest.main()
