import os,unittest
from unittest.mock import patch
from scripts.mexc_tier2_futures_preflight_v03 import run

class Tier2FuturesPreflightTests(unittest.TestCase):
    def test_wrong_local_api_key_binding_fails_before_network(self):
        with patch.dict(os.environ,{"MEXC_API_KEY":"abc","MEXC_API_SECRET":"secret"},clear=False):
            out=run(binding_sha256="0"*64)
        self.assertFalse(out["pass"])
        self.assertIn("LOCAL_API_KEY_BINDING_MISMATCH",out["blockers"])

if __name__=="__main__": unittest.main()
