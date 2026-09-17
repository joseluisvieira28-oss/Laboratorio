from radar.market import MarketDataError, MEXCFuturesPublicFeed


class StubMEXCFeed(MEXCFuturesPublicFeed):
    def __init__(self):
        super().__init__(timeout=1)

    def _get_json(self, path: str):
        if path == "/api/v1/contract/ticker":
            return {
                "success": True,
                "code": 0,
                "data": [
                    {
                        "symbol": "BTC_USDT",
                        "lastPrice": 100.0,
                        "bid1": 99.9,
                        "ask1": 100.1,
                        "amount24": 250000000.0,
                    },
                    {
                        "symbol": "ETH_USDT",
                        "lastPrice": 50.0,
                        "bid1": 49.9,
                        "ask1": 50.1,
                        "amount24": 150000000.0,
                    },
                ],
            }
        if path == "/api/v1/contract/detail":
            return {
                "success": True,
                "code": 0,
                "data": [
                    {"symbol": "BTC_USDT", "quoteCoin": "USDT", "apiAllowed": True},
                    {"symbol": "ETH_USDT", "quoteCoin": "USDT", "apiAllowed": True},
                    {"symbol": "BAD_USDT", "quoteCoin": "USDT", "apiAllowed": False},
                ],
            }
        raise AssertionError(path)


def test_mexc_normalizes_symbols_and_market_snapshot():
    feed = StubMEXCFeed()
    snapshots = feed.all_market_snapshots()
    assert set(snapshots) == {"BTCUSDT", "ETHUSDT"}
    assert snapshots["BTCUSDT"].last_price == 100.0
    assert snapshots["BTCUSDT"].bid_price == 99.9
    assert snapshots["BTCUSDT"].ask_price == 100.1
    assert snapshots["BTCUSDT"].quote_volume_24h == 250000000.0


def test_mexc_liquid_eligibility_respects_api_allowed():
    feed = StubMEXCFeed()
    assert feed.eligible_usdt_perpetual_symbols() == {"BTCUSDT", "ETHUSDT"}


def test_mexc_feed_has_only_allowlisted_public_get_paths():
    feed = MEXCFuturesPublicFeed(timeout=1)
    assert feed.base_url == "https://api.mexc.com"
    assert feed.allowed_paths == {
        "/api/v1/contract/detail",
        "/api/v1/contract/ticker",
    }
    try:
        feed._get_json("/api/v1/private/order/submit")
    except MarketDataError as exc:
        assert "blocked non-allowlisted public path" in str(exc)
    else:
        raise AssertionError("private/order path must be blocked")
