import unittest
from research.digui007 import collector as c

class TestAsOf(unittest.TestCase):
    def test_pool_parsing(self):
        pool={"id":"solana_pair1","attributes":{"address":"pair1",
            "pool_created_at":"2026-11-17T00:00:00Z",
            "reserve_in_usd":"1500"},"relationships":{"base_token":{"data":{"id":"solana_mint1"}},
               "quote_token":{"data":{"id":"solana_quote1"}}}}
        p=c.parse_pool(pool)
        self.assertEqual(p["mint"],"mint1")
        self.assertEqual(p["pool_address"],"pair1")
        self.assertNotIn("future_return",p)
    def test_missing_source_is_unknown(self):
        p={"gecko_liquidity_usd":None,"dex":None,"onchain":None}
        self.assertEqual(c.assess(p)["flag_status"],"PARTIAL_DATA_UNVERIFIED")
    def test_caution_not_fraud(self):
        p={"gecko_liquidity_usd":100,"dex":None,"onchain":{"mint_data_seen":True,
           "mint_authority_active":True,"freeze_authority_active":False,
           "top20_token_accounts_pct":95}}
        got=c.assess(p)
        self.assertIn("MINT_AUTHORITY_ACTIVE",got["flags"])
        self.assertNotIn("FRAUD",got["flag_status"].upper())
    def test_accounts_not_unique_owners(self):
        acc={"result":{"value":{"data":{"parsed":{"info":{
            "supply":"10000","mintAuthority":None,"freezeAuthority":None}}}}}}
        large={"result":{"value":[{"amount":"9000"},{"amount":"500"}]}}
        x=c.decode_chain(acc,large)
        self.assertEqual(x["top20_token_accounts_pct"],95)
        self.assertIn("NOT unique beneficial owners",x["note"])
    def test_empty_pool_not_promoted(self):
        self.assertIsNone(c.parse_pool({"relationships":{"base_token":{"data":{"id":"ethereum_0x1"}}}}))
    def test_asof_receipts_are_explicit(self):
        self.assertEqual(c.PUMP_PROGRAM,"6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
        self.assertIn("solana",c.GECKO)

if __name__=="__main__":unittest.main()
