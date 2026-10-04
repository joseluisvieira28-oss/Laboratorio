import gzip,hashlib,json,struct,tempfile,unittest
from pathlib import Path
import l2r_crossvenue_discovery_v01 as d

class PlannerTests(unittest.TestCase):
 def test_exact_forward_lookup_and_frozen_lateness(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'2024-01-01.idx'
   base=1704067200000; p.write_bytes(d.REC.pack(base+101,0)+d.REC.pack(base+101,1)+d.REC.pack(base+2101,2))
   (Path(td)/'2024-01-02.idx').write_bytes(d.REC.pack(base+86400000,0))
   try:
    self.assertEqual(d.idx_lookup(td,base*1_000_000+100_100_001),('2024-01-01',0,base+101,899_999))
   finally: d.clear_indexes()
   p.write_bytes(d.REC.pack(base+2101,0))
   self.assertIsNone(d.idx_lookup(td,base*1_000_000+100_100_001))
   d.clear_indexes()
 def test_checksum_parser_requires_filename_binding(self):
  fn='BTCUSDT-aggTrades-2024-01-01.zip'; text='a'*64+'  '+fn
  m=d.SHA_RE.fullmatch(text); self.assertIsNotNone(m); self.assertEqual(m.group(2),fn)
  self.assertIsNone(d.SHA_RE.fullmatch('bad '+fn))
 def test_protocol_cells_and_non_2024_lookup_fail_closed(self):
  self.assertEqual(len(d.CELLS),6)
  self.assertIsNone(d.idx_lookup('unused',int.from_bytes(b'\x00'*8,'little')+1735689600*1_000_000_000))

if __name__=='__main__': unittest.main()
