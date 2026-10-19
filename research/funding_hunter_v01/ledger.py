"""Offline accounting primitives. No network, credentials, collector or trading.
Synthetic diagnostics only; this module does not implement source approval or promotion.
"""
from decimal import Decimal, InvalidOperation
import json

D = Decimal
def number(x):
    if isinstance(x, bool):
        raise ValueError("boolean numeric field")
    try:
        value = D(str(x))
    except (InvalidOperation, TypeError):
        raise ValueError("invalid numeric field") from None
    if not value.is_finite():
        raise ValueError("nonfinite field")
    return value

def funding(side, quantity, multiplier, settlement_price, rate):
    if side not in (-1, 1):
        raise ValueError("side")
    q, m, p, r = map(number, (quantity, multiplier, settlement_price, rate))
    if min(q, m, p) <= 0:
        raise ValueError("positive position and price required")
    return -side*q*m*p*r

def cost_floor(n=1000, stress=False):
    n = number(n)
    if n <= 0:
        raise ValueError("notional")
    # Equal unchanged notionals only. Actual fill fees must use actual notionals.
    return n * (D(22) + (D(28) if stress else D(8))) / D(10000)

def four_commissions(notionals):
    if len(notionals) != 4:
        raise ValueError("exactly MEXC open/close, Binance open/close")
    ns = list(map(number, notionals))
    if min(ns) <= 0:
        raise ValueError("notional")
    return sum(n*r for n,r in zip(ns, (D(".0006"),D(".0006"),D(".0005"),D(".0005"))))

def validate_history(raw, venue, symbol, start, end):
    """Strict parsed funding-history shape validator, not completeness certification.
    start/end are epoch ms; this research version refuses any 2026 market row.
    Full coverage, dated schedules, exact marks, books and fee evidence remain
    separate mandatory gates. A schema success cannot approve economics.
    """
    if venue not in ("MEXC","BINANCE") or end >= 1767225600000 or start > end:
        raise ValueError("window or venue")
    def unique(pairs):
        out = {}
        for k,v in pairs:
            if k in out:
                raise ValueError("duplicate JSON key")
            out[k] = v
        return out
    obj = json.loads(raw, object_pairs_hook=unique, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    if venue == "MEXC":
        if not isinstance(obj, dict) or obj.get("success") is not True or type(obj.get("code")) is not int or obj["code"] != 0:
            raise ValueError("MEXC error")
        data = obj.get("data")
        if not isinstance(data, dict):
            raise ValueError("missing pagination")
        for k in ("pageSize","totalCount","totalPage","currentPage"):
            if type(data.get(k)) is not int or data[k] <= 0:
                raise ValueError("missing pagination")
        rows = data.get("resultList")
        if not isinstance(rows,list) or len(rows)>data["pageSize"] or data["currentPage"]>data["totalPage"]:
            raise ValueError("pagination")
        if data["totalPage"] != (data["totalCount"] + data["pageSize"] - 1)//data["pageSize"]:
            raise ValueError("pagination totals")
        key = "settleTime"
    else:
        rows, key = obj, "fundingTime"
    if not isinstance(rows,list) or not rows:
        raise ValueError("empty funding history")
    seen = set()
    for row in rows:
        if not isinstance(row,dict) or row.get("symbol") != symbol:
            raise ValueError("symbol")
        ts = row.get(key)
        if type(ts) is not int or not start <= ts <= end or ts in seen:
            raise ValueError("duplicate/out-of-window timestamp")
        seen.add(ts)
        number(row.get("fundingRate"))
        if venue == "MEXC" and (type(row.get("collectCycle")) is not int or row["collectCycle"] not in (1,4,8)):
            raise ValueError("unverified interval")
        if venue == "BINANCE" and number(row.get("markPrice")) <= 0:
            raise ValueError("missing exact mark")
    return len(rows)

if __name__ == "__main__":
    print(json.dumps({"synthetic_only": True, "baseline_cost_usdt_N1000": str(cost_floor()),
                      "stress_cost_usdt_N1000": str(cost_floor(stress=True)),
                      "verdict": "SOURCE_BLOCKED", "economic_outcomes_computed": False}, indent=2))
