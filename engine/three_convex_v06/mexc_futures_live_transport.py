"""MEXC Futures V06 REAL AUTHENTICATED HTTP GET/POST transport (not armed).

This module DOES contain REAL MEXC private order POST endpoints. Do not
interpret its presence, mock tests, or API ACK as permission to trade.
Production risk controller, stop read-back and account reconciliation must
issue a single-use, endpoint-bound mutation ticket before any POST can run.
No credentials may be written to disk or transmitted to a non-MEXC host.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re
import time
from typing import Any, Callable
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

BASE = "https://api.mexc.com"
SYMBOLS = frozenset(("SOL_USDT", "BNB_USDT"))
GET_PATHS = {
    "/api/v1/private/account/assets",
    "/api/v1/private/position/open_positions",
    "/api/v1/private/position/position_mode",
    "/api/v1/private/position/leverage",
    "/api/v1/private/account/tiered_fee_rate/v2",
    "/api/v1/private/order/list/open_orders",
    "/api/v1/private/stoporder/open_orders",
    "/api/v1/private/order/open_order_total_count",
}
POST_PATHS = frozenset((
    "/api/v1/private/order/create",
    "/api/v1/private/stoporder/place",
    "/api/v1/private/position/change_leverage",
    "/api/v1/private/position/change_auto_add_im",
))
SYMBOL_RE = re.compile(r"^(SOL|BNB)_USDT$")


class MEXCTransportHalt(ValueError):
    pass


@dataclass(frozen=True)
class PrivateKey:
    api_key: str
    api_secret: str

    def __post_init__(self):
        if not self.api_key or not self.api_secret:
            raise MEXCTransportHalt("MISSING_MEXC_CREDENTIALS")


@dataclass
class OneUseMutationTicket:
    """Created ONLY by a future independently reviewed real risk controller.

    Standalone transport never generates tickets and does not provide a
    command-line 'arm' switch. A ticket authorizes one request only.
    """
    endpoint: str
    symbol: str
    issued_ms: int
    risk_controller_digest: str
    consumed: bool = False


def _json_body(payload):
    return json.dumps(payload,ensure_ascii=False,separators=(",",":"))


def signature(key,secret,timestamp,payload):
    return hmac.new(secret.encode(),(key+str(timestamp)+payload).encode(),
                    hashlib.sha256).hexdigest()


class FuturesV06Transport:
    def __init__(self, credentials:PrivateKey, *,
                 opener:Callable[...,Any]=urlopen,
                 clock_ms:Callable[[],int]|None=None, timeout=9):
        self.credentials=credentials
        self.opener=opener
        self.clock_ms=clock_ms or (lambda:time.time_ns()//1_000_000)
        self.timeout=timeout

    def _exchange(self,method,path,params=None,*,ticket=None):
        if not path.startswith("/api/") or "?" in path or "#" in path:
            raise MEXCTransportHalt("INVALID_PATH")
        if method=="GET":
            if path not in GET_PATHS:
                raise MEXCTransportHalt("GET_ENDPOINT_NOT_ALLOWLISTED")
            if ticket is not None:
                raise MEXCTransportHalt("GET_MUST_NOT_REQUIRE_MUTATION_TICKET")
            payload=urlencode(sorted((str(k),str(v)) for k,v in (params or {}).items()),
                              quote_via=quote,safe="")
            url=BASE+path+("?" + payload if payload else "")
            data=None
        elif method=="POST":
            if path not in POST_PATHS:
                raise MEXCTransportHalt("POST_ENDPOINT_NOT_ALLOWLISTED")
            if not isinstance(ticket,OneUseMutationTicket):
                raise MEXCTransportHalt("REAL_MUTATION_REQUIRES_INDEPENDENT_AUTHORITY")
            now=int(self.clock_ms())
            if (ticket.consumed or ticket.endpoint!=path or
                ticket.symbol not in SYMBOLS or ticket.issued_ms>now or
                now-ticket.issued_ms>5000 or
                not re.fullmatch(r"[0-9a-f]{64}",ticket.risk_controller_digest or "")):
                raise MEXCTransportHalt("STALE_OR_INVALID_ONE_USE_MUTATION_TICKET")
            if path in ("/api/v1/private/order/create",
                        "/api/v1/private/position/change_leverage"):
                if not isinstance(params,dict) or params.get("symbol")!=ticket.symbol:
                    raise MEXCTransportHalt("SYMBOL_TICKET_MISMATCH")
            if path=="/api/v1/private/stoporder/place":
                if not isinstance(params,dict) or not isinstance(params.get("positionId"),int) or params["positionId"]<=0:
                    raise MEXCTransportHalt("STOP_REQUIRES_KNOWN_POSITION_ID")
            payload=_json_body(params or {})
            data=payload.encode("utf8")
            url=BASE+path
            # Burn before network request. Unknown HTTP outcome must NEVER
            # retry without independently reconciling broker state.
            ticket.consumed=True
        else:
            raise MEXCTransportHalt("METHOD_BLOCKED")
        parsed=urlparse(url)
        if parsed.scheme!="https" or parsed.netloc!="api.mexc.com":
            raise MEXCTransportHalt("INVALID_API_HOST")
        ts=int(self.clock_ms())
        sig=signature(self.credentials.api_key,
                      self.credentials.api_secret,ts,payload)
        req=Request(url,data=data,method=method,headers={
            "ApiKey":self.credentials.api_key,
            "Request-Time":str(ts),
            "Signature":sig,
            "Content-Type":"application/json",
            "User-Agent":"CryptoLab-MEXC-Futures-V06/0.1",
        })
        try:
            with self.opener(req,timeout=self.timeout) as res:
                if getattr(res,"status",200)!=200:
                    raise MEXCTransportHalt("MEXC_HTTP_NON200_UNKNOWN_ORDER_STATE")
                raw=res.read(2_000_000)
        except Exception as exc:
            # Intentionally avoid logging raw endpoint exceptions and URLs
            # because they may contain account identifiers.
            raise MEXCTransportHalt("MEXC_REQUEST_OUTCOME_UNVERIFIED_"+
                                    type(exc).__name__) from None
        try:
            obj=json.loads(raw)
        except (ValueError,UnicodeDecodeError,TypeError):
            raise MEXCTransportHalt("BROKER_RESPONSE_NOT_JSON")
        if not isinstance(obj,dict) or obj.get("success") is not True:
            raise MEXCTransportHalt("BROKER_REJECTED_OR_MALFORMED_RESPONSE")
        return obj.get("data")

    def account_assets(self):
        return self._exchange("GET","/api/v1/private/account/assets")

    def open_positions(self):
        return self._exchange("GET","/api/v1/private/position/open_positions")

    def position_mode(self):
        return self._exchange("GET","/api/v1/private/position/position_mode")

    def account_fees(self,symbol):
        if symbol not in SYMBOLS:raise MEXCTransportHalt("SYMBOL_BLOCKED")
        return self._exchange("GET","/api/v1/private/account/tiered_fee_rate/v2",
                              {"symbol":symbol})

    def open_orders(self):
        return self._exchange("GET","/api/v1/private/order/list/open_orders",
                              {"page_num":1,"page_size":100})

    def open_stops(self):
        return self._exchange("GET","/api/v1/private/stoporder/open_orders")

    def submit_long(self,symbol,contracts,external_oid,*,ticket):
        if symbol not in SYMBOLS or type(contracts) is not int or contracts!=1:
            raise MEXCTransportHalt("ONE_CONTRACT_LONG_ONLY")
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,32}",external_oid or ""):
            raise MEXCTransportHalt("EXTERNAL_OID_BAD")
        return self._exchange("POST","/api/v1/private/order/create",{
            "symbol":symbol,"price":0,"vol":contracts,"leverage":10,
            "side":1,"type":5,"openType":1,"positionMode":1,
            "externalOid":external_oid},ticket=ticket)

    def place_full_long_position_stop(self,position_id,contracts,price,*,ticket):
        if type(position_id) is not int or position_id<=0 or contracts!=1:
            raise MEXCTransportHalt("INVALID_PROTECTION_QUANTITY_OR_POSITION")
        if not isinstance(price,(str,int,float)) or float(price)<=0:
            raise MEXCTransportHalt("INVALID_STOP_PRICE")
        return self._exchange("POST","/api/v1/private/stoporder/place",{
            "lossTrend":2,"profitTrend":2,"positionId":position_id,
            "vol":contracts,"stopLossPrice":float(price),"takeProfitPrice":0,
            "priceProtect":0,"profitLossVolType":"SAME","volType":2,
            "takeProfitReverse":2,"stopLossReverse":2,
            "takeProfitType":0,"takeProfitOrderPrice":0,
            "stopLossType":0,"stopLossOrderPrice":0},ticket=ticket)
