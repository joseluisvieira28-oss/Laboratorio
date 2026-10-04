import csv,datetime as dt,gzip,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
import lz4.frame
import l2r_crossvenue_parent_state_materializer_v02 as e

PARENT=Path.home()/'Desktop/crypto2/L2R_2024_BTC_DISCOVERY_2024_V01/l2r_discovery_2024_v01.py'
def book(ms,bid=99,ask=101,size=1):
    timestamp=(dt.datetime(2024,1,1)+dt.timedelta(milliseconds=ms)).isoformat(timespec='milliseconds')
    return {'time':timestamp,'raw':{'channel':'l2Book','data':{'coin':'BTC','time':1704067200000+ms,'levels':[[{'px':str(bid-i),'sz':str(size),'n':1} for i in range(5)],[{'px':str(ask+i),'sz':str(size),'n':1} for i in range(5)]]}}}
class Conformance(unittest.TestCase):
    def test_frozen_parent_semantics_and_deterministic_bytes(self):
        p=e.parent(PARENT)
        data=[book(0),book(100,ask=102),book(1100,ask=102,size=.5),book(1300,ask=102,size=2),book(1500,bid=98,ask=103),book(5100,bid=98,ask=103),book(15100,bid=98,ask=103),book(59999,bid=98,ask=103),book(60100,bid=98,ask=103)]
        stale=book(1200,ask=900); stale['raw']['data']['time']=1704067200050
        data.insert(3,stale)
        data[4]['raw']['data']['time']=1704067201100 # equal payload survives
        for obj in data:
            expected=p.extract_state(obj); expected.pop('mid')
            self.assertEqual(e.source_extract(p,obj),expected)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); key='market_data/20240101/0/l2Book/BTC.lz4'; path=root/key; path.parent.mkdir(parents=True)
            blob=lz4.frame.compress(('\n'.join(json.dumps(o) for o in data)+'\n').encode()); path.write_bytes(blob)
            md5=hashlib.md5(blob).hexdigest(); rows=[{'key':key,'actual_size':str(len(blob)),'sha256':hashlib.sha256(blob).hexdigest(),'md5':md5,'inventory_etag':md5}]
            p.EXPECTED_SEGMENT_EVENTS[1]=(1,0,1)
            old=e.parent; e.parent=lambda _:p
            try:
                out=root/'one'; out.mkdir(); result=e.work((1,rows,str(root),str(out),str(PARENT)))
                out2=root/'two'; out2.mkdir(); again=e.work((1,rows,str(root),str(out2),str(PARENT)))
                ref=p.process_segment((1,rows,str(root)))
            finally: e.parent=old
            self.assertEqual(result['sha256'],again['sha256'])
            self.assertEqual(result['totals'],ref['totals'])
            self.assertEqual(result['totals']['stale'],1); self.assertEqual(result['totals']['equal'],1)
            for h in e.H:
                self.assertEqual(result['timing'][str(h)].get('available',0),ref['timing_available'][str(h)])
            for c in result['cells']:
                for k in ('anchors_total','zero_pre_depth','timing_missing','valid','weak_n','strong_n','weak_sum_rr','strong_sum_rr'):
                    pk=k.replace('_n','') if k.endswith('_n') else k
                    self.assertEqual(result['cells'][c].get(k,0),ref['cell_counts'][c].get(pk,0))
            with gzip.open(result['file'],'rt') as f: ledger=list(csv.DictReader(f))
            self.assertEqual(len(ledger),1); self.assertEqual(ledger[0]['r_1000_class'],'WEAK')
            self.assertEqual(ledger[0]['r_1000_rr'],'0.5'); self.assertEqual(ledger[0]['r_1000_same_side_depth5'],'2.5')
            self.assertEqual(ledger[0]['r_1000_envelope_ns'],'1704067201100000000')
            self.assertEqual(ledger[0]['pre_depth5'],'5.0')
            self.assertNotIn('mid',e.FIELDS)
    def test_fail_closed_parent_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'wrong.py'; path.write_text('pass')
            with self.assertRaises(e.Fail): e.parent(path)
    def test_source_schema_protected_keys_and_zero_depth(self):
        p=e.parent(PARENT)
        with self.assertRaises(Exception): p.key_hour('market_data/20250101/0/l2Book/BTC.lz4')
        self.assertEqual(e.source_extract(p,book(0,size=0))['ask_depth5'],0)
        bad=book(0); bad['raw']['data']['levels'][0][0]['sz']='nan'
        with self.assertRaises(Exception): e.source_extract(p,bad)
if __name__=='__main__': unittest.main()
