import unittest
from decimal import Decimal
from radar.near_mexc_scout import observe, sweep
from radar.market import MEXCFuturesPublicFeed, MarketDataError


class ScoutTests(unittest.TestCase):
    def test_depth_sweep_contract_volume_and_partial_levels(self):
        self.assertEqual(sweep([[5, 2, 1], [6, 10, 1]], Decimal(4)), Decimal('5.5'))
        with self.assertRaises(ValueError):
            sweep([[5, 2, 1]], Decimal(3))

    def test_source_outage_fails_closed(self):
        class Down:
            def _get_json(self, path):
                raise MarketDataError('public endpoint unavailable')
        result = observe(Down())
        self.assertEqual(result['verdict'], 'NO_TRADE')
        self.assertEqual(result['classification'], 'SOURCE_BLOCKED')
        self.assertFalse(result['execution_armed'])

    def test_private_endpoint_denied_before_network(self):
        with self.assertRaises(MarketDataError):
            MEXCFuturesPublicFeed()._get_json('/api/v1/private/order/submit')


if __name__ == '__main__':
    unittest.main()
