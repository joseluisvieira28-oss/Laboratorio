from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from typing import Any, Callable
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .mexc_auth_readonly import MEXCCredentials

BASE_URL="https://api.mexc.com"
CLIENT_ID_RE=re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")
_ALLOWED={
    ("GET","/api/v3/account"),
    ("GET","/api/v3/openOrders"),
    ("GET","/api/v3/order"),
    ("GET","/api/v3/myTrades"),
    ("POST","/api/v3/order/test"),
    ("POST","/api/v3/order"),
    ("DELETE","/api/v3/order"),
}

class MEXCSpotAuthError(RuntimeError):
    pass

def _signed_query(secret:str,params:dict[str,Any])->str:
    clean={k:v for k,v in params.items() if v is not None}
    query=urlencode([(str(k),str(v)) for k,v in clean.items()])
    sig=hmac.new(secret.encode(),query.encode(),hashlib.sha256).hexdigest()
    return query+"&signature="+sig

class MEXCSpotAuthenticatedClient:
    base_url=BASE_URL
    def __init__(self,credentials:MEXCCredentials,*,timeout:int=10,clock_ms:Callable[[],int]|None=None,opener:Callable[...,Any]=urlopen):
        self._credentials=credentials
        self.timeout=timeout
        self._clock_ms=clock_ms or (lambda:int(time.time_ns()/1_000_000))
        self._opener=opener

    def _request(self,method:str,path:str,params:dict[str,Any]|None=None)->Any:
        method=method.upper()
        parsed=urlparse(path)
        if parsed.scheme or parsed.netloc or (method,parsed.path) not in _ALLOWED:
            raise MEXCSpotAuthError(f"blocked Spot API route: {method} {path}")
        p=dict(params or {})
        p.setdefault("recvWindow",5000)
        p["timestamp"]=int(self._clock_ms())
        query=_signed_query(self._credentials.api_secret,p)
        url=f"{self.base_url}{parsed.path}?{query}"
        final=urlparse(url)
        if final.scheme!="https" or final.netloc!=urlparse(self.base_url).netloc:
            raise MEXCSpotAuthError("blocked Spot host or scheme")
        req=Request(url,method=method,headers={"X-MEXC-APIKEY":self._credentials.api_key,"Content-Type":"application/json","User-Agent":"crypto-lab-tier2-spot/0.3"})
        try:
            with self._opener(req,timeout=self.timeout) as response:
                status=int(getattr(response,"status",200))
                body=response.read().decode("utf-8")
        except Exception as exc:
            raise MEXCSpotAuthError(f"Spot authenticated transport failed: {type(exc).__name__}: {exc}") from exc
        if status!=200:
            raise MEXCSpotAuthError(f"Spot authenticated HTTP {status}")
        try:
            payload=json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise MEXCSpotAuthError("Spot authenticated response invalid JSON") from exc
        if isinstance(payload,dict) and payload.get("code") not in (None,0,200):
            raise MEXCSpotAuthError(f"MEXC Spot error code={payload.get('code')}: {payload.get('msg') or payload.get('message')}")
        return payload

    @staticmethod
    def _symbol(symbol:str)->str:
        value=symbol.upper()
        if value!="BTCUSDT":
            raise MEXCSpotAuthError("V0.3 Spot lane allowlists BTCUSDT only")
        return value

    def account(self)->dict[str,Any]:
        out=self._request("GET","/api/v3/account")
        if not isinstance(out,dict):
            raise MEXCSpotAuthError("account payload invalid")
        return out

    def open_orders(self,symbol:str="BTCUSDT")->list[dict[str,Any]]:
        out=self._request("GET","/api/v3/openOrders",{"symbol":self._symbol(symbol)})
        if not isinstance(out,list):
            raise MEXCSpotAuthError("openOrders payload invalid")
        return out

    def order(self,*,symbol:str="BTCUSDT",client_order_id:str)->dict[str,Any]:
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        out=self._request("GET","/api/v3/order",{"symbol":self._symbol(symbol),"origClientOrderId":client_order_id})
        if not isinstance(out,dict):
            raise MEXCSpotAuthError("order payload invalid")
        return out

    def my_trades(self,*,symbol:str="BTCUSDT",order_id:str|None=None)->list[dict[str,Any]]:
        params={"symbol":self._symbol(symbol)}
        if order_id is not None:
            params["orderId"]=order_id
        out=self._request("GET","/api/v3/myTrades",params)
        if not isinstance(out,list):
            raise MEXCSpotAuthError("myTrades payload invalid")
        return out

    def test_market_buy(self,*,quote_order_qty_usdt:float,client_order_id:str)->dict[str,Any]:
        return self._market_buy(path="/api/v3/order/test",quote_order_qty_usdt=quote_order_qty_usdt,client_order_id=client_order_id)

    def submit_market_buy(self,*,quote_order_qty_usdt:float,client_order_id:str)->dict[str,Any]:
        return self._market_buy(path="/api/v3/order",quote_order_qty_usdt=quote_order_qty_usdt,client_order_id=client_order_id)

    def _market_buy(self,*,path:str,quote_order_qty_usdt:float,client_order_id:str)->dict[str,Any]:
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        q=float(quote_order_qty_usdt)
        if not (0<q<=10.0):
            raise MEXCSpotAuthError("Spot BUY quoteOrderQty must be >0 and <=10 USDT")
        out=self._request("POST",path,{"symbol":"BTCUSDT","side":"BUY","type":"MARKET","quoteOrderQty":f"{q:.8f}","newClientOrderId":client_order_id})
        if not isinstance(out,dict):
            raise MEXCSpotAuthError("Spot BUY response invalid")
        return out

    def submit_market_sell(self,*,quantity_btc:float,client_order_id:str)->dict[str,Any]:
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        q=float(quantity_btc)
        if q<=0:
            raise MEXCSpotAuthError("Spot SELL quantity must be positive")
        out=self._request("POST","/api/v3/order",{"symbol":"BTCUSDT","side":"SELL","type":"MARKET","quantity":format(q,".12f").rstrip("0").rstrip("."),"newClientOrderId":client_order_id})
        if not isinstance(out,dict):
            raise MEXCSpotAuthError("Spot SELL response invalid")
        return out

    def cancel_order(self,*,client_order_id:str)->dict[str,Any]:
        if not CLIENT_ID_RE.fullmatch(client_order_id):
            raise MEXCSpotAuthError("invalid client order id")
        out=self._request("DELETE","/api/v3/order",{"symbol":"BTCUSDT","origClientOrderId":client_order_id})
        if not isinstance(out,dict):
            raise MEXCSpotAuthError("Spot cancel response invalid")
        return out

__all__=["MEXCSpotAuthError","MEXCSpotAuthenticatedClient","_signed_query"]
