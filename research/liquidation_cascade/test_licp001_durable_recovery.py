import copy
import json
import tempfile
import unittest
from pathlib import Path
from research.liquidation_cascade import licp001_forward_durable_ledger_v01 as ledger


class RecoveryTests(unittest.TestCase):
    def receipt(self):
        cfg = json.loads(ledger.CONFIG.read_text())
        primary = {'family': 'BTC_CONFIRMED', 'pressure': 'SELL',
                   'meta': {'ignition': {'ignition_venue_ts': 1800000000000}}}
        alt = {'family': 'ALT_SECOND_WAVE', 'propagation_asset': 'SOLUSDT',
               'pressure': 'SELL', 'meta': {'btc_episode': primary['meta']}}
        return {'status': 'FORWARD_OBSERVATION', 'live_trading': False,
                'config_version': cfg['version'],
                'config_sha256': ledger.sha256_bytes(ledger.CONFIG.read_bytes()),
                'started_wall_ms': ledger.FREEZE_CUTOFF_MS + 1,
                'ended_wall_ms': ledger.FREEZE_CUTOFF_MS + 1000,
                'records': [primary, alt]}

    def run_build(self, receipts):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i, receipt in enumerate(receipts):
                (root / f'{i}.json').write_text(json.dumps(receipt))
            return ledger.build(root, root / 'out')

    def test_nested_secondary_and_duplicate_receipts(self):
        receipt = self.receipt()
        result = self.run_build([receipt, copy.deepcopy(receipt)])
        self.assertEqual(result['status'], 'LEDGER_OK')
        self.assertEqual(result['unique_episode_ids'], 1)
        self.assertEqual(result['unique_record_keys'], 2)

    def test_conflicting_same_family_fails_closed(self):
        receipt = self.receipt()
        other = copy.deepcopy(receipt)
        other['records'][0]['targets'] = {'changed': True}
        self.assertEqual(self.run_build([receipt, other])['status'],
                         'BLOCKED_INTEGRITY_CONFLICT')

    def test_rejected_receipt_cannot_claim_ledger_ok(self):
        receipt = self.receipt()
        del receipt['records'][1]['meta']
        self.assertEqual(self.run_build([receipt])['status'],
                         'BLOCKED_REJECTED_RECEIPTS')


if __name__ == '__main__':
    unittest.main()
