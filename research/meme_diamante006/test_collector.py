"""Synthetic-only invariants; no network calls and no financial execution."""
import datetime as dt
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import collector as c

MINTS=["7R3gZePQntJW5nAS3k1qgXswfgbs3SWh9HnPrnQe1qnd",
"6x9ApsZg7BRW93jtD3Pb9qrEVxeE8R7orRg9pG8ocBfv",
"So11111111111111111111111111111111111111112",
"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
"EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
"DezXAZ8z7PnrnRJjz3wXBoRgixCaKGFaJ7P2nnnVJ5D"]

class Tests(unittest.TestCase):
    def test_signals_only_asof(self):
        x=dict(age_days=30,liq_usd=300000,vol24_usd=900000,tx24=1500,
            ch1=2,ch6=-5,buy1=35,sell1=20,price_usd=.5)
        self.assertEqual(c.tags(x),(["H_REVERSAL"],"QUALITY_PASS"))
        x["ch6"]=8
        self.assertEqual(c.tags(x),(["H_MOMENTUM"],"QUALITY_PASS"))
        x["liq_usd"]=0
        self.assertEqual(c.tags(x),([],"QUALITY_REJECT"))
    def test_pair_mint_strict_match(self):
        p={"pairs":[{"pairAddress":"POOL","chainId":"solana",
            "baseToken":{"address":MINTS[0]},"priceUsd":"1",
            "pairCreatedAt":1700000000000,
            "liquidity":{"usd":500000},"volume":{"h24":400000},
            "txns":{"h24":{"buys":250,"sells":250},"h1":{"buys":31,"sells":20}},
            "priceChange":{"h1":2,"h6":9}}]}
        row=dict(mint=MINTS[0],pool="POOL")
        self.assertEqual(c.verify_pair(p,row)["ch6"],9)
        self.assertIsNone(c.verify_pair(p,dict(mint=MINTS[1],pool="POOL")))
        self.assertIsNone(c.verify_pair(p,dict(mint=MINTS[0],pool="OTHER")))
    def test_no_silent_genesis_with_bad_prior(self):
        rows=[dict(id=str(i),mint=MINTS[i],pool="X"*40) for i in range(6)]
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"prior.json"
            p.write_text('{"protocol":"MEME006-v0.1","seed_sha256":"WRONG"}')
            with self.assertRaisesRegex(RuntimeError,"CONTINUITY_BLOCKED"):
                c.start_state(p,rows)
    def test_seed_only_six_premapped(self):
        rows=[dict(coingecko_id=str(i),mint=MINTS[i],
            pair=dict(pair_address="P"*40),
            screen=dict(status="SCREEN_PASS_ONLY")) for i in range(6)]
        seed=json.dumps({"selection":rows}).encode()
        with patch.object(c,"SEED_SHA256",hashlib.sha256(seed).hexdigest()):
            self.assertEqual(len(c.fixed_seed(seed)),6)
        with self.assertRaisesRegex(RuntimeError,"SOURCE_INTEGRITY_BLOCKED"):
            c.fixed_seed(seed)
    def test_settlement_unknown_before_horizon(self):
        cohort=[dict(id=str(i),mint=MINTS[i],pool="P"*40) for i in range(6)]
        st=c.start_state(None,cohort)
        t=dt.datetime.now(dt.timezone.utc)
        st["entries"]=[dict(id="X",mint=MINTS[0],policy=["H_REVERSAL"],
            entry_at=t.isoformat(),min_token_amount=555,
            settlements={"h4":{"status":"PENDING"},"h24":{"status":"PENDING"}})]
        with patch.object(c,"ray_quote",side_effect=AssertionError("no future queries")):
            c.settle_pending(st,t,cohort[0],[],[])
        self.assertEqual(st["entries"][0]["settlements"]["h4"]["status"],"PENDING")
    def test_horizon_requires_next_quote_and_cost(self):
        cohort=[dict(id=str(i),mint=MINTS[i],pool="P"*40) for i in range(6)]
        st=c.start_state(None,cohort)
        t=dt.datetime.now(dt.timezone.utc)
        entry=t-dt.timedelta(hours=4,minutes=20)
        st["entries"]=[dict(id="X",mint=MINTS[0],policy=["H_REVERSAL"],
            entry_at=entry.isoformat(),min_token_amount=555,
            settlements={"h4":{"status":"PENDING"},"h24":{"status":"PENDING"}})]
        future=(dict(input_amount=555,expected_amount=48_500_000,
                     min_amount=48_300_000,routes=[]),
                dict(received_at=t.isoformat(),body_sha256="test",elapsed_ms=30,
                     error=None,http_status=200))
        receipts=[];events=[]
        with patch.object(c,"ray_quote",return_value=future) as rq:
            c.settle_pending(st,t,cohort[0],receipts,events)
        rq.assert_called_once_with(MINTS[0],c.WSOL,555)
        self.assertEqual(st["entries"][0]["settlements"]["h24"]["status"],"PENDING")
        self.assertEqual(st["entries"][0]["settlements"]["h4"]["status"],"COUNTERFACTUAL_QUOTE_ONLY")
        self.assertAlmostEqual(st["entries"][0]["settlements"]["h4"]["net_pct"],-3.6)
    def test_expired_window_is_censored_no_quote(self):
        cohort=[dict(id=str(i),mint=MINTS[i],pool="P"*40) for i in range(6)]
        st=c.start_state(None,cohort)
        t=dt.datetime.now(dt.timezone.utc)
        st["entries"]=[dict(id="X",mint=MINTS[0],policy=["H_MOMENTUM"],
            entry_at=(t-dt.timedelta(hours=8)).isoformat(),min_token_amount=555,
            settlements={"h4":{"status":"PENDING"},"h24":{"status":"PENDING"}})]
        with patch.object(c,"ray_quote",side_effect=AssertionError("expired must not quote")):
            c.settle_pending(st,t,cohort[0],[],[])
        self.assertEqual(st["entries"][0]["settlements"]["h4"]["status"],"CENSORED_WINDOW_MISSED")
    def test_no_leaked_fills_claims(self):
        self.assertNotIn("/transaction/swap",c.RAY)
        self.assertNotIn("sendTransaction",c.RAY)
        self.assertEqual(c.STAKE_LAMPORTS,50000000)

if __name__=="__main__":unittest.main()
