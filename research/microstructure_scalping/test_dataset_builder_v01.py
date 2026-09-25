import unittest
from research.microstructure_scalping.dataset_builder_v01 import build_rows


def msg(ts,bid,ask,u):
    return {"type":"snapshot" if u==1 else "delta","ts":ts,"cts":ts-1,
            "data":{"u":u,"seq":u,"b":[[str(bid),"1"]],"a":[[str(ask),"1"]]}}


class DatasetTests(unittest.TestCase):
    def test_future_label_uses_first_state_at_or_after_horizon(self):
        messages=[
            msg(0,100,102,1),
            msg(80,101,103,2),
            msg(120,102,104,3),
            msg(620,103,105,4),
        ]
        rows=build_rows(messages,horizons_ms=(100,500))
        first=rows[0]
        self.assertEqual(first["ts"],0)
        self.assertEqual(first["fwd_mid_100ms"],103.0)
        self.assertEqual(first["fwd_mid_500ms"],104.0)

    def test_feature_at_t_does_not_change_after_future_messages(self):
        messages=[
            msg(0,100,102,1),
            msg(100,110,112,2),
            msg(200,120,122,3),
        ]
        rows=build_rows(messages,horizons_ms=(100,))
        self.assertEqual(rows[0]["mid"],101.0)
        self.assertEqual(rows[0]["fwd_mid_100ms"],111.0)


if __name__=="__main__":
    unittest.main()
