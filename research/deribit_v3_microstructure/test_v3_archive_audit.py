"""Offline archive-audit tests. No Deribit requests."""
import json
from pathlib import Path
import tempfile
import unittest

import v3_archive_audit as a
import test_collector

class ArchiveAuditTests(unittest.TestCase):
    def captured(self,root,mode='prospective'):
        attempt, receipt=test_collector.CollectorTests().run_attempt(root,mode=mode)
        return attempt, receipt

    def test_empty_archive_has_zero_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=a.audit_archive(tmp)
            self.assertEqual(r['independent_valid'],0)
            self.assertEqual(r['status'],'ARCHIVE_AUDIT_PASS')

    def test_saved_fixture_independently_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt,receipt=self.captured(tmp)
            r=a.audit_archive(tmp)
            self.assertEqual(r['independent_valid'],1)
            self.assertEqual(r['claimed_days'],1)
            self.assertEqual(r['invalid_attempts'],0)
            self.assertIsNone(r['net_pnl'])

    def test_invalid_attempt_retained_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt,receipt=self.captured(tmp)
            path=attempt/'receipt.json'
            r=json.loads(path.read_bytes())
            r.update(prospective_v3=False,valid_technical=False,status='INVALID_ATTEMPT',
                     reject_reason='SYNTHETIC_FAILURE')
            path.write_text(json.dumps(r))
            report=a.audit_archive(tmp)
            self.assertEqual(report['independent_valid'],0)
            self.assertEqual(report['invalid_attempts'],1)

    def test_raw_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt,_=self.captured(tmp)
            (attempt/'call.json').write_text('modified')
            with self.assertRaisesRegex(ValueError,'RAW_HASH'):
                a.audit_archive(tmp)

    def test_orphan_claim_blocks_further_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/'prospective';d.mkdir()
            (d/'2026-11-09.claim').write_text('{"day":"2026-11-09"}')
            with self.assertRaisesRegex(ValueError,'ORPHAN_CLAIM'):
                a.audit_archive(tmp)

    def test_changed_receipt_fields_rejected_independently(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt,_=self.captured(tmp)
            r=json.loads((attempt/'receipt.json').read_bytes())
            r['decision_at']='2026-11-06T08:10:00+00:00'
            (attempt/'receipt.json').write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'DECISION_WINDOW'):
                a.audit_archive(tmp)

    def test_missing_receipt_requires_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt,_=self.captured(tmp)
            (attempt/'receipt.json').unlink()
            with self.assertRaisesRegex(ValueError,'INCOMPLETE_ATTEMPT'):
                a.audit_archive(tmp)

if __name__=='__main__':
    unittest.main()
