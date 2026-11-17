#!/usr/bin/env python3
"""Offline synthetic tests. No public network, no exchange/ETH endpoint."""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import onchain_source_probe as p

def make_log(topic,token_id,data):
    return {"address":p.MANAGER,"topics":[topic,p.topicid(token_id)],
            "data":"0x"+"".join(format(x,"064x") for x in data)}

class TestEthereumProof(unittest.TestCase):
    def test_pinned_event_signature_hashes(self):
        self.assertEqual(p.INCREASE,"0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f")
        self.assertEqual(p.DECREASE,"0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4")
        self.assertEqual(p.COLLECT,"0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01")
    def test_decrease_is_not_fee(self):
        d=p.decode_event(make_log(p.DECREASE,102244,[123,10**18,7*10**6]),102244)
        self.assertEqual(d["type"],"DecreaseLiquidity")
        self.assertEqual(d["amount0_raw"],10**18)
        self.assertEqual(d["amount1_raw"],7*10**6)
    def test_collect_contains_principal_and_fee(self):
        d=p.decode_event(make_log(p.COLLECT,102244,[int("1234567890abcdef1234567890abcdef12345678",16),3*10**18,2*10**6]),102244)
        self.assertEqual(d["recipient"],"0x1234567890abcdef1234567890abcdef12345678")
        self.assertEqual(d["fee_attribution"],"UNKNOWN_COLLECT_INCLUDES_WITHDRAWN_PRINCIPAL")
    def test_wrong_token_or_contract_is_ignored(self):
        x=make_log(p.INCREASE,102244,[1,2,3])
        self.assertIsNone(p.decode_event(x,102245))
        x["address"]=p.POOL
        self.assertIsNone(p.decode_event(x,102244))
    def test_malformed_abi_is_rejected(self):
        with self.assertRaises(ValueError):
            p.decode_event(make_log(p.COLLECT,102244,[1,2]),102244)
    def test_transaction_gas_units(self):
        self.assertEqual(p.gas_eth({"gasUsed":hex(150000),"effectiveGasPrice":hex(40_000_000_000)}),"0.006")
        self.assertIsNone(p.gas_eth({"gasUsed":"0x1"}))
    def test_read_only_offline_guard(self):
        from subprocess import run
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"out.json"
            pr=run([sys.executable,p.__file__,"--offline","--output",str(out)],
                   capture_output=True,text=True,check=True)
            z=json.loads(out.read_text())
            self.assertEqual(z["state"],"SOURCE_BLOCKED_OFFLINE_MODE")
            self.assertEqual(z["economic_verdict"],"NO_LIVE_GO")
            self.assertIsNone(z["pnl_usd"])
    def test_no_private_keys_or_send_rpc(self):
        import inspect
        src=inspect.getsource(p)
        self.assertNotIn("eth_sendRawTransaction",src)
        self.assertNotIn("eth_sendTransaction",src)
        self.assertNotIn("PRIVATE_KEY",src)

if __name__=="__main__":unittest.main()
