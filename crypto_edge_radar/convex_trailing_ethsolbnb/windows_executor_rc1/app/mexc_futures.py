"""Narrow MEXC Futures signed transport. No secrets persisted, no wallet endpoints.
Mutation methods are not called unless explicit LIVE authority is present in supervisor.
HTTP is injectable for no-network unit tests. API must be confirmed against account before live.
"""
from __future__ import annotations
import hashlib, hmac, json, os, re, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE='https://api.mexc.com'
SYMS=('ETH_USDT','SOL_USDT','BNB_USDT')
GET_PATHS={'/api/v1/private/account/assets','/api/v1/private/position/open_positions',
           '/api/v1/private/order/list/open_orders','/api/v1/private/stoporder/open_orders',
           '/api/v1/private/position/position_mode','/api/v1/private/account/tiered_fee_rate/v2',
           '/api/v1/private/position/leverage','/api/v1/private/account/risk_limit','/api/v1/private/order/get/'}
POST_PATHS={'/api/v1/private/order/create','/api/v1/private/stoporder/place',
            '/api/v1/private/stoporder/change_plan_price','/api/v1/private/position/change_leverage',
            '/api/v1/private/position/change_auto_add_im'}

class ExchangeError(RuntimeError):pass

class MexcFutures:
    def __init__(self, key=None, secret=None, opener=urlopen, clock=None):
        self.key=key or os.environ.get('MEXC_API_KEY','')
        self.secret=secret or os.environ.get('MEXC_API_SECRET','')
        if not self.key or not self.secret:raise ExchangeError('MEXC_KEYS_NOT_PRESENT_IN_PROCESS')
        self.opener=opener; self.clock=clock or (lambda:int(time.time()*1000))

    def call(self, method, path, payload=None):
        if method not in ('GET','POST'): raise ExchangeError('METHOD_DENIED')
        if method=='GET' and path.startswith('/api/v1/private/order/external/'):
            components=path.split('/')
            if len(components)!=8 or components[6] not in SYMS or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}',components[7]):
                raise ExchangeError('BAD_EXTERNAL_ORDER_LOOKUP')
        elif path not in (GET_PATHS if method=='GET' else POST_PATHS): raise ExchangeError('PATH_DENIED')
        payload=payload or {}
        ts=int(self.clock())
        if method=='GET':
            body=urlencode(sorted((str(k),str(v)) for k,v in payload.items()))
            url=BASE+path+('?' + body if body else '')
            request=Request(url,method='GET')
        else:
            body=json.dumps(payload,separators=(',',':'),ensure_ascii=False)
            request=Request(BASE+path,data=body.encode('utf-8'),method='POST')
        sig=hmac.new(self.secret.encode(), f'{self.key}{ts}{body}'.encode(),hashlib.sha256).hexdigest()
        request.add_header('ApiKey',self.key)
        request.add_header('Request-Time',str(ts))
        request.add_header('Signature',sig)
        request.add_header('Content-Type','application/json')
        request.add_header('User-Agent','CryptoLab-Convex-Radar-v01')
        try:
            with self.opener(request,timeout=10) as response:
                data=json.loads(response.read().decode('utf-8'))
        except Exception as e:
            # An order request can have reached the exchange despite a network failure. NO RETRY.
            raise ExchangeError(f'RESPONSE_UNKNOWN_NO_BLIND_RETRY:{type(e).__name__}') from e
        if not isinstance(data,dict) or data.get('success') is not True:
            raise ExchangeError('MEXC_REJECTED:'+str(data.get('code') if isinstance(data,dict) else 'BAD_JSON'))
        return data.get('data')

    def positions(self):return self.call('GET','/api/v1/private/position/open_positions') or []
    def orders(self):
        data=self.call('GET','/api/v1/private/order/list/open_orders',{'page_num':1,'page_size':100})
        if data is None:return []
        if isinstance(data,dict) and isinstance(data.get('resultList'),list):
            # refuse truncated status: do not trade if pagination uncertain
            if int(data.get('totalPage',1) or 1)>1:raise ExchangeError('ORDERS_PAGINATION_NOT_RECONCILED')
            return data['resultList']
        if isinstance(data,list):return data
        raise ExchangeError('ORDERS_BAD_SHAPE')
    def stops(self):return self.call('GET','/api/v1/private/stoporder/open_orders') or []
    def position_mode(self):return self.call('GET','/api/v1/private/position/position_mode')
    def assets(self):return self.call('GET','/api/v1/private/account/assets') or []
    def fees(self,sym):
        if sym not in SYMS:raise ExchangeError('SYMBOL_DENIED')
        return self.call('GET','/api/v1/private/account/tiered_fee_rate/v2',{'symbol':sym})

    def prepare_long(self,sym,leverage):
        if sym not in SYMS or type(leverage)!=int or not 1<=leverage<=20:raise ExchangeError('LEVERAGE_DENIED')
        return self.call('POST','/api/v1/private/position/change_leverage',
                         {'openType':1,'leverage':leverage,'symbol':sym,'positionType':1})
    def buy_market(self,sym,contracts,leverage,oid):
        if sym not in SYMS or type(contracts)!=int or contracts<1 or not 1<=leverage<=20 or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}',oid):
            raise ExchangeError('ORDER_INVALID')
        result=self.call('POST','/api/v1/private/order/create',
                         {'symbol':sym,'price':0,'vol':contracts,'leverage':leverage,
                          'side':1,'type':5,'openType':1,'externalOid':oid,'positionMode':1})
        if not isinstance(result,dict) or not result.get('orderId'):raise ExchangeError('ACK_UNVERIFIABLE')
        return result
    def install_stop_only(self, position_id, contracts, stop_price):
        if position_id<=0 or contracts<=0 or stop_price<=0:raise ExchangeError('STOP_INVALID')
        data=self.call('POST','/api/v1/private/stoporder/place',{
            'lossTrend':1,'profitTrend':1,'positionId':position_id,'vol':contracts,
            'stopLossPrice':stop_price,'takeProfitPrice':0,'priceProtect':0,
            'profitLossVolType':'SAME','volType':2,'takeProfitReverse':2,'stopLossReverse':2,
            'takeProfitType':0,'takeProfitOrderPrice':0,'stopLossType':0,'stopLossOrderPrice':0})
        return data
    def revise_stop_only(self,stop_plan_id,stop_price):
        if int(stop_plan_id)<=0 or stop_price<=0:raise ExchangeError('STOP_REVISION_INVALID')
        return self.call('POST','/api/v1/private/stoporder/change_plan_price',
                         {'stopPlanOrderId':int(stop_plan_id),'stopLossPrice':stop_price,'takeProfitPrice':0})

    def order_by_external(self,sym,oid):
        if sym not in SYMS or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}',oid):raise ExchangeError('ORDER_LOOKUP_INVALID')
        return self.call('GET',f'/api/v1/private/order/external/{sym}/{oid}')
    def close_owned_long(self,sym,contracts,position_id,oid):
        if sym not in SYMS or not isinstance(contracts,int) or contracts<1 or int(position_id)<=0 or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}',oid):
            raise ExchangeError('CLOSE_INVALID')
        return self.call('POST','/api/v1/private/order/create',
              {'symbol':sym,'price':0,'vol':contracts,'side':4,'type':5,'openType':1,
               'positionId':int(position_id),'externalOid':oid,'positionMode':1})
    def buy_with_initial_stop(self,sym,contracts,leverage,oid,stop_price):
        if sym not in SYMS or not isinstance(contracts,int) or contracts<1 or not isinstance(leverage,int) or not 1<=leverage<=20 or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}',oid) or stop_price<=0:
            raise ExchangeError('ENTRY_PROTECTION_INVALID')
        result=self.call('POST','/api/v1/private/order/create',
            {'symbol':sym,'price':0,'vol':contracts,'leverage':leverage,'side':1,'type':5,
             'openType':1,'externalOid':oid,'positionMode':1,
             'stopLossPrice':stop_price,'lossTrend':1,'priceProtect':0})
        if not isinstance(result,dict) or not result.get('orderId'):raise ExchangeError('ACK_UNVERIFIABLE')
        return result