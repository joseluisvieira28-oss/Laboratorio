"""Test the frozen V03 replay against SYNTHETIC dummy records, not user books."""
import gzip,io,json,tarfile,tempfile,unittest
from pathlib import Path
from research.funding_hunter_v03.dual_btc_400l2_private_replay import INSTS,PROBES,run,replay,stamp

def fake(d,inst,mode="ok"):
    fn=f"{inst}-L2orderbook-400lv-2025-06-02"
    p=Path(d)/(fn+".tar.gz")
    a=[[str(99000+i*.01),"400","1"] for i in range(400)]
    b=[[str(98999-i*.01),"400","1"] for i in range(400)]
    records=[]
    if mode=="stale":
        times=[stamp("00:04:00"),stamp("12:04:00"),stamp("23:54:00")]
    else:
        times=[stamp(x)-30 for x in PROBES]
    for k,t in enumerate(times):
        records.append({"instId":inst,"action":"snapshot","ts":str(t),
                        "asks":a,"bids":b})
    if mode=="wrong_symbol":records[1]["instId"]="BAD"
    if mode=="crossed":records[0]["bids"][0][0]="99500"
    if mode=="update_first":records[0]["action"]="update"
    records.append({"instId":inst,"action":"update","ts":str(stamp("23:55:00")+1),
                    "asks":[],"bids":[]})
    if mode=="bad_tail":records[-1]["instId"]="BAD"
    if mode=="invalid_count":records[-1]["asks"]=[["110000","1","nan"]]
    if mode=="exact_time":records[0]["ts"]=str(stamp(PROBES[0]))
    if mode=="equal_timestamp":
        records.insert(1,{"instId":inst,"action":"update","ts":records[0]["ts"],
                         "asks":[["110000","0","0"]],"bids":[]})
    raw=b"\n".join(json.dumps(x).encode() for x in records)+b"\n"
    with tarfile.open(p,"w:gz") as z:
        m=tarfile.TarInfo(fn+".data");m.size=len(raw);z.addfile(m,io.BytesIO(raw))
        if mode=="extra_member":
            m=tarfile.TarInfo("unexpected.data");m.size=1;z.addfile(m,io.BytesIO(b"x"))
    return p

class FreezeContracts(unittest.TestCase):
    def test_entire_tail_validated_after_last_probe(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"],"bad_tail")
            with self.assertRaisesRegex(ValueError,"WRONG_INSTRUMENT"):
                replay(p,INSTS["LINEAR"])
    def test_gzip_trailer_crc_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"])
            raw=bytearray(p.read_bytes());raw[-8]^=1;p.write_bytes(raw)
            with self.assertRaises(gzip.BadGzipFile):replay(p,INSTS["LINEAR"])
    def test_truncated_gzip_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"]);p.write_bytes(p.read_bytes()[:-8])
            with self.assertRaises(EOFError):replay(p,INSTS["LINEAR"])
    def test_extra_tar_member_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"],"extra_member")
            with self.assertRaisesRegex(ValueError,"EXTRA_TAR_MEMBER"):replay(p,INSTS["LINEAR"])
    def test_invalid_order_count_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"],"invalid_count")
            with self.assertRaisesRegex(ValueError,"INVALID_ORDER_COUNT"):replay(p,INSTS["LINEAR"])
    def test_probe_includes_event_exactly_at_clock(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"],"exact_time")
            self.assertEqual(replay(p,INSTS["LINEAR"])["sample_quotes"][0]["source_quote_age_ms"],0)
    def test_equal_timestamp_and_zero_delete(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"],"equal_timestamp");out=replay(p,INSTS["LINEAR"])
            self.assertEqual(out["same_timestamp_adjacent_events"],1)
            self.assertEqual(out["zero_quantity_deletions"],1)
            self.assertTrue(out["gzip_crc32_isize_verified_to_eof"])
    def test_exact_clocks_and_names_frozen(self):
        self.assertEqual(PROBES,("00:05:00","12:05:00","23:55:00"))
        self.assertEqual(tuple(INSTS),("LINEAR","INVERSE"))
    def test_complete_deterministic_asof_and_no_alpha(self):
        with tempfile.TemporaryDirectory() as d:
            a=fake(d,INSTS["LINEAR"]);b=fake(d,INSTS["INVERSE"])
            out=run({"LINEAR":a,"INVERSE":b})
            self.assertEqual(out["verdict"],"REAL_TWO_BOOK_SAMPLES_QUOTE_ONLY_NO_FUNDING_EDGE")
            self.assertEqual(len(out["two_instruments_simultaneous_descriptive_quotes"]),3)
            self.assertFalse(out["live_go"])
            self.assertFalse(out["funding_cashflows_verified"])
            for row in out["source_only_cases"].values():
                self.assertEqual(len(row["sample_quotes"]),3)
                self.assertEqual([s["source_quote_age_ms"] for s in row["sample_quotes"]],[30,30,30])
                self.assertFalse(row["lossless_source_continuity_proven"])
    def test_stale_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"],"stale")
            out=replay(p,INSTS["LINEAR"])
            self.assertEqual(out["status"],"SOURCE_QUOTE_COVERAGE_FAIL_CLOSED")
            self.assertEqual(out["sample_quotes"][0]["status"],"STALE_OR_FUTURE_QUOTE")
    def test_wrong_instrument_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"],"wrong_symbol")
            with self.assertRaisesRegex(ValueError,"WRONG_INSTRUMENT"):
                replay(p,INSTS["LINEAR"])
    def test_crossed_at_probe_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["INVERSE"],"crossed")
            with self.assertRaisesRegex(ValueError,"CROSSED"):
                replay(p,INSTS["INVERSE"])
    def test_update_before_first_snapshot_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["INVERSE"],"update_first")
            with self.assertRaisesRegex(ValueError,"NO_INITIAL_SNAPSHOT"):
                replay(p,INSTS["INVERSE"])
    def test_exact_file_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=fake(d,INSTS["LINEAR"])
            with self.assertRaisesRegex(ValueError,"ORIGINAL_ARCHIVE"):
                replay(p,INSTS["INVERSE"])
if __name__=="__main__":unittest.main()
