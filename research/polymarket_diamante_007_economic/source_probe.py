"""Check contract metadata and official settlements for 36 UTC windows."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from subprocess import check_output, CalledProcessError
import json

def lookup(start):
    slug = f"btc-updown-5m-{int(start.timestamp())}"
    try:
        market = json.loads(check_output(["curl", "-fsSL", "--max-time", "18",
            f"https://gamma-api.polymarket.com/markets/slug/{slug}"]))
        authority = {key: market.get(key) for key in
            ("conditionId", "slug", "resolutionSource", "umaResolutionStatus",
             "outcomes", "outcomePrices", "clobTokenIds")}
        assert authority["slug"] == slug
        authority["utc_start"] = start.isoformat()
        return authority
    except (CalledProcessError, ValueError, AssertionError) as exc:
        return {"slug": slug, "utc_start": start.isoformat(), "error": type(exc).__name__}

starts = [datetime(2026, 11, day, 12, tzinfo=timezone.utc)+timedelta(minutes=5*i)
          for day in (7,) for i in range(12,24)]
with ThreadPoolExecutor(8) as executor:
    print(json.dumps(list(executor.map(lookup, starts)),indent=2))
