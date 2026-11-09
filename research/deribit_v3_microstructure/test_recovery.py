"""Failure injection with local Git remotes and synthetic quotes only."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import cloud_runner as r
import recovery
import test_cloud_runner as git_fixture
import test_collector as fixture
import v3_archive_audit


class RecoveryTests(unittest.TestCase):
    def fixture_attempt(self, root):
        path, _ = fixture.CollectorTests().run_attempt(root)
        day = fixture.T.date().isoformat()
        r.immutable(root / 'reservations' / (day + '.json'), r.canonical(
            dict(day=day, status='RESERVED_BEFORE_MARKET', orders=0)))
        r.immutable(root / 'completions' / (day + '.json'), r.canonical(dict(
            attempt=path.name, receipt_sha256=r.sha((path / 'receipt.json').read_bytes()))))
        return path, day

    def test_reservation_push_failure_prevents_market(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, _ = git_fixture.repo(tmp)
            with patch('collector.collect', side_effect=AssertionError('MARKET_FORBIDDEN')) as market:
                with self.assertRaisesRegex(RuntimeError, 'PUSH_DENIED'):
                    r.execute(work, 'prospective', clock=lambda: fixture.T,
                              publish_fn=lambda *a, **k: (_ for _ in ()).throw(RuntimeError('PUSH_DENIED')))
                market.assert_not_called()

    def test_failed_final_push_blocks_fresh_runner_then_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, bare = git_fixture.repo(tmp)
            calls = []
            def fail_final(*args, **kwargs):
                calls.append(1)
                if len(calls) == 2:
                    raise RuntimeError('FINAL_PUSH_FAILURE')
                return r.publish(*args, **kwargs)
            original = __import__('collector').collect
            def synthetic(root, mode, clock):
                opener = fixture.MagicMock()
                opener.open.side_effect=lambda req,timeout: fixture.CollectorTests().transport(req)
                with patch('collector.urllib.request.build_opener', return_value=opener):
                    return original(root, mode, clock)
            with patch('collector.collect', side_effect=synthetic):
                with self.assertRaisesRegex(RuntimeError, 'FINAL_PUSH_FAILURE'):
                    r.execute(work, 'prospective', clock=lambda: fixture.T, publish_fn=fail_final)
            fresh = Path(tmp) / 'fresh'
            git_fixture.git(tmp, 'clone', '-b', r.BRANCH, str(bare), str(fresh))
            with patch('collector.collect', side_effect=AssertionError('MARKET_FORBIDDEN')) as market:
                with self.assertRaisesRegex(ValueError, 'PENDING_RECOVERY'):
                    r.execute(fresh, 'prospective', clock=lambda: fixture.T)
                market.assert_not_called()
            bundle = Path(tmp) / 'recovery.zip'
            packed = recovery.pack(work / r.REL, str(fixture.T.date()), bundle)
            recovery.restore(bundle, packed['sha256'], fresh / r.REL)
            self.assertEqual(v3_archive_audit.audit_archive(fresh / r.REL)['independent_valid'], 1)
            git_fixture.git(fresh, 'config', 'user.name', 'Recovery Test')
            git_fixture.git(fresh, 'config', 'user.email', 'recovery@example.invalid')
            r.publish(fresh, fresh / r.REL, 'synthetic recovery verified')
            final = Path(tmp) / 'final'
            git_fixture.git(tmp, '-c', 'core.longpaths=true', 'clone', '-b', r.BRANCH, str(bare), str(final))
            self.assertEqual(r.verify_existing(final / r.REL), 1)
            self.assertEqual(v3_archive_audit.audit_archive(final / r.REL)['independent_valid'], 1)

    def test_round_trip_is_idempotent_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            attempt, day = self.fixture_attempt(root)
            bundle = Path(tmp) / 'bundle.zip'
            packed = recovery.pack(root, day, bundle)
            dest = Path(tmp) / 'restored'
            for _ in range(2):
                recovery.restore(bundle, packed['sha256'], dest)
            for path in root.rglob('*'):
                if path.is_file():
                    self.assertEqual(path.read_bytes(), (dest / path.relative_to(root)).read_bytes())

    def test_wrong_bundle_hash_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            _, day = self.fixture_attempt(root)
            bundle = Path(tmp) / 'bundle.zip'
            recovery.pack(root, day, bundle)
            dest = Path(tmp) / 'dest'
            with self.assertRaisesRegex(ValueError, 'BUNDLE_HASH'):
                recovery.restore(bundle, '0' * 64, dest)
            self.assertFalse(dest.exists())

    def test_conflict_rejected_without_partial_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            attempt, day = self.fixture_attempt(root)
            bundle = Path(tmp) / 'bundle.zip'
            packed = recovery.pack(root, day, bundle)
            dest = Path(tmp) / 'dest'
            conflict = dest / attempt.relative_to(root) / 'call.json'
            r.immutable(conflict, b'other raw')
            with self.assertRaisesRegex(ValueError, 'RECOVERY_CONFLICT'):
                recovery.restore(bundle, packed['sha256'], dest)
            self.assertEqual(list(dest.rglob('*.json')), [conflict])

    def test_traversal_rejected_even_with_matching_outer_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / 'bad.zip'
            with zipfile.ZipFile(bundle, 'w') as archive:
                archive.writestr('recovery.json', json.dumps(dict(day='2026-11-06',kind='V3_RECOVERY_ONLY',
                    orders=0, net_pnl=None, files={'../escape': recovery.digest(b'bad')})))
                archive.writestr('../escape', b'bad')
            with self.assertRaisesRegex(ValueError, 'RECOVERY_PATH'):
                recovery.restore(bundle, recovery.digest(bundle.read_bytes()), Path(tmp) / 'dest')
            self.assertFalse((Path(tmp) / 'escape').exists())

    def test_incomplete_attempt_stays_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            attempt, day = self.fixture_attempt(root)
            (attempt / 'receipt.json').unlink()
            bundle = Path(tmp) / 'bundle.zip'
            packed = recovery.pack(root, day, bundle)
            with self.assertRaisesRegex(ValueError, 'RECOVERY_RECEIPT_MISMATCH'):
                recovery.restore(bundle, packed['sha256'], Path(tmp) / 'dest')

    def test_missed_only_archive_is_actually_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'missed_windows' / '2026-11-06.json'
            r.immutable(path, r.canonical(dict(status='MISSED_WINDOW', prospective_v3=False, orders=1, net_pnl=None)))
            with self.assertRaisesRegex(ValueError, 'MISSED_WINDOW_DATA'):
                v3_archive_audit.audit_archive(tmp)


if __name__ == '__main__':
    unittest.main()
