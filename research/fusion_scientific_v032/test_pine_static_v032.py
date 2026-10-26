import re
import unittest
from pathlib import Path

SRC = Path(__file__).with_name('Fusion_Radar_Visual_V032.pine')

class TestPineStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SRC.read_text('utf-8')

    def test_no_global_indentation_and_version(self):
        self.assertTrue(self.src.startswith('//@version=6\nindicator('))
        self.assertTrue(all(not line.startswith(' ') for line in self.src.splitlines()
                            if line and not line.startswith('    ')))

    def test_exactly_seven_daily_requests(self):
        self.assertEqual(len(re.findall(r'request\.security\(', self.src)), 7)
        self.assertEqual(self.src.count('lookahead=barmerge.lookahead_on'), 7)

    def test_confirmed_daily_not_current(self):
        for fragment in ('close[1]', 'close[21]', 'close[2]', 'close[22]'):
            self.assertIn(fragment, self.src)

    def test_no_pnl_or_execution(self):
        for forbidden in ('strategy.entry', 'strategy.exit', 'strategy.order',
                          'NET14', 'NET20', 'DD14', 'request.security_lower_tf'):
            self.assertNotIn(forbidden, self.src)

    def test_twelve_individual_alerts(self):
        self.assertEqual(self.src.count('alertcondition('), 12)

    def test_avoid_vertical_background(self):
        self.assertNotIn('bgcolor(', self.src)

    def test_no_forbidden_holdout_pnl(self):
        self.assertNotIn('2024, 1, 1', self.src)
        self.assertNotIn('2026, 1, 1', self.src)

    def test_hide_table(self):
        self.assertIn('table.clear(panel, 0, 0, 4, 7)', self.src)

if __name__ == '__main__':
    unittest.main()
