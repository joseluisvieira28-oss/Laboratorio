"""All fixtures below are SYNTHETIC, never empirical market validation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from second_wave import find_signal, simulate, load, analyze

def trade(t, price, wallet="u", side="buy", usd=150., liq=60000.):
    return dict(mint="TEST_MINT", timestamp=1700000000+t, tx="tx-"+str(t),
                wallet=wallet, side=side, price_usd=price,
                amount_usd=usd, liquidity_usd=liq, source="SYNTHETIC_TEST")

def fixture(continued=True):
    tape = [trade(t,1+t/900.,wallet="p"+str(t)) for t in range(0,181,30)]
    tape += [trade(210,1., "s1","sell"),trade(240,.80,"s2","sell"),
             trade(270,.66,"s3","sell")]
    tape += [trade(300+20*j,.66+.015*j,wallet="buyer"+str(j),usd=200) for j in range(9)]
    if continued:
        tape += [trade(520,.89,"later"),trade(630,.94,"later2"),trade(2400,1.16,"later3")]
    return tape

class Tests(unittest.TestCase):
    def test_asof_no_future_price(self):
        tape=fixture()
        signal=find_signal(tape)
        self.assertIsNotNone(signal)
        self.assertLess(signal["index"],len(tape)-1)
        self.assertEqual(find_signal(tape[:signal["index"]+1])["at"],signal["at"])

    def test_one_address_does_not_pass(self):
        tape=fixture()
        for r in tape:
            if r["wallet"].startswith("buyer"):
                r["wallet"]="same_wallet"
        self.assertIsNone(find_signal(tape))

    def test_low_liquidity_rejects(self):
        tape=fixture()
        for r in tape: r["liquidity_usd"]=100
        self.assertIsNone(find_signal(tape))

    def test_missing_exit_censored(self):
        tape=fixture(False)
        s=find_signal(tape)
        self.assertIsNotNone(s)
        result=simulate(tape,s)
        self.assertEqual(result["status"],"EXIT_UNOBSERVED")
        self.assertIsNone(result["net_return_pct"])

    def test_costs_and_no_go(self):
        tape=fixture()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"events.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in tape)+"\n")
            result=analyze(path)
        self.assertEqual(result["signals"],1)
        self.assertEqual(result["print_proxy_outcomes"],1)
        self.assertIn("NO-GO",result["gate"])

    def test_duplicate_and_invalid(self):
        r=trade(1,1)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"events.jsonl"
            path.write_text(json.dumps(r)+"\n"+json.dumps(r)+"\n{not_json}")
            rows,quality=load(path)
        self.assertEqual(len(rows),1)
        self.assertEqual(quality["invalid"],1)
        self.assertEqual(quality["duplicate"],1)

if __name__ == "__main__": unittest.main()
