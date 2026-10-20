"""Adversarial checks against the unchanged parent mechanism outcome firewall."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PARENT = Path(__file__).with_name('cbeth_mechanism_discovery_v01.py').resolve()


class ParentFirewall(unittest.TestCase):
    def exercise(self, states, last_day='2024-07-01'):
        temp_root = (Path.cwd() / 'artifacts/firewall_tests').resolve()
        assert Path.cwd().resolve() in temp_root.parents
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as tmp:
            root = Path(tmp)
            here = root / 'research/cbeth_redemption_basis_001'
            here.mkdir(parents=True)
            data = {
                'PREDICTOR_CENSUS_RECEIPT_V0.1.json': {'classification': 'PREDICTOR_CENSUS_PASS', 'row_set_sha256': 'synthetic'},
                'PREDICTOR_CENSUS_ROWS_V0.1.json': {'row_set_sha256': 'synthetic', 'rows': []},
                'DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json': {'classification': 'PREDICTOR_SAMPLE_PASS', 'future_mechanism_outcomes_opened': False, 'transition_event_count': len(states)},
                'DISCOVERY_PREDICTOR_SAMPLE_ROWS_V0.1.json': {'events': [{'utc_day': last_day, 'state': s} for s in states]},
            }
            for name, obj in data.items():
                (here / name).write_text(json.dumps(obj))
            p = subprocess.run([sys.executable, str(PARENT)], cwd=root, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
            result = json.loads((here / 'MECHANISM_DISCOVERY_RESULT_V0.1.json').read_text())
            self.assertEqual(result['classification'], 'MECHANISM_OUTCOME_INSUFFICIENT_SAMPLE')
            self.assertFalse(result['future_mechanism_outcomes_opened'])
            self.assertEqual(result['rows'], [])
            self.assertFalse(result['protected_2026_opened'])

    def test_under_total_minimum_without_any_future_data(self):
        self.exercise(['DISCOUNT_EXTREME'] * 9 + ['PREMIUM_EXTREME'] * 10)

    def test_one_tail_below_minimum_without_any_future_data(self):
        self.exercise(['DISCOUNT_EXTREME'] * 5 + ['PREMIUM_EXTREME'] * 20)

    def test_boundary_censor_cannot_rescue_count(self):
        self.exercise(['DISCOUNT_EXTREME'] * 10 + ['PREMIUM_EXTREME'] * 10, '2024-12-20')


if __name__ == '__main__':
    unittest.main()
