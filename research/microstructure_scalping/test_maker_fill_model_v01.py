import unittest
from research.microstructure_scalping.maker_fill_model_v01 import Trade, full_passive_fill


class MakerFillModelTests(unittest.TestCase):
    def test_touch_without_trade_is_not_fill(self):
        r=full_passive_fill(order_side="Buy",price=100,order_size=1,
            displayed_queue_ahead=2,effective_placement_ms=1000,deadline_ms=2000,trades=[])
        self.assertFalse(r.filled)

    def test_wrong_aggressor_side_does_not_fill(self):
        trades=[Trade(1100,"Buy",100,10)]
        r=full_passive_fill(order_side="Buy",price=100,order_size=1,
            displayed_queue_ahead=2,effective_placement_ms=1000,deadline_ms=2000,trades=trades)
        self.assertFalse(r.filled)

    def test_exact_price_volume_must_consume_queue_and_order(self):
        trades=[Trade(1100,"Sell",100,1.5),Trade(1200,"Sell",100,1.4),Trade(1300,"Sell",100,0.2)]
        r=full_passive_fill(order_side="Buy",price=100,order_size=1,
            displayed_queue_ahead=2,effective_placement_ms=1000,deadline_ms=2000,trades=trades)
        self.assertTrue(r.filled)
        self.assertEqual(r.fill_time_ms,1300)

    def test_trade_through_is_not_credited(self):
        trades=[Trade(1100,"Sell",99.5,100)]
        r=full_passive_fill(order_side="Buy",price=100,order_size=1,
            displayed_queue_ahead=2,effective_placement_ms=1000,deadline_ms=2000,trades=trades)
        self.assertFalse(r.filled)

    def test_queue_multiplier_is_conservative(self):
        trades=[Trade(1100,"Sell",100,4)]
        r1=full_passive_fill(order_side="Buy",price=100,order_size=1,
            displayed_queue_ahead=2,effective_placement_ms=1000,deadline_ms=2000,trades=trades,queue_multiplier=1)
        r2=full_passive_fill(order_side="Buy",price=100,order_size=1,
            displayed_queue_ahead=2,effective_placement_ms=1000,deadline_ms=2000,trades=trades,queue_multiplier=2)
        self.assertTrue(r1.filled)
        self.assertFalse(r2.filled)

    def test_trade_at_placement_timestamp_not_credited(self):
        trades=[Trade(1000,"Sell",100,100)]
        r=full_passive_fill(order_side="Buy",price=100,order_size=1,
            displayed_queue_ahead=0,effective_placement_ms=1000,deadline_ms=2000,trades=trades)
        self.assertFalse(r.filled)


if __name__=="__main__":
    unittest.main()
