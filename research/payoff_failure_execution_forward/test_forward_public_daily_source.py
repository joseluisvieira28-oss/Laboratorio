"""Synthetic and network-free source-gate tests for future PAYOFF shadows."""
import hashlib,io,json,sys,unittest,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parent))
import forward_public_daily_source as src
UTC=timezone.utc

class SyntheticSource(unittest.TestCase):
    def make_archive(self,day,kind="klines",skip=None):
        base=int(day.timestamp()*1000)
        rows=[]
        for i in range(24):
            if i==skip:continue
            row=[str(base+i*src.H),"100","101","99","100"]
            if kind=="klines":row.append("150")
            rows.append(",".join(row))
        import csv
        content=("\n".join(rows)+"\n").encode()
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("BTCUSDT-1h-test.csv",content)
        return buf.getvalue()

    def fake(self,data,checksum_override=None):
        def read(url,max_size=3_000_000):
            if url.endswith(".CHECKSUM"):
                return (checksum_override or hashlib.sha256(data).hexdigest()).encode()+b" synthetic.zip"
            return data
        return read

    def test_no_preboundary_or_premature_collection(self):
        with self.assertRaisesRegex(src.SourceBlocked,"WARMUP"):
            src.window(datetime(2026,10,22,23,59,tzinfo=UTC))
        d=src.window(datetime(2026,10,23,tzinfo=UTC))
        self.assertEqual(d[0],src.FIRST_DAY)
        self.assertEqual(len(d),9)
        self.assertEqual(d[-1],datetime(2026,10,22,tzinfo=UTC))

    def test_archive_markets_and_marks(self):
        date=src.FIRST_DAY
        for kind in ("klines","markPriceKlines"):
            rec,proof=src.parse_day_archive(date,kind,self.fake(self.make_archive(date,kind)))
            self.assertEqual(len(rec),24)
            self.assertEqual(proof["hourly_bars"],24)
            self.assertEqual(min(rec),int(date.timestamp()*1000))

    def test_archive_gap_closed(self):
        date=src.FIRST_DAY
        with self.assertRaisesRegex(src.SourceBlocked,"COVERAGE_INCOMPLETE"):
            src.parse_day_archive(date,"klines",self.fake(self.make_archive(date,skip=12)))

    def test_archive_checksum_closed(self):
        date=src.FIRST_DAY
        with self.assertRaisesRegex(src.SourceBlocked,"CHECKSUM_MISMATCH"):
            src.parse_day_archive(date,"klines",self.fake(self.make_archive(date),checksum_override="0"*64))

    def test_funding_range_and_normalization(self):
        start=int(src.FIRST_DAY.timestamp()*1000)
        end=start+3*src.DAY
        records=[]
        for i in range(0,3*24,8):
            records.append({"symbol":"BTCUSDT","fundingTime":start+i*src.H,"fundingRate":"0.0001"})
        def reader(url,max_size=1_000_000):
            self.assertTrue(url.startswith(src.FUND_URL+"?"))
            return json.dumps(records).encode()
        funds,receipts=src.read_funding(start,end,reader)
        self.assertEqual(len(funds),9)
        self.assertEqual(len(receipts),1)

    def test_funding_missing_edge_blocked(self):
        start=int(src.FIRST_DAY.timestamp()*1000)
        end=start+3*src.DAY
        def reader(url,max_size=1_000_000):
            return json.dumps([{"symbol":"BTCUSDT","fundingTime":start,
                                "fundingRate":"0.0001"}]).encode()
        with self.assertRaisesRegex(src.SourceBlocked,"FUNDING_EDGE"):
            src.read_funding(start,end,reader)

    def test_funding_not_an_order(self):
        with self.assertRaisesRegex(src.SourceBlocked,"UNAPPROVED_NETWORK"):
            src.get("https://fapi.binance.com/fapi/v1/order?symbol=BTCUSDT")

    def test_run_blocks_before_warmup_with_zero_network(self):
        def never(url,max_size=3_000_000):raise AssertionError("NETWORK_SHOULD_NOT_RUN")
        with self.assertRaisesRegex(src.SourceBlocked,"WARMUP"):
            src.collect(datetime(2026,10,13,tzinfo=UTC),never)

    def test_max_horizon_requires_rollover(self):
        with self.assertRaisesRegex(src.SourceBlocked,"HORIZON_LIMIT"):
            src.window(src.FIRST_DAY+timedelta(days=src.MAX_DAYS+2))

if __name__=="__main__":unittest.main()
