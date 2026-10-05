import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collector as c
import model as m


class Persistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'state.db'
        self.store = c.Store(self.path)
        self.raw = b'{"success":true}'
        self.row = {'source': 'mexc_depth', 'raw_sha256': c.digest(self.raw), 'validation': {'update_id': 1}}

    def tearDown(self):
        self.store.db.close(); self.tmp.cleanup()

    def test_restart_idempotency(self):
        first = self.store.append('one', self.row, self.raw)
        self.store.db.close(); self.store = c.Store(self.path)
        self.assertEqual(first, self.store.append('one', self.row, self.raw))
        self.assertEqual(self.store.verify()['receipts'], 1)
        other = dict(self.row, raw_sha256=c.digest(b'other'))
        with self.assertRaises(ValueError): self.store.append('one', other, b'other')

    def test_duplicate_message_survives_restart(self):
        self.store.append('one', self.row, self.raw)
        self.store.db.close(); self.store = c.Store(self.path)
        self.store.append('two', self.row, self.raw)
        obj = json.loads(self.store.db.execute('SELECT payload FROM receipts WHERE token="two"').fetchone()[0])
        self.assertTrue(obj['duplicate_message'])

    def test_corruption_detected(self):
        self.store.append('one', self.row, self.raw)
        self.store.db.execute('UPDATE raw SET body=?', (b'bad',)); self.store.db.commit()
        with self.assertRaises(ValueError): self.store.verify()

    def test_rollback_incomplete_transaction(self):
        self.store.append('one', self.row, self.raw)
        code = "import sqlite3,os,sys;d=sqlite3.connect(sys.argv[1]);d.execute('BEGIN IMMEDIATE');d.execute('DELETE FROM receipts');os._exit(9)"
        result = subprocess.run([sys.executable, '-c', code, str(self.path)])
        self.assertEqual(result.returncode, 9)
        self.assertEqual(self.store.verify()['receipts'], 1)

    def test_concurrent_lock_and_crash_lease(self):
        self.store.acquire('a', 100)
        second = c.Store(self.path)
        try:
            with self.assertRaises(RuntimeError): second.acquire('b', 200)
            second.acquire('b', 180101)
            with self.assertRaises(RuntimeError): self.store.acquire('a', 180102)
        finally: second.db.close()


class Boundaries(unittest.TestCase):
    def test_html_200_is_invalid(self):
        row = {'source': 'mexc_depth', 'http_status': 200, 'rtt_ms': 10}
        self.assertFalse(c.validate(row, b'<html>Site Unavailable</html>')['schema_valid'])

    def test_binance_rest_clock_not_fabricated(self):
        row = {'source': 'binance_depth', 'http_status': 200, 'rtt_ms': 10}
        v = c.validate(row, b'{"lastUpdateId":1,"bids":[["1", "10"]],"asks":[["1.1","10"]]}')
        self.assertTrue(v['schema_valid']); self.assertIsNone(v['exchange_ms']); self.assertFalse(v['timing_valid'])

    def test_book_invalid_nan_crossed_and_unsorted(self):
        for b in [{'bids': [[float('nan'), 1]], 'asks': [[2, 1]]},
                  {'bids': [[2, 1]], 'asks': [[1, 1]]},
                  {'bids': [[1, 1], [1.5, 1]], 'asks': [[2, 1]]}]:
            with self.assertRaises(ValueError): c.book(b)

    def test_protected_event_stops_before_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(sys, 'argv', ['collector.py', '--state', tmp + '/db', '--export', tmp + '/evidence']), patch.object(c.time, 'time', return_value=c.SETUP_STOP), patch.object(c, 'fetch') as fetch:
                with self.assertRaises(RuntimeError): c.main()
                fetch.assert_not_called()

    def test_generic_ecb_change_not_event(self):
        row = {'source': 'ecb_index', 'http_status': 200}
        v = c.validate(row, b'<html>monetary policy cookie banner changed</html>')
        self.assertFalse(v['semantic_publication_detected'])


class FrozenModel(unittest.TestCase):
    def test_directions_and_stale(self):
        self.assertEqual(m.signal(1.01, 1, 0, 20, True), 'SHORT')
        self.assertEqual(m.signal(.99, 1, 0, 20, True), 'LONG')
        self.assertIsNone(m.signal(1.01, 1, 0, 20, False))

    def test_calibration_not_pnl(self):
        out = m.calibrate([1.] * 21600, [2.] * 21600)
        self.assertEqual(out['threshold_bps'], 20)
        with self.assertRaises(ValueError): m.calibrate([1.], [2.])

    def test_contract_rounding_and_no_default(self):
        self.assertEqual(m.contracts(10, 1.1, 1, 1, 1), 9)
        with self.assertRaises(ValueError): m.contracts(10, 1.1, 0, 1, 1)
        with self.assertRaises(ValueError): m.contracts(.1, 1.1, 1, 1, 1)

    def test_insufficient_depth_and_real_fees(self):
        with self.assertRaises(ValueError): m.vwap([[1, 1]], 2, 1)
        self.assertEqual(m.vwap([[1, 1], [2, 1]], 2, 1), 1.5)
        self.assertEqual(m.net_bps('LONG', 1, 1), -18)

    def test_no_early_pass_and_no_signal_events(self):
        self.assertEqual(m.economic_gate([10.] * 7)['verdict'], 'FORWARD_COLLECTING')
        self.assertEqual(m.economic_gate([10.] * 8)['verdict'], 'FORWARD_PASS')
        self.assertEqual(m.economic_gate([0.] * 8)['verdict'], 'FORWARD_FAIL')


if __name__ == '__main__':
    unittest.main()
