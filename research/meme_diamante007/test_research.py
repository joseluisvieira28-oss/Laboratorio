import datetime as dt
import hashlib
import json
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import generate_dune_sql as gen
import reduce_dune_export as red

def fake_report():
    cohort=[dict(coin_id="coin"+str(i),mint="mint"+str(i),pool="pool"+str(i)) for i in range(6)]
    rows=[]
    for i in range(6):
        for j in range(6):
            t=dt.datetime(2026,10,2,2*j,37,tzinfo=dt.timezone.utc).timestamp()
            rows.append(dict(coin_id="coin"+str(i),policy="H_REVERSAL_PRICE_ONLY" if j<3 else "H_MOMENTUM_PRICE_ONLY",
                observed_at=int(t),h1_pct=1.5,h6_pct=-4.0))
    return json.dumps(dict(cohort=cohort,proxy_price_events=rows)).encode()

class Tests(unittest.TestCase):
    def test_source_hash_enforced(self):
        with self.assertRaisesRegex(RuntimeError,"SOURCE_INTEGRITY_BLOCKED"):
            gen.selected_from_report(fake_report())
    def test_36_exact_frozen_windows(self):
        raw=fake_report()
        entries=gen.selected_from_report(raw,hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(entries),36)
        self.assertEqual(sum(x["policy"]=="H_REVERSAL_PRICE_ONLY" for x in entries),18)
        sql=gen.make_sql(entries)
        self.assertIn("dex_solana.trades",sql)
        self.assertIn("INTERVAL '1' HOUR",sql)
        self.assertIn("t.project_main_id=w.target_pool",sql)
    def test_tx_dedup_same_direction(self):
        targets=[dict(coin_id="coin0",observed_at="2026-10-02 02:37:00",pool="pool0",policy="H_MOMENTUM_PRICE_ONLY")]
        row=dict(coin_id="coin0",observed_at=targets[0]["observed_at"],target_pool="pool0",
                 block_time="2026-10-02 02:20:00",tx_id="tx1",trader_id="a",
                 project_main_id="pool0",raw_leg_side="BUY",direct_pool_id_match="true")
        out=red.evaluate([row,row],targets)
        self.assertEqual(out["windows"][0]["economic_tx_buy"],1)
        self.assertEqual(out["windows"][0]["economic_tx_sell"],0)
        self.assertEqual(out["windows"][0]["status"],"PRELIMINARY_FLOW_REJECT")
    def test_mixed_buy_sell_same_tx_not_counted(self):
        targets=[dict(coin_id="coin0",observed_at="2026-10-02 02:37:00",pool="pool0",policy="H_MOMENTUM_PRICE_ONLY")]
        row=dict(coin_id="coin0",observed_at=targets[0]["observed_at"],target_pool="pool0",
                 block_time="2026-10-02 02:20:00",tx_id="tx1",trader_id="a",
                 project_main_id="pool0",raw_leg_side="BUY",direct_pool_id_match="true")
        sell=dict(row,raw_leg_side="SELL")
        out=red.evaluate([row,sell],targets)
        self.assertEqual(out["windows"][0]["economic_tx_buy"],0)
        self.assertEqual(out["windows"][0]["economic_tx_sell"],0)
        self.assertEqual(out["windows"][0]["ambiguous_tx"],1)
    def test_no_rows_never_called_zero_real_trades(self):
        targets=[dict(coin_id="coin0",observed_at="2026-10-02 02:37:00",pool="pool0",policy="H_MOMENTUM_PRICE_ONLY")]
        result=red.evaluate([],targets)
        self.assertEqual(result["windows"][0]["status"],"COVERAGE_UNVERIFIED")
    def test_wrong_pool_not_counted(self):
        targets=[dict(coin_id="coin0",observed_at="2026-10-02 02:37:00",pool="pool0",policy="H_MOMENTUM_PRICE_ONLY")]
        row=dict(coin_id="coin0",observed_at=targets[0]["observed_at"],target_pool="pool0",
                 block_time="2026-10-02 02:20:00",tx_id="tx1",trader_id="a",
                 project_main_id="pool_other",raw_leg_side="BUY",direct_pool_id_match="false")
        out=red.evaluate([row],targets)
        self.assertEqual(out["windows"][0]["status"],"COVERAGE_UNVERIFIED")
        self.assertEqual(out["windows"][0]["unmapped_other_pool_legs"],1)
    def test_no_future_trade(self):
        targets=[dict(coin_id="coin0",observed_at="2026-10-02 02:37:00",pool="pool0",policy="H_MOMENTUM_PRICE_ONLY")]
        row=dict(coin_id="coin0",observed_at=targets[0]["observed_at"],target_pool="pool0",
                 block_time="2026-10-02 02:40:00",tx_id="tx1",trader_id="a",
                 project_main_id="pool0",raw_leg_side="BUY",direct_pool_id_match="true")
        out=red.evaluate([row],targets)
        self.assertEqual(out["invalid"]["lookahead_or_wrong_window"],1)

if __name__=="__main__":unittest.main()
