import unittest,json,tempfile,sys,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import engine,market,mexc_futures
from convex_core import initial_position,evaluate_closed_bar,size_for_risk

class MockResponse:
    status=200
    def __init__(self,obj):self.obj=obj
    def read(self):return json.dumps(self.obj).encode()
    def __enter__(self):return self
    def __exit__(self,*a):pass

class FakeBroker:
    def __init__(self):
        self.ps=[];self.ss=[];self.oo=[];self.assets_data=[{'currency':'USDT','equity':500,'availableBalance':490}]
        self.calls=[];self.order=None
    def positions(self):return [dict(x) for x in self.ps]
    def stops(self):return [dict(x) for x in self.ss]
    def orders(self):return [dict(x) for x in self.oo]
    def assets(self):return [dict(x) for x in self.assets_data]
    def position_mode(self):return 1
    def fees(self,sym):return {'takerFeeRate':'.0005'}
    def prepare_long(self,sym,lev):self.calls.append(('leverage',sym,lev))
    def buy_with_initial_stop(self,sym,contracts,lev,oid,stop):
        self.calls.append(('buy',sym,contracts,oid,stop))
        self.order={'symbol':sym,'externalOid':oid,'side':1,'state':3,'dealVol':contracts,'dealAvgPrice':100,
                    'positionId':123,'orderId':'4321'}
        self.ps=[{'symbol':sym,'positionId':123,'positionType':1,'holdVol':contracts}]
        self.ss=[{'symbol':sym,'positionId':123,'id':99,'vol':contracts,'stopLossPrice':stop,'takeProfitPrice':0,'isFinished':0}]
        return {'orderId':'4321'}
    def order_by_external(self,sym,oid):
        self.calls.append(('order_read',sym,oid));return dict(self.order)
    def install_stop_only(self,pid,contracts,stop):
        self.calls.append(('install_stop',pid,contracts,stop))
        self.ss=[{'symbol':'ETH_USDT','positionId':pid,'id':99,'vol':contracts,'stopLossPrice':stop,'takeProfitPrice':0}]
    def revise_stop_only(self,id,price):
        self.calls.append(('revise',id,price));self.ss[0]['stopLossPrice']=price
    def close_owned_long(self,*a):self.calls.append(('EMERGENCY',*a));return {'orderId':'9988'}

class CoreTests(unittest.TestCase):
    def test_initial_stop_and_reset_nonlatched(self):
        p=initial_position('ETH_USDT',123,100,2,3600000,'s1')
        high=evaluate_closed_bar(p,boundary=7200000,open_price=101,high=110,low=99,close=106)
        self.assertEqual(high['action'],'CHANGE_STOP')
        self.assertAlmostEqual(high['position'].active_stop,96.8)
        lo=evaluate_closed_bar(high['position'],boundary=10800000,open_price=106,high=108,low=101,close=102)
        self.assertAlmostEqual(lo['position'].active_stop,96)
    def test_size_small_account_block(self):
        r=size_for_risk(equity_usdt=112,market_ask=2517,contract_size=.01,min_vol=1,
           vol_unit=1,max_vol=1000,leverage=20)
        self.assertEqual(r['status'],'BLOCKED_LOT_RISK_MISMATCH')
    def test_size_big_account(self):
        r=size_for_risk(equity_usdt=3000,market_ask=100,contract_size=.01,min_vol=1,
            vol_unit=1,max_vol=1000,leverage=20)
        self.assertEqual(r['status'],'SIZED')
        self.assertLessEqual(r['estimated_loss_budget_usdt'],r['account_risk_budget_usdt']+1e-8)
    def test_missing_stop_makes_failure(self):
        with self.assertRaises(engine.EngineBlocked):engine.validated_stop({'stops':[]},123,1)
    def test_wrong_volume_makes_failure(self):
        with self.assertRaises(engine.EngineBlocked):engine.validated_stop({'stops':[{'id':10,'positionId':123,'vol':1,'stopLossPrice':90}]},123,2)
    def test_config_is_identity_locked(self):self.assertEqual(engine.config()['leverage'],20)
    def test_no_rsi_signal_flat(self):
        self.assertFalse(market.signal_parent_v5([{'close':100,'vol':1} for _ in range(400)])['signal'])
    def test_oid_deterministic(self):self.assertEqual(engine.oid('ETH_USDT',100,'entry'),engine.oid('ETH_USDT',100,'entry'))
    def test_stop_price_floor(self):self.assertEqual(market.floor_price(97.999,.01),97.99)
    def test_public_old_domain_removed(self):self.assertEqual(market.BASE,'https://api.mexc.com')

class TransportTests(unittest.TestCase):
    def test_place_market_long_with_protection(self):
        box={}
        def opener(request,timeout):
            box['url']=request.full_url;box['body']=json.loads(request.data)
            return MockResponse({'success':True,'code':0,'data':{'orderId':'54321'}})
        c=mexc_futures.MexcFutures(key='k',secret='s',opener=opener,clock=lambda:1234)
        c.buy_with_initial_stop('SOL_USDT',2,20,'cv1-id',96)
        self.assertEqual(box['body']['side'],1);self.assertEqual(box['body']['stopLossPrice'],96)
        self.assertEqual(box['body']['positionMode'],1);self.assertEqual(box['body']['leverage'],20)
    def test_stop_revision_has_no_tp(self):
        box={}
        def opener(req,timeout):box.update(json.loads(req.data));return MockResponse({'success':True,'code':0})
        c=mexc_futures.MexcFutures(key='k',secret='s',opener=opener)
        c.revise_stop_only('42',92)
        self.assertEqual(box['stopPlanOrderId'],42);self.assertEqual(box['takeProfitPrice'],0)
    def test_unknown_mutation_no_retry(self):
        seen=[]
        def opener(req,timeout):seen.append(req);raise TimeoutError('connection lost')
        c=mexc_futures.MexcFutures(key='k',secret='s',opener=opener)
        with self.assertRaisesRegex(mexc_futures.ExchangeError,'NO_BLIND_RETRY'):c.buy_with_initial_stop('BNB_USDT',1,5,'oid',90)
        self.assertEqual(len(seen),1)
    def test_account_external_id_path(self):
        seen=[]
        def opener(req,timeout):seen.append(req.full_url);return MockResponse({'success':True,'code':0,'data':{'externalOid':'abc'}})
        c=mexc_futures.MexcFutures(key='k',secret='s',opener=opener)
        self.assertEqual(c.order_by_external('ETH_USDT','abc')['externalOid'],'abc')
        self.assertTrue(seen[0].endswith('/ETH_USDT/abc'))
    def test_denies_arbitrary_paths(self):
        c=mexc_futures.MexcFutures(key='k',secret='s')
        with self.assertRaises(mexc_futures.ExchangeError):c.call('POST','/api/v1/private/account/transfer',{})

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.patcher=patch.multiple(engine,STATE=root,LEDGER=root/'ledger.json',AUTH=root/'authority.json',KILL=root/'kill',LOG=root/'log.jsonl')
        self.patcher.start();self.addCleanup(self.patcher.stop)
    def test_recover_stop_already_attached(self):
        b=FakeBroker();b.buy_with_initial_stop('ETH_USDT',2,20,'oid1',96)
        s=engine.ledger();s['entries']['ETH_USDT']={'oid':'oid1','contracts':2,'boundary':3600000,'price_unit':.01,
                            'contract_size':.01,'stop_place_attempted':False,'initial_adjust_attempted':False}
        engine.save(s);engine.entry_recovery(s,'ETH_USDT',b)
        self.assertIn('ETH_USDT',s['positions'])
        self.assertEqual(s['positions']['ETH_USDT']['stop'],96)
        self.assertEqual(s['entries']['ETH_USDT']['phase'],'POSITION_OWNED_PROTECTED')
        self.assertFalse(any(t[0]=='install_stop' for t in b.calls))
    def test_recovery_installs_missing_stop(self):
        b=FakeBroker();b.buy_with_initial_stop('ETH_USDT',2,20,'oid2',96);b.ss=[]
        s=engine.ledger();s['entries']['ETH_USDT']={'oid':'oid2','contracts':2,'boundary':3600000,'price_unit':.01,
                            'contract_size':.01,'stop_place_attempted':False,'initial_adjust_attempted':False}
        engine.save(s);engine.entry_recovery(s,'ETH_USDT',b)
        self.assertTrue(any(t[0]=='install_stop' for t in b.calls))
    def test_emergency_one_shot(self):
        b=FakeBroker();b.buy_with_initial_stop('ETH_USDT',2,20,'oid2',96);b.ss=[]
        s=engine.ledger();s['positions']['ETH_USDT']={'position_id':123,'last_boundary':3600000,'contracts':2}
        with self.assertRaisesRegex(engine.EngineBlocked,'EMERGENCY_CLOSE_SENT'):
            engine.emergency_flatten_unprotected(s,b,engine.account_snapshot(b))
        self.assertEqual(sum(t[0]=='EMERGENCY' for t in b.calls),1)
        with self.assertRaisesRegex(engine.EngineBlocked,'ALREADY_ATTEMPTED'):
            engine.emergency_flatten_unprotected(s,b,engine.account_snapshot(b))
        self.assertEqual(sum(t[0]=='EMERGENCY' for t in b.calls),1)
    def test_nonowned_position_blocks(self):
        b=FakeBroker();b.ps=[{'symbol':'BTC_USDT','positionId':999,'holdVol':1}]
        with self.assertRaisesRegex(engine.EngineBlocked,'FOREIGN_POSITIONS'):
            engine.assert_clean_account(engine.ledger(),engine.account_snapshot(b))
    def test_unsafe_retroactive_trailing_block(self):
        b=FakeBroker();b.buy_with_initial_stop('ETH_USDT',2,20,'oid1',96)
        s=engine.ledger();s['positions']['ETH_USDT']={'position_id':123,'entry':100,'peak':100,'stop':96,
            'contracts':2,'contract_size':.01,'last_boundary':3600000,'pending_stop':None}
        bars=[{'boundary_ms':7200000,'open':100,'high':101,'low':99,'close':100},
              {'boundary_ms':10800000,'open':101,'high':105,'low':99,'close':102}]
        with self.assertRaisesRegex(engine.EngineBlocked,'MISSED_HOURLY'):
            engine.update_closed_position(s,'ETH_USDT',bars,b,engine.account_snapshot(b),{'priceUnit':.01},True)
    def test_trailing_update_readback(self):
        b=FakeBroker();b.buy_with_initial_stop('ETH_USDT',2,20,'oid1',96)
        s=engine.ledger();s['positions']['ETH_USDT']={'position_id':123,'entry':100,'peak':100,'stop':96,
            'contracts':2,'contract_size':.01,'last_boundary':3600000,'pending_stop':None}
        bars=[{'boundary_ms':7200000,'open':100,'high':120,'low':99,'close':106}]
        engine.update_closed_position(s,'ETH_USDT',bars,b,engine.account_snapshot(b),{'priceUnit':.01},True)
        self.assertAlmostEqual(s['positions']['ETH_USDT']['stop'],105.6)
        self.assertEqual(s['positions']['ETH_USDT']['pending_stop'],None)
        self.assertTrue(any(t[0]=='revise' for t in b.calls))

class EndToEndSimulation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.patcher=patch.multiple(engine,STATE=root,LEDGER=root/'ledger.json',AUTH=root/'authority.json',KILL=root/'kill',LOG=root/'log.jsonl')
        self.patcher.start();self.addCleanup(self.patcher.stop)
        self.boundary=1800000000000
        self.now=self.boundary+30000
        self.candles=[{'open_ms':i,'boundary_ms':self.boundary,'open':100,'high':101,'low':99,'close':100,'vol':1} for i in range(400)]
    def _patch_source(self):
        from unittest.mock import patch
        source=patch.multiple(market,
           bars=lambda sym:self.candles,
           book=lambda sym:{'ask':100,'bid':99.9,'age_ms':100,'as_of_ms':self.now},
           signal_parent_v5=lambda hist:{'signal':True,'score':3})
        return source
    def test_synthetic_entire_entry_order_stop_journal(self):
        b=FakeBroker()
        a={'status':'ARMED','candidate_id':engine.config()['candidate_id'],
           'config_sha256':__import__('hashlib').sha256(engine.CONFIG.read_bytes()).hexdigest()}
        engine.atomic(engine.AUTH,a)
        with self._patch_source(), patch.object(market,'spec',lambda sym:{'symbol':sym,'contractSize':.1,'minVol':1,'volUnit':1,'maxVol':10000,'priceUnit':.01}), patch.object(engine.time,'time_ns',return_value=self.now*1000000):
            # Accept one of three symbols; fake broker does not support multi-position execution.
            b.assets_data=[{'currency':'USDT','equity':500,'availableBalance':490}]
            initial=engine.tick(b,now=self.now)
        self.assertTrue(any(x[0]=='buy' for x in b.calls))
        self.assertEqual(initial['mode'],'LIVE_ARMED')
        self.assertIn('ETH_USDT',engine.ledger()['positions'])
        self.assertEqual(engine.ledger()['positions']['ETH_USDT']['stop'],96)
    def test_disarmed_observes_signal_but_cannot_order(self):
        with self._patch_source(),patch.object(engine.time,'time_ns',return_value=self.now*1000000):
            out=engine.tick(now=self.now)
        self.assertEqual(out['mode'],'OBSERVE_ONLY')
        self.assertEqual(len(engine.ledger()['signals']),3)
        self.assertEqual(len(engine.ledger()['entries']),0)

if __name__=='__main__':unittest.main()