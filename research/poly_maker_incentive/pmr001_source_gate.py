"""PMR-001: one-shot public Gamma market-maker incentive census. Research-only."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import statistics
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE = "https://gamma-api.polymarket.com/markets"
OFFSETS = (0, 100)
LIMIT = 100
MAX_BODY_BYTES = 3_000_000
MAX_TIMEOUT_SECONDS = 10
CAPS_SHARES = (50, 100, 200)


class SourceBlocked(ValueError):
    pass


def positive_decimal(value: object, *, strict=False) -> Decimal:
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0 or (strict and n <= 0):
            raise SourceBlocked("NONPOSITIVE_OR_NONFINITE_NUMERIC_FIELD")
        return n
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise SourceBlocked("INVALID_NUMERIC_FIELD") from exc


def valid_reward_rate(row: dict, today: date) -> Decimal:
    rewards = row.get("clobRewards")
    if rewards is None:
        return Decimal("0")
    if not isinstance(rewards, list):
        raise SourceBlocked("REWARD_LIST_SCHEMA_INVALID")
    total = Decimal("0")
    for reward in rewards:
        if not isinstance(reward, dict):
            raise SourceBlocked("REWARD_ROW_SCHEMA_INVALID")
        rate = positive_decimal(reward.get("rewardsDailyRate"), strict=False)
        try:
            since = date.fromisoformat(str(reward["startDate"])[:10])
            until = (date.fromisoformat(str(reward["endDate"])[:10])
                     if reward.get("endDate") else None)
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceBlocked("REWARD_DATE_SCHEMA_INVALID") from exc
        if since <= today and (until is None or until >= today):
            total += rate
    return total


def adjudicate(pages: list[list[dict]], today: date) -> dict:
    if len(pages) != len(OFFSETS) or any(not isinstance(p, list) for p in pages):
        raise SourceBlocked("INCOMPLETE_FROZEN_PAGES")
    markets = [m for page in pages for m in page]
    if len(markets) == 0:
        raise SourceBlocked("EMPTY_GAMMA_RESPONSE_CANNOT_GENERALIZE")
    unique = set()
    candidates = []
    for m in markets:
        if not isinstance(m, dict):
            raise SourceBlocked("MARKET_SCHEMA_INVALID")
        ident = str(m.get("id") or "")
        if not ident or ident in unique:
            raise SourceBlocked("DUPLICATE_OR_MISSING_MARKET_ID")
        unique.add(ident)
        if not m.get("active") or m.get("closed") or not m.get("acceptingOrders"):
            continue
        if not m.get("enableOrderBook"):
            continue
        rate = valid_reward_rate(m, today)
        if rate <= 0:
            continue
        minsize = positive_decimal(m.get("rewardsMinSize"), strict=False)
        maxspread = positive_decimal(m.get("rewardsMaxSpread"), strict=False)
        liquidity = positive_decimal(m.get("liquidityNum", m.get("liquidity", 0)))
        if not (minsize > 0 and maxspread > 0 and liquidity > 0):
            continue
        candidates.append({
            "id": ident,
            "slug": str(m.get("slug") or "")[:180],
            "reward_daily_pool_usdc_all_makers": float(rate),
            "rewards_min_size_shares": float(minsize),
            "rewards_max_spread_value_as_reported": float(maxspread),
            "market_liquidity_usdc": float(liquidity),
        })
    reward_total = sum(x["reward_daily_pool_usdc_all_makers"] for x in candidates)
    sizes = [x["rewards_min_size_shares"] for x in candidates]
    return {
        "source_verdict": ("SOURCE_PASS_REWARDS_EXIST_BUT_EDGE_UNPROVEN" if candidates
                            else "SAMPLE_ZERO_ACTIVE_REWARDS"),
        "profitability_verdict": "UNPROVEN",
        "orders_created": False,
        "trading_authority": "NONE",
        "sample_kind": "TOP_VOLUMED_200_SNAPSHOT_NOT_UNBIASED_CENSUS",
        "pages_requested": list(OFFSETS),
        "markets_returned": len(markets),
        "qualified_active_reward_markets": len(candidates),
        "eligible_reward_market_count_by_min_shares": {
            str(cap): sum(n <= cap for n in sizes) for cap in CAPS_SHARES
        },
        "microcap_100shares_sample_not_eligible": bool(candidates and all(n > 100 for n in sizes)),
        "median_rewards_min_size_shares": statistics.median(sizes) if sizes else None,
        "max_single_market_daily_pool_usdc": max((x["reward_daily_pool_usdc_all_makers"] for x in candidates), default=None),
        "sum_market_daily_pools_usdc_sample": round(reward_total, 5),
        "meaning_of_pool": "SHARED_ACROSS_ALL_MAKERS_NOT_USER_EXPECTED_REVENUE",
        "user_net_income_usdc": None,
        "competition_score_or_fill_observed": False,
        "markets_sample": sorted(candidates, key=lambda x: x["reward_daily_pool_usdc_all_makers"], reverse=True)[:10],
    }


def fetch_one(offset: int) -> list[dict]:
    params = urlencode({
        "active": "true", "closed": "false", "limit": LIMIT,
        "order": "volume24hr", "ascending": "false", "offset": offset,
    })
    req = Request(BASE + "?" + params,
                  headers={"Accept": "application/json", "User-Agent": "CryptoLab-PMR001-ReadOnly/1.0"},
                  method="GET")
    try:
        with urlopen(req, timeout=MAX_TIMEOUT_SECONDS) as resp:
            if resp.status != 200:
                raise SourceBlocked("HTTP_STATUS_NON_200")
            raw = resp.read(MAX_BODY_BYTES + 1)
        if len(raw) > MAX_BODY_BYTES:
            raise SourceBlocked("SOURCE_TOO_LARGE")
        result = json.loads(raw)
        if not isinstance(result, list):
            raise SourceBlocked("API_NOT_MARKET_LIST")
        return result
    except SourceBlocked:
        raise
    except Exception as exc:
        raise SourceBlocked("PUBLIC_GAMMA_TRANSPORT_" + type(exc).__name__) from exc


def run() -> dict:
    result = {
        "source_verdict": "SOURCE_BLOCKED",
        "profitability_verdict": "UNPROVEN",
        "orders_created": False,
        "trading_authority": "NONE",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Gamma public GET /markets",
        "markets_returned": None,
        "user_net_income_usdc": None,
    }
    try:
        pages = [fetch_one(i) for i in OFFSETS]
        result.update(adjudicate(pages, datetime.now(timezone.utc).date()))
    except SourceBlocked as exc:
        result["reason"] = str(exc)
    return result


if __name__ == "__main__":
    report = run()
    where = Path(os.environ.get("PMR001_RECEIPT_PATH", "PMR001_SOURCE_RECEIPT.json"))
    where.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps(report, indent=2, sort_keys=True))
