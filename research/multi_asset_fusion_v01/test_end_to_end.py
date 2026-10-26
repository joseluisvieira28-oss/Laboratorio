"""Synthetic temporary source fixtures only; no fabricated market results saved."""
import csv, io, json, tempfile, unittest, zipfile
from pathlib import Path
import audit
import replay as r

class FullPipelineTests(unittest.TestCase):
    def test_raw_source_to_second_arithmetic_replay_and_corruption(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_FUSION_TEST_') as tmp:
            root=Path(tmp);cache=root/'archives';cache.mkdir();out=root/'results';out.mkdir()
            for kind,a,tf,y,m,name,url in r.inventory():
                step=86_400_000 if tf=='1d' else 3_600_000
                first=r.stamp(r.dt.datetime(y,m,1,tzinfo=r.UTC))
                count=r.calendar.monthrange(y,m)[1]*(1 if tf=='1d' else 24)
                text=io.StringIO();writer=csv.writer(text)
                for i in range(count):
                    t=first+i*step;op=100+(t//step)%47;cl=op+.1
                    writer.writerow([t,op,cl+1,op-1,cl,5,t+step-1,0,1,0,0,0])
                b=io.BytesIO()
                with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(name[:-4]+'.csv',text.getvalue())
                raw=b.getvalue();file=cache/r.cache_name(kind,name);file.write_bytes(raw)
                Path(str(file)+'.CHECKSUM').write_text(r.sha(raw)+'  '+name)
            candles,manifest=r.load_archives(cache);rows=r.reconstruct(candles)
            r.write_json(out/'manifest.json',manifest)
            report={'source_manifest_sha256':r.sha((out/'manifest.json').read_bytes()),'results':r.summarize(rows)}
            inference=r.inference(rows)
            self.assertEqual(len(inference['tests']),25)
            self.assertEqual(inference['asset_order'],list(r.ASSETS))
            self.assertTrue(all(t['asset']!='AVAXUSDT' and t['p_holm_25']==1 for t in inference['tests']))
            self.assertTrue(all(t['delta_bps_day']==0 and t['ci95']==[0,0] for t in inference['tests']))
            r.write_json(out/'report.json',report)
            def write_rows():
                with (out/'daily.csv').open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            write_rows();receipt=audit.audit(cache,out)
            self.assertEqual(receipt['ledger_rows'],4380);self.assertEqual(receipt['verified_pairs'],319)
            rows[0]['gross_bps']+=1;write_rows()
            with self.assertRaisesRegex(ValueError,'GROSS'):audit.audit(cache,out)
            rows[0]['gross_bps']-=1;write_rows()
            report['results']['SOLUSDT']['14']['fusion']['total_net_bps']+=1
            r.write_json(out/'report.json',report)
            with self.assertRaisesRegex(ValueError,'TOTAL_OR_COUNT'):audit.audit(cache,out)
            first_zip=next(cache.glob('*.zip'));first_zip.write_bytes(first_zip.read_bytes()+b'x')
            with self.assertRaisesRegex(ValueError,'SOURCE_HASH'):audit.audit(cache,out)
if __name__=='__main__':unittest.main()
