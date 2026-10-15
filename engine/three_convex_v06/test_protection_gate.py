"""MEXC native stop read-back verifier stress tests. Synthetic only, no POST."""
from copy import deepcopy
import unittest

from engine.three_convex_v06.protection_gate import (
    ProtectHalt,reconcile_native_stop,
)


def example():
    order={"orderId":"739106551624717312","symbol":"SOL_USDT",
           "externalOid":"CLV6.SOL.123","positionId":123456,
           "state":3,"side":1,"openType":1,"leverage":10,
           "positionMode":1,"dealVol":1,"dealAvgPrice":"102.74"}
    pos={"positionId":123456,"symbol":"SOL_USDT","positionType":1,
         "openType":1,"leverage":10,"state":1,"autoAddIm":False,
         "holdVol":1,"holdAvgPrice":"102.74","liquidatePrice":"92.00"}
    stop={"id":998,"positionId":123456,"symbol":"SOL_USDT","positionType":1,
          "state":1,"isFinished":0,"vol":1,
          "stopLossPrice":"98.63","takeProfitPrice":0,"lossTrend":2}
    return dict(order=order,positions=[pos],stops=[stop],
                symbol="SOL_USDT",external_oid="CLV6.SOL.123",
                tick_size="0.01",mark_price="102.75",
                now_ms=10300,order_read_ms=10280,
                position_read_ms=10290,stop_read_ms=10300,
                stop_submit_ack_ms=10100,stop_order_id=998)


class ProtectionTests(unittest.TestCase):
    def test_fully_matching_receipt_is_only_structural(self):
        r=reconcile_native_stop(**example())
        self.assertEqual(r["state"],"STRUCTURALLY_MATCHED_ACTIVE_NATIVE_STOP_AFTER_FILL")
        self.assertEqual(r["trading_authority"],"NONE")
        self.assertFalse(r["authenticated_origin_independently_proven"])
        self.assertLess(float(r["modeled_risk_usdt"]),.5)

    def fail(self, mutation, reason):
        e=example()
        mutation(e)
        with self.assertRaisesRegex(ProtectHalt,reason):
            reconcile_native_stop(**e)

    def test_wrong_symbol(self):
        self.fail(lambda x:x["order"].update(symbol="BNB_USDT"),"IDENTITY")

    def test_wrong_external_identity(self):
        self.fail(lambda x:x.update(external_oid="other"),"IDENTITY")

    def test_partial_fill_not_accepted(self):
        self.fail(lambda x:x["order"].update(dealVol=".5"),"ONE")

    def test_order_pending_not_filled(self):
        self.fail(lambda x:x["order"].update(state=2),"ENTRY_NOT")

    def test_wrong_order_leverage(self):
        self.fail(lambda x:x["order"].update(leverage=5),"ENTRY_NOT")

    def test_wrong_mode(self):
        self.fail(lambda x:x["order"].update(positionMode=2),"ENTRY_NOT")

    def test_cross_margin(self):
        self.fail(lambda x:x["positions"][0].update(openType=2),"POSITION_ISOLATED")

    def test_auto_add_margin_on(self):
        self.fail(lambda x:x["positions"][0].update(autoAddIm=True),"POSITION_ISOLATED")

    def test_missing_position(self):
        self.fail(lambda x:x.update(positions=[]),"FILLED_POSITION_ABSENT")

    def test_position_multiple_holding_units(self):
        self.fail(lambda x:x["positions"][0].update(holdVol=2),"POSITION_SIZE")

    def test_price_mismatch(self):
        self.fail(lambda x:x["positions"][0].update(holdAvgPrice="100"),"AVERAGE_POSITION")

    def test_liquidation_too_high(self):
        self.fail(lambda x:x["positions"][0].update(liquidatePrice="98.5"),"LIQUIDATION")

    def test_missing_broker_stop(self):
        self.fail(lambda x:x.update(stops=[]),"NOT_EXACTLY_ONE")

    def test_duplicate_broker_stop(self):
        self.fail(lambda x:x["stops"].append(deepcopy(x["stops"][0])),"NOT_EXACTLY_ONE")

    def test_broker_stop_does_not_cover_position(self):
        self.fail(lambda x:x["stops"][0].update(vol=".5"),"EXACT_POSITION")

    def test_broker_stop_not_yet_active(self):
        self.fail(lambda x:x["stops"][0].update(state=2),"STOP_NOT_ACTIVE")

    def test_broker_stop_finished(self):
        self.fail(lambda x:x["stops"][0].update(isFinished=1),"STOP_NOT_ACTIVE")

    def test_broker_stop_price_wrong(self):
        self.fail(lambda x:x["stops"][0].update(stopLossPrice="97.00"),"NOT_EXACT")

    def test_stop_not_read_after_ack(self):
        self.fail(lambda x:x.update(stop_read_ms=10050),"STOP_NOT_READ")

    def test_stop_data_stale(self):
        self.fail(lambda x:x.update(now_ms=40000),"STALE_ORDER_READ")

    def test_post_ack_id_not_same_as_stop_read_id(self):
        self.fail(lambda x:x.update(stop_order_id=999),"ID_MISMATCH")

    def test_stop_mark_trigger_different(self):
        self.fail(lambda x:x["stops"][0].update(lossTrend=1),"FAIR_MARK")

    def test_mark_already_below_stop(self):
        self.fail(lambda x:x.update(mark_price="90"),"MARK_ALREADY")

    def test_extra_take_profit_changes_strategy(self):
        self.fail(lambda x:x["stops"][0].update(takeProfitPrice="125"),"EXTRANEOUS")

    def test_unexpected_other_position_blocks_isolation(self):
        def change(x):
            p=deepcopy(x["positions"][0])
            p["symbol"]="BNB_USDT"
            p["positionId"]=789
            x["positions"].append(p)
        self.fail(change,"EXTRA_ACCOUNT")

    def test_bad_risk_cap_halts(self):
        self.fail(lambda x:x.update(max_cash_risk="0.10"),"CASH_RISK")

    def test_nonfinite_price_halts(self):
        self.fail(lambda x:x["stops"][0].update(stopLossPrice="NaN"),"BAD_BROKER_STOP")


if __name__=="__main__":
    unittest.main()
