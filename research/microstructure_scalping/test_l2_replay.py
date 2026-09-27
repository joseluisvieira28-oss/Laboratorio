import unittest
from research.microstructure_scalping.l2_replay import L2Replay


class ReplayTests(unittest.TestCase):
    def msg(self, typ, ts, u, seq, bids, asks):
        return {"type":typ,"ts":ts,"cts":ts-1,
                "data":{"u":u,"seq":seq,"b":bids,"a":asks}}

    def test_snapshot_delta_features(self):
        r=L2Replay()
        s=r.apply(self.msg("snapshot",1000,1,10,
            [["100","2"],["99","3"]],[["101","1"],["102","4"]]))
        self.assertEqual(s.best_bid,100)
        self.assertEqual(s.best_ask,101)
        self.assertGreater(s.microprice,s.mid)
        d=r.apply(self.msg("delta",1100,2,11,[["100","0"],["100.5","5"]],[]))
        self.assertEqual(d.best_bid,100.5)
        self.assertEqual(d.best_ask,101)

    def test_delta_before_snapshot_fails(self):
        r=L2Replay()
        with self.assertRaisesRegex(ValueError,"delta_before_snapshot"):
            r.apply(self.msg("delta",1000,1,1,[["100","1"]],[["101","1"]]))

    def test_crossed_book_fails(self):
        r=L2Replay()
        with self.assertRaisesRegex(ValueError,"crossed_or_locked_book"):
            r.apply(self.msg("snapshot",1000,1,1,[["101","1"]],[["101","1"]]))

    def test_nonmonotonic_timestamp_fails(self):
        r=L2Replay()
        r.apply(self.msg("snapshot",1000,1,1,[["100","1"]],[["101","1"]]))
        with self.assertRaisesRegex(ValueError,"nonmonotonic_ts"):
            r.apply(self.msg("delta",999,2,2,[],[]))


if __name__=="__main__":
    unittest.main()
