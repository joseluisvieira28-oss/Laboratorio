import copy, datetime as dt, io, json, tempfile, unittest, zipfile
from pathlib import Path
import numpy as np
import replay as r

def fixture(mutate=None,extra=False):
    start=r.stamp(dt.datetime(2022,1,1,tzinfo=r.UTC)); step=86_400_000
    rows=[[str(start+i*step),'100','102','99','101','10',str(start+(i+1)*step-1),'0','1','0','0','0'] for i in range(31)]
    if mutate: mutate(rows)
    b=io.BytesIO();name='BTCUSDT-1d-2022-01.zip'
    with zipfile.ZipFile(b,'w') as z:
        z.writestr(name[:-4]+'.csv','\n'.join(','.join(row) for row in rows))
        if extra:z.writestr('../other.csv','x')
    raw=b.getvalue();return raw,(r.sha(raw)+'  '+name).encode(),name
class ArchiveTests(unittest.TestCase):
    def parse(self,**kw):
        raw,ch,name=fixture(**kw);return r.parse_archive(raw,ch,name,'1d',2022,1)
    def test_valid_complete_month(self):self.assertEqual(len(self.parse()),31)
    def test_duplicate(self):
        with self.assertRaisesRegex(r.GateError,'DUPLICATE'):self.parse(mutate=lambda x:x.append(x[0]))
    def test_missing(self):
        with self.assertRaisesRegex(r.GateError,'INCOMPLETE'):self.parse(mutate=lambda x:x.pop())
    def test_nan(self):
        with self.assertRaisesRegex(r.GateError,'BAD_PRICE'):self.parse(mutate=lambda x:x[0].__setitem__(1,'nan'))
    def test_ohlc(self):
        with self.assertRaisesRegex(r.GateError,'OHLC'):self.parse(mutate=lambda x:x[0].__setitem__(2,'90'))
    def test_bad_clock(self):
        with self.assertRaisesRegex(r.GateError,'CLOCK'):self.parse(mutate=lambda x:x[0].__setitem__(6,'0'))
    def test_holdout(self):
        with self.assertRaisesRegex(r.GateError,'CLOCK_OR_HOLDOUT'):self.parse(mutate=lambda x:x[0].__setitem__(0,str(r.stamp(dt.datetime(2024,1,1,tzinfo=r.UTC)))))
    def test_members(self):
        with self.assertRaisesRegex(r.GateError,'ZIP_MEMBERS'):self.parse(extra=True)
    def test_hash(self):
        raw,ch,name=fixture()
        with self.assertRaisesRegex(r.GateError,'CHECKSUM_MISMATCH'):r.parse_archive(raw+b'x',ch,name,'1d',2022,1)
    def test_checksum_filename(self):
        raw,ch,name=fixture()
        with self.assertRaisesRegex(r.GateError,'CHECKSUM_FILENAME'):r.parse_archive(raw,ch+b'bad',name,'1d',2022,1)
    def test_wrong_width(self):
        with self.assertRaisesRegex(r.GateError,'ROW_WIDTH'):self.parse(mutate=lambda x:x[0].pop())
    def test_inventory(self):
        inv=list(r.inventory());self.assertEqual(len(inv),319)
        self.assertTrue(all((i[3],i[4]) in r.MONTHS for i in inv))
        self.assertFalse(any('/2024' in i[-1] for i in inv))
    def test_missing_cache(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaisesRegex(r.GateError,'MISSING_ARCHIVE'):r.load_archives(Path(p))
class ScienceTests(unittest.TestCase):
    def synthetic(self):
        candles={}
        for kind,a,tf in r.specs():
            d={};step=dt.timedelta(days=1) if tf=='1d' else dt.timedelta(hours=1)
            start=dt.datetime(2021,12,1,tzinfo=r.UTC) if tf=='1d' else r.START
            t=start;i=0
            while t<dt.datetime(2024,1,1,tzinfo=r.UTC):
                # Changing closes, daily open prices independent of next day's return.
                d[r.stamp(t)]=(100+i*.01,100+i*.02);t+=step;i+=1
            candles[kind,a,tf]=d
        return candles
    def test_causal_invariance(self):
        c=self.synthetic();before=r.reconstruct(c)
        # Change current-day close, which must not affect that day's signal.
        target=r.START+dt.timedelta(days=30);key=('futures/um','SOLUSDT','1d')
        c[key][r.stamp(target)]=(100,1)
        after=r.reconstruct(c);i=30
        self.assertEqual(before[i],after[i]);self.assertNotEqual(before[i+1]['asset20'],after[i+1]['asset20'])
    def test_hours_and_cost_once(self):
        rows=r.reconstruct(self.synthetic());self.assertEqual(len(rows),4380)
        row=rows[0];self.assertTrue(row['entry_utc'].endswith('01:00:00+00:00'))
        self.assertTrue(row['exit_utc'].endswith('02:00:00+00:00'))
        self.assertAlmostEqual(r.ledger([row],'fusion',14)[0],row['gross_bps']-14)
    def test_flat_no_cost(self):
        row={'gross_bps':123,'fusion':False}
        self.assertEqual(r.ledger([row],'fusion',20)[0],0)
    def test_short_pnl(self):
        self.assertEqual(r.side(100,90),-1)
        self.assertAlmostEqual(-1*(99/100-1)*10000,100)
    def test_zero_signal(self):self.assertEqual(r.side(1,1),0)
    def test_missing_required_bar(self):
        c=self.synthetic();del c['spot','BTCUSDT','1d'][r.stamp(r.START-dt.timedelta(days=21))]
        with self.assertRaisesRegex(r.GateError,'CAUSAL_BAR_MISSING'):r.reconstruct(c)
    def test_calendar_denominator(self):
        m=r.metrics([10,0,-4],[True,False,True]);self.assertEqual(m['mean_bps_per_calendar_day'],2)
        self.assertEqual(m['mean_bps_per_trade'],3)
        self.assertEqual(m['remove_top_winners_total']['3'],-4)
    def test_drawdown_from_initial_zero(self):self.assertEqual(r.metrics([-3,1,-4],[True]*3)['max_drawdown_bps'],6)
    def test_holm_monotone(self):self.assertEqual(r.holm([.01,.04,.02]),[.03,.04,.04])
    def test_listing_reject_late_and_wrong_venue(self):
        valid=json.loads(Path(__file__).with_name('listings.json').read_text())
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/'l.json'
            for change in ({'launch_utc':'2022-01-01T00:00:00Z'},{'venue':'Binance Spot'}):
                v=copy.deepcopy(valid);v['SOLUSDT'].update(change);f.write_text(json.dumps(v))
                with self.assertRaises(r.GateError):r.listing_gate(f)
if __name__=='__main__':unittest.main()
