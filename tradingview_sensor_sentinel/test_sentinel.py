import importlib.util
import unittest
from datetime import datetime, timezone

spec=importlib.util.spec_from_file_location("s","tradingview_sensor_sentinel/sentinel.py")
s=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

def rec(close=1790253600000, ltf=5):
    p={
      "lab_id":s.LAB_ID,"sensor_version":s.SENSOR_VERSION,"symbol":s.SYMBOL,"timeframe":s.TIMEFRAME,
      "bar_open_ms":close-s.BAR_MS,"bar_close_ms":close,"close":83385.78,
      "tv_total_volume":30.0,"tv_buy_volume":18.0,"tv_sell_volume":12.0,"tv_delta":6.0,
      "tv_delta_pct":0.2,"poc_mid":100.0,"poc_migration_bps":1.0,"vah":101.0,"val":99.0,
      "buy_imbalance_rows":2,"sell_imbalance_rows":1,"footprint_rows":10,"ltf_intrabars":ltf,
      "ltf_path_efficiency":0.5,"ltf_signed_volume_pct":0.1,"volume_z":0.0,"bar_return_bps":1.0,
      "eth_ret":0.0,"sol_ret":0.0,"cme_btc_ret":None,"ndx_ret":None,"dxy_ret":None
    }
    recv=datetime.fromtimestamp((close+6000)/1000, tz=timezone.utc).isoformat()
    return {
      "record_type":"TVFP_RECEIPT",
      "evidence_key":f"{s.LAB_ID}|{s.SENSOR_VERSION}|{s.SYMBOL}|{s.TIMEFRAME}|{close}",
      "payload_sha256":s.sha(p),"received_at":recv,
      "payload":p,"trading_authority":"NONE"
    }

class T(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(s.audit([rec()])["status"],"PASS")

    def test_gap(self):
        self.assertEqual(s.audit([rec(),rec(1790254200000)])["status"],"DEGRADED")

    def test_incomplete_ltf(self):
        self.assertEqual(s.audit([rec(ltf=4)])["status"],"DEGRADED")

    def test_bad_poc(self):
        r=rec()
        r["payload"]["poc_mid"]=200
        r["payload_sha256"]=s.sha(r["payload"])
        self.assertEqual(s.audit([r])["status"],"FAIL_CLOSED")

    def test_bad_sha(self):
        r=rec()
        r["payload_sha256"]="0"*64
        self.assertEqual(s.audit([r])["status"],"FAIL_CLOSED")

    def test_conflicting_duplicate(self):
        a=rec()
        b=rec()
        b["payload"]["close"]=999
        b["payload_sha256"]=s.sha(b["payload"])
        self.assertEqual(s.audit([a,b])["status"],"FAIL_CLOSED")

    def test_exact_retry(self):
        a=rec()
        x=s.audit([a,dict(a)])
        self.assertEqual(x["status"],"PASS")
        self.assertEqual(x["exact_duplicate_retries"],1)

if __name__=="__main__":
    unittest.main()
