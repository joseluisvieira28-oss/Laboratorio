import unittest
from .base_keeper_source_gate_v01 import decode_liquidation, decide, GateBlocked, cost_wei, TOPIC, POOL


def ev(tx="0xabc", index="0x0",liquidator=5,block="0x100"):
    def word(x):return f"{x:064x}"
    return {
        "address":POOL,"topics":[TOPIC,"0x"+word(1),"0x"+word(2),"0x"+word(3)],
        "data":"0x"+word(100)+word(105)+word(liquidator)+word(0),
        "transactionHash":tx,"logIndex":index,"blockNumber":block
    }


class BaseKeeperSourceTests(unittest.TestCase):
    def test_event_decoding(self):
        d=decode_liquidation(ev())
        self.assertEqual(d["liquidator"],"0x"+f"{5:040x}")
        self.assertEqual(d["debt_repaid_raw"],"100")
        self.assertEqual(d["collateral_received_raw"],"105")
        self.assertFalse(d["receive_atoken"])

    def test_bad_topic_rejected(self):
        bad=ev()
        bad["topics"][0]="0x"+("0"*64)
        with self.assertRaises(ValueError):decode_liquidation(bad)

    def test_gas_fee_and_l1_knowledge(self):
        val,yes=cost_wei({"gasUsed":"0xa","effectiveGasPrice":"0x64","l1Fee":"0x1"})
        self.assertEqual(val,1001)
        self.assertTrue(yes)
        val,no=cost_wei({"gasUsed":"0xa","effectiveGasPrice":"0x64"})
        self.assertEqual(val,1000)
        self.assertFalse(no)

    def test_concentration_risk(self):
        rows=[decode_liquidation(ev(tx=f"0x{i}",index="0x0",liquidator=(5 if i<10 else 7))) for i in range(11)]
        d=decide(rows,True,[12345],1)
        self.assertEqual(d["source_verdict"],"SOURCE_PASS")
        self.assertTrue(d["high_concentration_barrier"])
        self.assertIsNone(d["net_profit_usd"])

    def test_empty_is_not_profitable_and_requires_complete(self):
        self.assertEqual(decide([],True,[],0)["source_verdict"],"SOURCE_EMPTY")
        self.assertEqual(decide([],False,[],0)["source_verdict"],"SOURCE_BLOCKED")

    def test_duplicate_event_fails_closed(self):
        rows=[decode_liquidation(ev()), decode_liquidation(ev())]
        with self.assertRaises(GateBlocked):decide(rows,True,[100],0)


if __name__=="__main__":
    unittest.main()
