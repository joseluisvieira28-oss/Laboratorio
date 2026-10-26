import io,json,os,shutil,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import run as v

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.rec=self.root/'recovery';self.rec.mkdir();self.out=self.root/'out';self.out.mkdir()
        self.cache=Path(os.environ.get('RECOVERY_CACHE',str(Path(__file__).parent.parent/'outputs/multi_asset_fusion_v01/archives')))
        source=Path(os.environ.get('RECOVERY_INPUTS',str(Path(__file__).parent.parent/'recovery_review')))
        for f in source.iterdir():
            if f.is_file() and (f.suffix=='.json' or f.name.endswith('.zip') or f.name.endswith('.CHECKSUM')):shutil.copyfile(f,self.rec/f.name)
    def tearDown(self):self.temp.cleanup()
    def test_exact_inventory_and_whitelist(self):
        self.assertEqual(len(list(v.r.inventory())),319)
        self.assertEqual(sum(len(v.whitelist(a,t,y,m)) for k,a,t,y,m,n,u in v.r.inventory()),250)
    def test_api_body_corruption_blocks(self):
        f=self.rec/'api_SOLUSDT_1d_2022-02-26.json';f.write_bytes(f.read_bytes()+b' ')
        with self.assertRaisesRegex(v.r.GateError,'API_CAPTURE_HASH'):v.source_gate(self.cache,self.rec,self.out)
    def test_receipt_corruption_blocks(self):
        f=self.rec/'api_evidence_retry.json';f.write_bytes(f.read_bytes()+b' ')
        with self.assertRaisesRegex(v.r.GateError,'API_EVIDENCE_MANIFEST'):v.source_gate(self.cache,self.rec,self.out)
    def test_daily_checksum_corruption_blocks(self):
        f=self.rec/'SOLUSDT-1d-2022-02-26.zip';f.write_bytes(f.read_bytes()+b'corrupt')
        with self.assertRaisesRegex(v.r.GateError,'CHECKSUM:'):v.source_gate(self.cache,self.rec,self.out)
    def test_monthly_changed_hash_blocks(self):
        original=Path.read_bytes
        def altered(p):
            raw=original(p)
            return raw+b'corrupt' if p.name=='spot__BTCUSDT-1d-2021-12.zip' else raw
        with patch.object(Path,'read_bytes',altered):
            with self.assertRaisesRegex(v.r.GateError,'MONTHLY_REFERENCE_HASH'):v.source_gate(self.cache,self.rec,self.out)
    def test_duplicate_blocks(self):
        row=['0','1','1','1','1','0','3599999','0','0','0','0','0']
        with self.assertRaisesRegex(v.r.GateError,'DUPLICATE'):v.validate([row,row],{0},3600000)
    def test_gap_blocks(self):
        with self.assertRaisesRegex(v.r.GateError,'GAP'):v.validate([],{0},3600000)
    def test_unexpected_timestamp_blocks(self):
        row=['0','1','1','1','1','0','3599999','0','0','0','0','0']
        with self.assertRaisesRegex(v.r.GateError,'GAP_OR_UNEXPECTED'):v.validate([row],{3600000},3600000)
if __name__=='__main__':unittest.main(verbosity=2)
