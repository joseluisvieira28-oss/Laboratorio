import unittest
from research.microstructure_scalping.dataset_builder_v01 import build_rows


def snapshot(ts,bid,ask,u):
    return {"type":"snapshot","ts":ts,"cts":ts-1,
            "data":{"u":u,"seq":u,"b":[[str(bid),"1"]],"a":[[str(ask),"1"]]}}


class DatasetTests(unittest.TestCase):
    def test_future_label_uses_first_state_at_or_after_horizon(self):
        messages=[
            snapshot(0,100,102,1),
            snapshot(80,101,103,2),
            snapshot(120,102,104,3),
            snapshot(620,103,105,4),
        ]
        rows=build_rows(messages,horizons_ms=(100,500))
        first=rows[0]
        self.assertEqual(first["event_time_ms"],-1)
        self.assertEqual(first["fwd_mid_100ms"],103.0)
        self.assertEqual(first["fwd_mid_500ms"],104.0)
        self.assertEqual(first["fwd_bid_100ms"],102.0)
        self.assertEqual(first["fwd_ask_100ms"],104.0)

    def test_feature_at_t_does_not_change_after_future_messages(self):
        messages=[
            snapshot(0,100,102,1),
            snapshot(100,110,112,2),
            snapshot(200,120,122,3),
        ]
        rows=build_rows(messages,horizons_ms=(100,))
        self.assertEqual(rows[0]["mid"],101.0)
        self.assertEqual(rows[0]["fwd_mid_100ms"],111.0)

    def test_anchor_interval_reduces_overlapping_samples(self):
        messages=[snapshot(t,100+t/1000,102+t/1000,i+1)
                  for i,t in enumerate(range(0,1001,100))]
        rows=build_rows(messages,horizons_ms=(100,),anchor_interval_ms=500)
        self.assertEqual([r["ts"] for r in rows],[0,500])

    def test_cts_is_primary_clock(self):
        m={"type":"snapshot","ts":1005,"cts":1000,
           "data":{"u":1,"seq":1,"b":[["100","1"]],"a":[["101","1"]]}}
        n={"type":"snapshot","ts":1110,"cts":1100,
           "data":{"u":2,"seq":2,"b":[["101","1"]],"a":[["102","1"]]}}
        rows=build_rows([m,n],horizons_ms=(100,))
        self.assertEqual(rows[0]["event_time_ms"],1000)
        self.assertEqual(rows[0]["label_time_100ms"],1100)


if __name__=="__main__":
    unittest.main()
