import hashlib,hmac,unittest
from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_spot_auth import MEXCSpotAuthenticatedClient,MEXCSpotAuthError,_signed_query

class SpotAuthTests(unittest.TestCase):
    def test_signature_matches_hmac_sha256(self):
        q=_signed_query("secret",{"symbol":"BTCUSDT","timestamp":123})
        base=q.split("&signature=")[0]; sig=q.split("&signature=")[1]
        self.assertEqual(sig,hmac.new(b"secret",base.encode(),hashlib.sha256).hexdigest())
    def test_non_btc_symbol_is_blocked(self):
        c=MEXCSpotAuthenticatedClient(MEXCCredentials("k","s"),opener=lambda *a,**k:None)
        with self.assertRaises(MEXCSpotAuthError): c.open_orders("ETHUSDT")
    def test_buy_above_10_usdt_blocks_before_network(self):
        c=MEXCSpotAuthenticatedClient(MEXCCredentials("k","s"),opener=lambda *a,**k:None)
        with self.assertRaises(MEXCSpotAuthError): c.submit_market_buy(quote_order_qty_usdt=10.01,client_order_id="x")
    def test_no_transfer_or_withdraw_methods_exist(self):
        c=MEXCSpotAuthenticatedClient(MEXCCredentials("k","s"),opener=lambda *a,**k:None)
        self.assertFalse(hasattr(c,"transfer")); self.assertFalse(hasattr(c,"withdraw"))

if __name__=="__main__": unittest.main()
