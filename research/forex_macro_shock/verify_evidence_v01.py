"""Offline source-receipt integrity gates; never fetch prices or compute outcomes."""
import hashlib,json,unittest,importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parent
class SourceEvidenceTests(unittest.TestCase):
    def test_raw_provenance_and_honest_withdrawal(self):
        count=0;withdrawn=[]
        for p in (ROOT/'evidence').glob('*.json'):
            for r in json.loads(p.read_text(encoding='utf-8')).get('requests',[]):
                if r.get('raw_path'):
                    raw=ROOT/r['raw_path']
                    self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),r['sha256'])
                    self.assertEqual(raw.stem,r['sha256']);count+=1
                elif r.get('evidence_status','').startswith('WITHDRAWN'):
                    self.assertFalse(r['raw_bytes_preserved']);withdrawn.append(r['label'])
        self.assertEqual(count,86)
        self.assertEqual(set(withdrawn),{'BoE_clock','BoE_calendar','MEXC_kline_docs','MEXC_fee'})
    def test_no_economic_activation_on_missing_history(self):
        charter=json.loads((ROOT/'SOURCE_GATE_CHARTER_V01.json').read_text())
        self.assertFalse(charter['economic_evaluation_authorized'])
        self.assertFalse(charter['scientific_freeze_created'])
        j=json.loads((ROOT/'evidence/SOURCE_CAPABILITY_RECEIPT_V01.json').read_text())
        self.assertFalse(j['sample_event_prices_opened']);self.assertFalse(j['returns_computed'])
        self.assertEqual({x['symbol'] for x in j['metadata']},{'EUR_USDT','GBP_USDT','JPY_USDT','CHF_USDT'})
        old=[x for x in j['checks'] if 'kline_2025-04-29' in x['label']]
        self.assertEqual(len(old),4)
        self.assertTrue(all(x['rows']==0 and not x['valid'] for x in old))
    def test_private_and_foreign_destinations_fail_before_network(self):
        spec=importlib.util.spec_from_file_location('source_gate',ROOT/'source_gate_v01.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        for u in ['https://api.mexc.com/api/v1/private/account/assets','https://api.mexc.com.evil.test/api/v1/contract/detail','http://api.mexc.com/api/v1/contract/detail']:
            with self.assertRaises(PermissionError):m.fetch('forbidden',u)
if __name__=='__main__':unittest.main()
