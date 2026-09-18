from __future__ import annotations

import json
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

BASE="https://fapi.binance.com"
ALLOWED={"/fapi/v1/time","/fapi/v1/klines","/fapi/v1/fundingRate"}
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")


class BinanceUSDMPublicError(RuntimeError):
    pass


class BinanceUSDMPublicFeed:
    provider="BINANCE_USDM_PUBLIC_REST"
    base_url=BASE

    def __init__(self,timeout:int=15)->None:
        self.timeout=timeout

    def _get_json(self,path:str,query:dict|None=None):
        if path not in ALLOWED:
            raise BinanceUSDMPublicError(f"blocked non-allowlisted path:{path}")
        qs=f"?{urlencode(query)}" if query else ""
        url=f"{self.base_url}{path}{qs}"
        p=urlparse(url)
        if p.scheme!="https" or p.netloc!="fapi.binance.com":
            raise BinanceUSDMPublicError("blocked host/scheme")
        req=Request(url,method="GET",headers={"User-Agent":"crypto-edge-radar/0.9 dh03-12h-public"})
        try:
            with urlopen(req,timeout=self.timeout) as r:
                body=r.read()
                if r.status!=200:
                    raise BinanceUSDMPublicError(f"HTTP {r.status}")
                return json.loads(body.decode("utf-8"))
        except Exception as exc:
            if isinstance(exc,BinanceUSDMPublicError):
                raise
            raise BinanceUSDMPublicError(f"public source unavailable:{type(exc).__name__}:{exc}") from exc

    def server_time_ms(self)->int:
        p=self._get_json("/fapi/v1/time")
        if not isinstance(p,dict) or "serverTime" not in p:
            raise BinanceUSDMPublicError("time payload invalid")
        return int(p["serverTime"])

    def klines(self,symbol:str,interval:str="15m",limit:int=5):
        symbol=symbol.upper()
        if symbol not in SYMBOLS:
            raise BinanceUSDMPublicError("symbol outside frozen universe")
        if interval not in {"1m","15m"}:
            raise BinanceUSDMPublicError("interval not allowlisted")
        if not 1<=int(limit)<=1500:
            raise BinanceUSDMPublicError("invalid limit")
        p=self._get_json("/fapi/v1/klines",{"symbol":symbol,"interval":interval,"limit":int(limit)})
        if not isinstance(p,list):
            raise BinanceUSDMPublicError("klines payload invalid")
        return p

    def funding(self,symbol:str,limit:int=5):
        symbol=symbol.upper()
        if symbol not in SYMBOLS:
            raise BinanceUSDMPublicError("symbol outside frozen universe")
        p=self._get_json("/fapi/v1/fundingRate",{"symbol":symbol,"limit":int(limit)})
        if not isinstance(p,list):
            raise BinanceUSDMPublicError("funding payload invalid")
        return p


def public_source_probe(feed:BinanceUSDMPublicFeed|None=None)->dict:
    feed=feed or BinanceUSDMPublicFeed()
    server=feed.server_time_ms()
    rows={}
    for symbol in SYMBOLS:
        k=feed.klines(symbol,"15m",5)
        f=feed.funding(symbol,5)
        if len(k)<2:
            raise BinanceUSDMPublicError(f"insufficient klines:{symbol}")
        if not f:
            raise BinanceUSDMPublicError(f"no funding rows:{symbol}")
        rows[symbol]={
            "kline_rows":len(k),
            "last_kline_open_ms":int(k[-1][0]),
            "funding_rows":len(f),
            "last_funding_time_ms":int(f[-1]["fundingTime"]),
        }
    return {
        "status":"PASS_PUBLIC_SOURCE",
        "provider":feed.provider,
        "server_time_ms":server,
        "symbols":rows,
        "authenticated_api_used":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
        "used_as_forward_evidence":False,
    }
