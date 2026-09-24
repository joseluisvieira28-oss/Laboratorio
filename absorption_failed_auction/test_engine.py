import importlib.util, unittest
spec=importlib.util.spec_from_file_location("m","absorption_failed_auction/engine.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class T(unittest.TestCase):
    def test_sensor_block(self):
        self.assertEqual(m.adjudicate([],"PASS_LIMITED")["classification"],"SENSOR_BLOCKED")
    def test_classifier(self):
        rows=[]
        for i in range(289):
            rows.append({
              "agg_delta_pct":0.1,
              "ltf_path_efficiency":0.5,
              "bar_return_bps":5.0,
              "poc_migration_bps":1.0
            })
        rows[-1]={"agg_delta_pct":0.9,"ltf_path_efficiency":0.1,"bar_return_bps":-1.0,"poc_migration_bps":-1.0}
        out=m.classify(rows)
        self.assertEqual(out[-1]["event_class"],"FAILED_AUCTION")
    def test_insufficient(self):
        rows=[{"event_class":"FAILED_AUCTION","utc_date":"2026-01-01","R60":-1.0}]
        self.assertEqual(m.adjudicate(rows,"PASS_STRONG")["classification"],"INSUFFICIENT_SAMPLE")
    def test_wilson(self):
        self.assertGreater(m.wilson_lower(80,100),0.7)

if __name__=="__main__": unittest.main()
