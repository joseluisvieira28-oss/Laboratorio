"""Hermetic original-format OKX archive fixtures, no market data or exchange calls."""
import io,json,tarfile,tempfile,unittest
from pathlib import Path
from research.convex_okx_l2_v05.operator_uploaded_l2_v05d import replay,CASES,TIERS

def fixture(folder,key,order=1,bad_seq=False,bad_snapshot=False):
    spec=CASES[key]
    t0=spec["t0"]
    inst=spec["inst"]
    file=Path(folder)/f"{inst}-L2orderbook-400lv-{spec['day']}.tar.gz"
    asks=[[str(100+i/1000),"100","3"] for i in range(400)]
    bids=[[str(99-i/1000),"100","3"] for i in range(400)]
    doc=[
       {"instId":inst,"action":"snapshot" if not bad_snapshot else "update",
        "ts":str(t0-150),"asks":asks,"bids":bids},
       {"instId":inst,"action":"update","ts":str(t0-50),
        "asks":[["100","50","1"]],"bids":[["99","200","1"]]},
       {"instId":inst,"action":"update","ts":str(t0+20),
        "asks":[["100","0","0"]],"bids":[["99","0","0"]]},
    ]
    if bad_seq:doc[1]["ts"]=str(t0-500)
    data=b"\n".join(json.dumps(x).encode() for x in doc)+b"\n"
    with tarfile.open(file,"w:gz") as tar:
        info=tarfile.TarInfo(file.name.removesuffix(".tar.gz")+".data")
        info.size=len(data)
        tar.addfile(info,io.BytesIO(data))
    return file

class ActualFormatContracts(unittest.TestCase):
    def test_both_instruments_tar_data_no_seq_valid_as_provisional(self):
        for key in CASES:
            with self.subTest(key=key):
                with tempfile.TemporaryDirectory() as d:
                    path=fixture(d,key)
                    v=replay(path,key)
                    self.assertEqual(v["latest_quote_age_ms"],50)
                    self.assertEqual(v["continuity_proof"],"UNVERIFIED_NO_EXPORTED_SEQ_IDS")
                    self.assertEqual(v["asks_levels"],400)
                    self.assertEqual(v["bids_levels"],400)
                    self.assertEqual(v["best_ask"],"100.0")
                    self.assertEqual(v["first_event_after_T0_was_NOT_APPLIED"],CASES[key]["t0"]+20)
                    self.assertEqual(len(v["static_hypothetical_long_ask_entry_sweeps"]),4)
                    self.assertFalse(v["live_go"])
    def test_wrong_day_symbol_filename_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            path=fixture(d,"BNB")
            with self.assertRaisesRegex(ValueError,"EXACT_PORTAL_FILENAME"):
                replay(path,"SOL")
    def test_event_order_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path=fixture(d,"SOL",bad_seq=True)
            with self.assertRaisesRegex(ValueError,"NONCHRONOLOGICAL_EVENT"):
                replay(path,"SOL")
    def test_uninitialized_update_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=fixture(d,"BNB",bad_snapshot=True)
            with self.assertRaisesRegex(ValueError,"DELTA_BEFORE_FIRST_SNAPSHOT"):
                replay(path,"BNB")
    def test_four_static_pre_frozen_fractions(self):
        self.assertEqual(TIERS,("0.25","0.5","0.75","1"))
    def test_no_base_coin_equals_contracts_assumption(self):
        self.assertEqual(CASES["SOL"]["launch_face_base_per_contract"],"1")
        self.assertEqual(CASES["BNB"]["launch_face_base_per_contract"],"0.01")

if __name__=="__main__":unittest.main()
