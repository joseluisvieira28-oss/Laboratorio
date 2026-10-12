import io, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from convex_core import *
from mexc_futures import MexcFutures, ExchangeError
import supervisor

class FakeResponse:
    status=200
    def __init__(self,p):self.p=p
    def __enter__(self):return self
    def __exit__(self,*a):return None
    def read(self):return json.dumps(self.p).encode()

def fake_opener(request, timeout):
    return FakeResponse({'success':True,'data':{'orderId':'1234'}})

class BridgeTest(unittest.TestCase):
    def test_original_no_tp(self):
        self.assertEqual(TRAIL_ACTIVATION,.05)
        self.assertEqual(TRAIL_DISTANCE,.12)
        self.assertEqual(STOP_FRAC,.04)
    def test_entry_stop(self):
        p=initial_position('SOL_USDT',1,100,2,10,'15')
        self.assertAlmostEqual(p.active_stop,96)
    def test_trail_closed_bar_no_intrabar_lookahead(self):
        p=initial_position('SOL_USDT',1,100,2,10,'15')
        x=evaluate_closed_bar(p,boundary=20,open_price=100,high=130,low=98,close=110)
        self.assertEqual(x['action'],'CHANGE_STOP')
        self.assertAlmostEqual(x['next_stop'],114.4)
    def test_reverts_to_initial_stop(self):
        p=initial_position('SOL_USDT',1,100,2,10,'15')
        p=evaluate_closed_bar(p,boundary=20,open_price=100,high=112,low=98,close=110)['position']
        x=evaluate_closed_bar(p,boundary=30,open_price=110,high=111,low=103,close=104)
        self.assertAlmostEqual(x['next_stop'],96)
    def test_old_stop_has_priority(self):
        p=initial_position('SOL_USDT',1,100,2,10,'15')
        p=evaluate_closed_bar(p,boundary=20,open_price=100,high=120,low=98,close=110)['position']
        x=evaluate_closed_bar(p,boundary=30,open_price=110,high=115,low=104,close=112)
        self.assertEqual(x['action'],'EXCHANGE_STOP_RECONCILIATION_REQUIRED')
    def test_duplicate_bar(self):
        p=initial_position('SOL_USDT',1,100,2,10,'15')
        self.assertEqual(evaluate_closed_bar(p,boundary=10,open_price=100,high=110,low=90,close=100)['action'],'DUPLICATE_OR_OLD_BAR')
    def test_risk_blocks_subminimum(self):
        x=size_for_risk(equity_usdt=112,market_ask=2517,contract_size=.01,min_vol=1,vol_unit=1,max_vol=1000)
        self.assertEqual(x['status'],'BLOCKED_LOT_RISK_MISMATCH')
    def test_20x_does_not_bypass_stop_risk(self):
        a=size_for_risk(equity_usdt=112,market_ask=2517,contract_size=.01,min_vol=1,vol_unit=1,max_vol=1000,leverage=1)
        b=size_for_risk(equity_usdt=112,market_ask=2517,contract_size=.01,min_vol=1,vol_unit=1,max_vol=1000,leverage=20)
        self.assertEqual(a['contracts'],b['contracts'])
    def test_refuse_21x(self):
        with self.assertRaises(ValueError):size_for_risk(equity_usdt=1000,market_ask=100,contract_size=.01,min_vol=1,vol_unit=1,max_vol=100,leverage=21)
    def test_order_transport_only_allowlist(self):
        x=MexcFutures(key='a',secret='b',opener=fake_opener,clock=lambda:123)
        with self.assertRaises(ExchangeError): x.call('POST','/api/v1/private/account/transfer',{})
    def test_only_three_symbols(self):
        x=MexcFutures(key='a',secret='b',opener=fake_opener,clock=lambda:123)
        with self.assertRaises(ExchangeError):x.buy_market('BTC_USDT',1,20,'oid-1')
    def test_stopped_live_authority(self):
        self.assertFalse(supervisor.verified_order_authority())
    def test_api_request_market_order_shape(self):
        requests=[]
        def capture(req,timeout):
            requests.append(req)
            return FakeResponse({'success':True,'data':{'orderId':'1234'}})
        x=MexcFutures(key='a',secret='b',opener=capture,clock=lambda:123)
        x.buy_market('BNB_USDT',1,20,'oid-1')
        self.assertEqual(requests[0].method,'POST')
        payload=json.loads(requests[0].data)
        self.assertEqual(payload['side'],1)
        self.assertEqual(payload['leverage'],20)
        self.assertEqual(payload['openType'],1)
    def test_stop_only_without_tp(self):
        requests=[]
        def capture(req,timeout):
            requests.append(req)
            return FakeResponse({'success':True,'data':{'id':'3'}})
        x=MexcFutures(key='a',secret='b',opener=capture,clock=lambda:123)
        x.install_stop_only(100,2,96)
        p=json.loads(requests[0].data)
        self.assertEqual(p['stopLossPrice'],96)
        self.assertEqual(p['takeProfitPrice'],0)
    def test_stop_update_order_id(self):
        requests=[]
        def capture(req,timeout):
            requests.append(req)
            return FakeResponse({'success':True,'data':None})
        x=MexcFutures(key='a',secret='b',opener=capture,clock=lambda:123)
        x.revise_stop_only('33',101.2)
        self.assertTrue(requests[0].full_url.endswith('change_plan_price'))
        self.assertEqual(json.loads(requests[0].data)['stopPlanOrderId'],33)
    def test_no_blind_retry_timeout(self):
        def error(req,timeout):raise TimeoutError('unknown')
        x=MexcFutures(key='a',secret='b',opener=error,clock=lambda:123)
        with self.assertRaisesRegex(ExchangeError,'NO_BLIND_RETRY'):
            x.buy_market('SOL_USDT',1,20,'oid-1')
    def test_foreign_position_blocks(self):
        with self.assertRaisesRegex(RuntimeError,'FOREIGN_OPEN_POSITION'):
            supervisor.safety_gate({'positions':[{'positionId':44}],'orders':[],'stops':[]},
                                   {'positions':{}})

if __name__=='__main__': unittest.main()