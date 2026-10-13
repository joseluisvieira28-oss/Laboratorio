"""No network test of post-boundary source collector. No real prices, no orders."""
import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import public_future_source as src
import forward_boundary_gate as guard

class SourceTest(unittest.TestCase):
    def test_prior_boundary_rejects_before_network(self):
        bad=dt.datetime(2026,10,13,12,0,tzinfo=dt.timezone.utc)
        with patch.object(src,"fetch_json",side_effect=AssertionError("NETWORK_FORBIDDEN")) as req:
            with self.assertRaisesRegex(ValueError,"FORWARD_NOT_READY"):
                src.collect(bad)
            req.assert_not_called()
    def test_insufficient_forward_warmup_rejects(self):
        at=dt.datetime(2026,10,22,8,30,tzinfo=dt.timezone.utc)
        with patch.object(src,"fetch_json",side_effect=AssertionError("NETWORK_FORBIDDEN")) as req:
            with self.assertRaisesRegex(ValueError,"FORWARD_NOT_READY"):
                src.collect(at)
            req.assert_not_called()
    def test_forbidden_endpoint_rejects_before_network(self):
        with self.assertRaisesRegex(ValueError,"FORBIDDEN_ENDPOINT"):
            src.fetch_json("/fapi/v1/order",{},[])
    def test_full_readonly_source_schema(self):
        n=202
        bars=[{"t":guard.BOUNDARY+i*guard.H,"open":100.,"high":101.,
               "low":99.,"close":100.,"volume":100.} for i in range(n)]
        marks=[{k:v for k,v in b.items() if k!="volume"} for b in bars]
        enough=dt.datetime.fromtimestamp((guard.BOUNDARY+202*guard.H)/1000,dt.timezone.utc)
        with patch.object(src,"paginated_klines",side_effect=[bars,marks]) as klines:
            with patch.object(src,"paginated_funding",return_value={}) as funding:
                result=src.collect(enough)
                self.assertEqual(len(result["bars"]),202)
                self.assertEqual(result["authority"],"PUBLIC_READ_ONLY_SHADOW")
                self.assertEqual(result["forward_boundary_utc"],"2026-10-14T00:00:00Z")
                guard.validate(result)
                self.assertEqual(klines.call_count,2)
                funding.assert_called_once()
if __name__=="__main__":unittest.main()
