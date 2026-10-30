import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from btc_event10m_source_gates_v04 import asof
D=1800000000500
SHA="f"*64
def setup():
    samples=[]
    for lag in (13000,8000,1500):
        t=D-lag
        samples.append({"asset":"BTC_USDT","received_ms":t,
            "okx_spot":{"received_ms":t-200,"server_ms":t-400,"sha256":SHA},
            "mexc_futures":{"received_ms":t-250,"sha256":SHA}})
    product={"symbol":"BTC_USDT","state":"ONLINE","duration_min":10,
       "received_ms":D-5100,"sha256":SHA,"up_pay_rate":.8,"down_pay_rate":.8}
    idx={"symbol":"BTC_USDT","index_price":65000.,"received_ms":D-300,
       "server_ms":D-400,"sha256":SHA}
    return samples,product,idx,D
class Gates(unittest.TestCase):
 def test_source_all_pass(self):self.assertTrue(all(asof(*setup()).values()))
 def test_old_last_book_fail(self):
    a=setup();a[0][-1]["mexc_futures"]["received_ms"]=D-2500
    self.assertFalse(asof(*a)["last_book_fresh"])
 def test_payout_too_old_fail(self):
    a=setup();a[1]["received_ms"]=D-15000
    self.assertFalse(asof(*a)["product_fresh"])
 def test_index_old_fail(self):
    a=setup();a[2]["server_ms"]=D-9000
    self.assertFalse(asof(*a)["index_fresh"])
 def test_pair_wrong_gap_block(self):
    a=setup();a[0][1]["received_ms"]=a[0][0]["received_ms"]+9000
    with self.assertRaises(ValueError):asof(*a)
 def test_future_received_block(self):
    a=setup();a[0][-1]["received_ms"]=D+1
    with self.assertRaises(ValueError):asof(*a)
 def test_wrong_asset_block(self):
    a=setup();a[0][0]["asset"]="ETH_USDT"
    with self.assertRaises(ValueError):asof(*a)
if __name__=="__main__":unittest.main()
