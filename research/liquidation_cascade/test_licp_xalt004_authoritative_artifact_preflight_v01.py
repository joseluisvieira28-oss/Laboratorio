"""Synthetic-only XALT-004 pre-observation state firewall tests."""
import hashlib,unittest
import licp_xalt004_authoritative_artifact_preflight_v01 as s

NOW=2_000_000_000_000
def rec(i,complete=True):
    event=1_791_200_000_000+i*10_000_000
    start=event+60_000
    row={"schema":"licp_fwd_xalt_004.record.v1","episode_id":hashlib.sha256(str(i).encode()).hexdigest(),
      "pressure":"SELL","target":"SOL_USDT","event_wall_ms":event,"entry_due_wall_ms":start,
      "entry":{"wall_ms":start+500,"bid":120.0,"ask":120.1,"entry_bid":120.0},
      "exit":None}
    if complete:
        row["exit"]={"wall_ms":start+500+s.HORIZON_MS,"bid":119.5,"ask":119.6,"exit_ask":119.6}
        row["gross_bps"]=30.0;row["net_taker_bps"]=14.0
    return row

def prior():
    return {"schema":"licp_fwd_xalt_004.state.v1",
        "records":[rec(i,True) for i in range(4)]+[rec(4,False),rec(5,False)]}
class Preflight(unittest.TestCase):
    def test_valid_six(self):
        self.assertEqual(s.check_state(prior(),NOW)["elapsed_exit_missing_on_restart"],2)
    def test_duplicate_ids_fail(self):
        p=prior();p["records"][1]["episode_id"]=p["records"][0]["episode_id"]
        with self.assertRaises(s.Blocked):s.check_state(p,NOW)
    def test_missing_state_block(self):
        p=prior();p["schema"]="FAKE"
        with self.assertRaises(s.Blocked):s.check_state(p,NOW)
    def test_fee_invariant(self):
        p=prior();p["records"][0]["net_taker_bps"]=10
        with self.assertRaises(s.Blocked):s.check_state(p,NOW)
    def test_pending_missing_still_in_future(self):
        p=prior()
        with self.assertRaises(s.Blocked):s.check_state(p,1_791_200_000_000)
    def test_missing_not_filled(self):
        p=prior();s.check_state(p,NOW)
        self.assertIsNone(p["records"][4]["exit"])
        self.assertIsNone(p["records"][5]["exit"])
    def test_early_exit_block(self):
        p=prior();p["records"][0]["exit"]["wall_ms"]-=1
        with self.assertRaises(s.Blocked):s.check_state(p,NOW)
    def test_pending_count_mismatch_block(self):
        p=prior();p["records"].pop()
        with self.assertRaises(s.Blocked):s.check_state(p,NOW)
    def test_buy_side_block(self):
        p=prior();p["records"][0]["pressure"]="BUY"
        with self.assertRaises(s.Blocked):s.check_state(p,NOW)
    def test_no_live_promotion(self):
        p=s.check_state(prior(),NOW)
        self.assertEqual(p["trading_authority"],"NONE")
        self.assertFalse(p["future_results_opened"])
if __name__=="__main__":unittest.main()
