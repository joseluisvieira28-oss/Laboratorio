"""Offline integration of scheduled prior-expiry reconciliation; no actual network."""
import datetime as dt
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import probe
import settle_prior
from test_audit_forward import synthetic_archive

REAL_DATETIME=dt.datetime
UTC=dt.timezone.utc

class FrozenClock(REAL_DATETIME):
    @classmethod
    def now(cls,tz=None):
        return REAL_DATETIME(2026,11,6,8,5,30,tzinfo=UTC)

class PriorReconciliationTests(unittest.TestCase):
    def test_absent_eligible_entry_never_calls_market(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            evidence=root/"evidence"; evidence.mkdir()
            request=root/"request.json";request.write_text('{"date":"2026-11-06"}')
            with patch("probe.settlement",side_effect=AssertionError("not eligible")):
                result=settle_prior.run(request,evidence,root/"work")
            self.assertEqual(result["status"],"NO_ELIGIBLE_EXPIRED_ENTRY_TO_SETTLE")

    def test_exactly_one_official_delivery_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);evidence=root/"evidence"
            dated=evidence/"2026-11-04";dated.mkdir(parents=True)
            entry=synthetic_archive()
            (dated/"entry-session.zip").write_bytes(entry)
            (dated/"entry-session-archive.json").write_text(json.dumps(
                {"sha256":hashlib.sha256(entry).hexdigest()}))
            request=root/"request.json";request.write_text('{"date":"2026-11-06"}')
            calls=[]
            def one_get(source,name,method,**params):
                self.assertEqual(name,"settlement")
                self.assertEqual(method,"get_delivery_prices")
                calls.append(1)
                data={"data":[{"date":"2026-11-05","delivery_price":80000}]}
                raw=json.dumps({"testnet":False,"result":data}).encode()
                (source.root/"settlement.json").write_bytes(raw)
                source.manifest.append(dict(name="settlement",
                    url="https://www.deribit.com/api/v2/public/get_delivery_prices?index_name=btc_usdc&count=100",
                    started="2026-11-06T08:05:30+00:00",
                    received="2026-11-06T08:05:31+00:00",
                    sha256=hashlib.sha256(raw).hexdigest()))
                return data
            with patch("probe.dt.datetime",FrozenClock),patch.object(probe.Source,"get",one_get):
                result=settle_prior.run(request,evidence,root/"work")
            self.assertEqual(result["status"],"OFFICIAL_SETTLEMENT_INDEPENDENTLY_AUDITED_NOT_EDGE")
            self.assertEqual(len(calls),1)
            self.assertTrue((dated/"settlement-2026-11-06.zip").exists())
            self.assertTrue((dated/"settlement-audit-2026-11-06.json").exists())
            with patch("probe.settlement",side_effect=AssertionError("no duplicate")):
                again=settle_prior.run(request,evidence,root/"work-again")
            self.assertEqual(again["status"],"NO_ELIGIBLE_EXPIRED_ENTRY_TO_SETTLE")

if __name__=="__main__":unittest.main()
