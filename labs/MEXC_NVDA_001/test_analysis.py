"""Meaningful timing and split-isolation checks using synthetic data only."""
import contextlib,io,json,pathlib,tempfile,unittest
import analyze
class TimingTests(unittest.TestCase):
    def test_next_open_and_split_no_same_close_fill(self):
        with contextlib.nullcontext(str(analyze.ROOT/'test_work')) as folder:
            assert pathlib.Path(folder).resolve().is_relative_to(analyze.ROOT.resolve())
            root=pathlib.Path(folder); root.mkdir(exist_ok=True); raw=root/'raw'; raw.mkdir(exist_ok=True); start=1788480000
            for label in ['last','index','fair']:
                times=[start+d*86400+i*60 for d in range(32) for i in range(10)]
                d={'time':times,'open':[101 if label=='last' else 100]*len(times),'close':[99.7 if label=='last' and i%10==0 else 100 for i in range(len(times))],'vol':[1]*len(times)}
                (raw/f'{label}_0.json').write_text(json.dumps({'response':{'success':True,'data':d}}))
            (raw/'contract_detail.json').write_text(json.dumps({'response':{'data':[]}}))
            (raw/'spot_exchange_info.json').write_text(json.dumps({'response':{'symbols':[]}}))
            previous=analyze.ROOT
            try:
                analyze.ROOT=root
                with contextlib.redirect_stdout(io.StringIO()): analyze.main()
                r=json.loads((root/'results.json').read_text())
                for n,count in [('Discovery',16),('OOS',8),('Holdout',8)]:
                    s=r['H2']['index'][n]['fee_only']; self.assertEqual(s['signals'],count); self.assertAlmostEqual(s['mean_bps'],-16)
                    self.assertIsNone(s['ci99_day_block'])
                self.assertLess(r['coverage_within_observed_span'],0.1)
            finally: analyze.ROOT=previous
    def test_no_confidence_from_one_day(self):
        self.assertIsNone(analyze.ci_by_day([(1,100),(2,100)]))
if __name__=='__main__': unittest.main()
