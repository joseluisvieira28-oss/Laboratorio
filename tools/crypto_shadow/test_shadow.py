import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import shadow

class ShadowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = shadow.Store(Path(self.temp.name)/'state')
    def tearDown(self):
        self.store.close()
        self.temp.cleanup()
    def test_raw_and_chain_tamper_detected(self):
        transport = shadow.PublicTransport(self.store)
        transport.witness('https://api.mexc.com/api/v1/contract/detail', 200, b'{"data":[]}', 100)
        self.store.verify()
        raw = next((self.store.folder/'raw').iterdir())
        raw.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'RAW_RECEIPT_BROKEN'): self.store.verify()
    def test_ledger_tamper_detected(self):
        self.store.add('TEST', {'x':1})
        self.store.db.execute("UPDATE receipts SET body='{}'")
        self.store.db.commit()
        with self.assertRaisesRegex(ValueError, 'CHAIN_BROKEN'): self.store.verify()
    def test_dedup_atomic_on_restart(self):
        self.store.add('SIGNAL', {'x':1}, 'one')
        self.assertIsNone(self.store.add('SIGNAL', {'x':2}, 'one'))
        self.assertFalse(self.store.first_seen('one'))
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM receipts').fetchone()[0],1)
    def test_private_and_history_rejected_without_network(self):
        transport = shadow.PublicTransport(self.store)
        for base, path in [('https://api.mexc.com','/api/v1/private/order/create'),
                           ('https://api.mexc.com','/api/v1/contract/kline/SOL_USDT'),
                           ('https://www.okx.com','/api/v5/public/funding-rate-history'),
                           ('http://api.mexc.com','/api/v1/contract/detail')]:
            with self.assertRaises(ValueError): transport.get_json([base],path)
    def test_quote_depth_units_and_fail_closed(self):
        raw = {'success':True,'data':{'timestamp':1000,'bids':[[99,100]],'asks':[[100,100]]}}
        receipt = {'received_ms':1100,'sha256':'a'*64}
        q = shadow.quote_view(raw,receipt,'0.1')
        self.assertEqual(shadow.number(q['static_crossing_loss_usdt']),1)
        self.assertIsNone(q['net_usdt'])
        for change in ('stale','crossed','nan','thin','negative','unsorted'):
            bad = copy.deepcopy(raw)
            if change == 'stale': bad['data']['timestamp']=-9000
            if change == 'crossed': bad['data']['asks']=[[98,100]]
            if change == 'nan': bad['data']['asks']=[['NaN',100]]
            if change == 'thin': bad['data']['asks']=[[100,0.01]]
            if change == 'negative': bad['data']['bids']=[[99,-1]]
            if change == 'unsorted': bad['data']['bids']=[[98,100],[99,100]]
            with self.subTest(change=change), self.assertRaises((ValueError, ArithmeticError)):
                shadow.quote_view(bad,receipt,'0.1')
    def test_real_outbox_alert_no_fabricated_proof_or_duplicates(self):
        local = Path(self.temp.name)/'local'
        dbdir = local/'CryptoLab'/'ThreeConvexV07'/'data'
        dbdir.mkdir(parents=True)
        close = ((self.store.freeze['started_ms']//3600000)+1)*3600000
        db = sqlite3.connect(dbdir/'v07_events.sqlite3')
        db.execute('CREATE TABLE outbox(id TEXT,sent_at_ms INT,telegram_message_id INT,added_ms INT)')
        db.execute('INSERT INTO outbox VALUES(?,?,?,?)',(f'SIGNAL:SOL_CONVEX_1H:{close}',None,None,close))
        db.commit(); db.close()
        with patch.object(shadow,'now_ms',return_value=close+1000):
            first = shadow.observe_signals(self.store,local,{})
            second = shadow.observe_signals(self.store,local,{})
        self.assertEqual(len(first['new_alerts']),1)
        self.assertEqual(first['new_alerts'][0]['status'],'NO_GO_SIGNAL_PROOF_MISSING')
        self.assertIsNone(first['new_alerts'][0]['net_usdt'])
        self.assertEqual(second['new_alerts'],[])
    def test_preinstall_settlement_ignored_and_frozen_threshold(self):
        due = ((self.store.freeze['started_ms']//86400000)+1)*86400000+300000
        t = due-300000
        rows = {}
        for instrument, rate in [('BTC-USDT-SWAP','0.001'),('BTC-USD-SWAP','0')]:
            rows[instrument] = {'funding_prediction_not_cashflow':[{'prevFundingTime':str(t), 'fundingTime':str(t+28800000),
                'settState':'settled','ts':str(due), 'settFundingRate':rate}], 'funding_receipt':{'sha256':'a'*64}}
        result = shadow.funding_decisions(self.store,rows,due)
        self.assertEqual(result['signal'],'SHORT_LINEAR_LONG_INVERSE')
        self.assertEqual(result['lagged_spread_bps_per_hour'],'1.250')
        self.assertIsNone(result['net_usdt'])
        self.assertEqual(shadow.funding_decisions(self.store,rows,due)['status'],'DAILY_DECISION_ALREADY_RECORDED')
    def test_no_backfill_or_predicted_rate_as_settlement(self):
        result = shadow.funding_decisions(self.store,{}, self.store.freeze['started_ms'])
        self.assertNotIn('signal', result)
        self.assertEqual(result['future_settlements_witnessed'],0)
    def test_preinstallation_and_processing_funding_not_admitted(self):
        current = self.store.freeze['started_ms'] + 10000
        old = self.store.freeze['started_ms']-1000
        for state, t in [('settled', old), ('processing', current-1000)]:
            row = {'funding_prediction_not_cashflow':[{'prevFundingTime':str(t), 'fundingTime':str(t+28800000),
                'settState':state, 'ts':str(current), 'settFundingRate':'0.2', 'fundingRate':'0.99'}],
                'funding_receipt':{'sha256':'a'*64}}
            shadow.funding_decisions(self.store, {'BTC-USDT-SWAP':row}, current)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM seen WHERE id LIKE ?',('SETTLED:%',)).fetchone()[0],0)
    def test_http_observer_seals_actual_response_bytes(self):
        class Response:
            status = 200
            fp = None
            def read(self): return b'{"success": true, "data": []}'
            def __enter__(self): return self
            def __exit__(self,*_): pass
        transport = shadow.PublicTransport(self.store)
        with patch('urllib.request.urlopen',return_value=Response()):
            result = transport.get_json(['https://api.mexc.com'],'/api/v1/contract/detail')
        self.assertTrue(result['success'])
        receipt = transport.last['/api/v1/contract/detail']
        self.assertEqual(receipt['sha256'],shadow.sha(b'{"success": true, "data": []}'))
        self.store.verify()
    def test_report_does_not_fabricate_money(self):
        summary = shadow.dashboard(self.store,{'mexc':{}})
        self.assertEqual(summary['verified_net_opportunities'],0)
        self.assertIsNone(summary['verified_net_usdt'])
        self.assertIsNone(summary['verified_net_eur'])
        self.assertIsNone(summary['realised_trading_pnl'])

if __name__ == '__main__': unittest.main()
