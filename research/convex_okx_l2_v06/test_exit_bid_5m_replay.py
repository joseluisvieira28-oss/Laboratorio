"""No external historical prices in CI. Synthetic .data tar fixtures only."""
import io,json,tarfile,tempfile,unittest
from pathlib import Path
from research.convex_okx_l2_v06.exit_bid_5m_replay import CONFIG,SCALES,observe

def make_source(directory,key,mode="normal"):
    spec=CONFIG[key]
    start=spec["end_ms"]-300000
    name=f"{spec['inst']}-L2orderbook-400lv-{spec['day']}"
    path=Path(directory)/(name+".tar.gz")
    messages=[]
    for i,t in enumerate([start+x*60000-100 for x in range(5)]+[spec["end_ms"]-101]):
        bid=25 if key=="SOL" else 250
        if i>=2:bid=19 if key=="SOL" else 238
        if mode=="no-cross":bid=25 if key=="SOL" else 250
        b=[[str(bid-j/1000),"10000","1"] for j in range(400)]
        a=[[str(bid+0.01+j/1000),"10000","1"] for j in range(400)]
        if mode=="crossed" and i==2:a[0][0]=str(bid)
        messages.append({"instId":spec["inst"],"ts":str(t),"action":"snapshot" if mode!="no-snapshot" else "update",
                         "bids":b,"asks":a})
    messages.append({"instId":spec["inst"],"ts":str(spec["end_ms"]+10),
                     "action":"update","bids":[["0","0","0"]],"asks":[]})
    data=b"\n".join(json.dumps(x).encode() for x in messages)+b"\n"
    with tarfile.open(path,"w:gz") as arc:
        member=tarfile.TarInfo(name+".data");member.size=len(data)
        arc.addfile(member,io.BytesIO(data))
    return path

class ExitIntrabarContracts(unittest.TestCase):
    def test_exact_two_original_frozen_exit_bars(self):
        self.assertEqual(CONFIG["SOL"]["end_ms"],1685981100000)
        self.assertEqual(CONFIG["BNB"]["end_ms"],1700588700000)
        self.assertEqual(SCALES,("0.25","0.5","0.75","1"))
    def test_both_frozen_assets_six_fresh_checkpoint_snapshots_and_first_cross(self):
        for asset in CONFIG:
            with self.subTest(asset=asset):
                with tempfile.TemporaryDirectory() as d:
                    out=observe(make_source(d,asset),asset)
                    self.assertEqual(out["status"],"SIX_CAUSAL_L2_SAMPLES_NO_SEQ_PROOF")
                    self.assertEqual(len(out["six_reference_quotes"]),6)
                    self.assertIsNotNone(out["first_bid_cross_within_original_bar"])
                    self.assertEqual(out["first_bid_cross_within_original_bar"]["relative_to_original_stop_bar_start_ms"],119900)
                    self.assertFalse(out["lossless_update_continuity_proven"])
                    self.assertEqual(out["trading_authority"],"NONE")
    def test_no_cross_reported_no_fake_broker_trigger(self):
        with tempfile.TemporaryDirectory() as d:
            out=observe(make_source(d,"SOL","no-cross"),"SOL")
            self.assertIsNone(out["first_bid_cross_within_original_bar"])
    def test_crossed_book_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"CROSSED"):
                observe(make_source(d,"BNB","crossed"),"BNB")
    def test_update_before_snapshot_failclosed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"NO_INITIAL_SNAPSHOT"):
                observe(make_source(d,"SOL","no-snapshot"),"SOL")
    def test_filename_wrong_contract_or_day_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path=make_source(d,"BNB")
            with self.assertRaisesRegex(ValueError,"INVALID_ORIGINAL_OKX_PORTAL_ARCHIVE"):
                observe(path,"SOL")
if __name__=="__main__":unittest.main()
