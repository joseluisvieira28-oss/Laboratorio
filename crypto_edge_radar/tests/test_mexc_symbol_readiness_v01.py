from types import SimpleNamespace

from radar.mexc_symbol_readiness_v01 import run_symbol_readiness


class Feed:
    def contract_row(self, symbol):
        return {
            "symbol": symbol,
            "apiAllowed": True,
            "state": 0,
            "futureType": 1,
            "positionOpenType": 3,
            "minVol": 1,
            "volUnit": 1,
            "contractSize": 0.1,
            "priceUnit": 0.001,
            "minLeverage": 1,
            "maxLeverage": 200,
        }

    def all_market_snapshots(self):
        return {
            "AVAXUSDT": SimpleNamespace(last_price=10.0),
            "BNBUSDT": SimpleNamespace(last_price=800.0),
        }

    def funding_rate(self, symbol):
        return {
            "fundingRate": 0.0001,
            "nextSettleTime": 123,
            "idxPrice": 10,
            "fairPrice": 10,
        }


class Client:
    def __init__(self, global_positions=None):
        self.global_positions = global_positions or []

    def fee_details(self, symbol):
        return {"realMakerFee": 0.0006, "realTakerFee": 0.0008}

    def open_positions(self, symbol=None):
        if symbol:
            return [p for p in self.global_positions if p.get("symbol") == symbol]
        return list(self.global_positions)

    def open_orders(self, symbol=None):
        return []

    def leverage(self, symbol):
        return [{"positionType": 1, "openType": 1, "leverage": 1, "autoAddIm": False}]

    def risk_limit(self, symbol):
        return {"symbol": symbol}


def test_avax_symbol_readiness_passes_when_account_has_no_open_positions():
    out = run_symbol_readiness(
        symbol="AVAX_USDT",
        private_client=Client(),
        public_feed=Feed(),
    )
    assert out["pass"] is True
    assert out["status"] == "PASS_TECHNICAL_READINESS_ONLY"
    assert out["authority"]["live_activation_authorized"] is False


def test_bnb_symbol_readiness_is_blocked_by_existing_options_position():
    out = run_symbol_readiness(
        symbol="BNB_USDT",
        private_client=Client(global_positions=[{"symbol": "BTC_USDT"}]),
        public_feed=Feed(),
    )
    assert out["pass"] is False
    assert "GLOBAL_OPEN_FUTURES_POSITION_PRESENT" in out["blockers"]


def test_symbol_specific_existing_position_is_also_fail_closed():
    out = run_symbol_readiness(
        symbol="AVAX_USDT",
        private_client=Client(global_positions=[{"symbol": "AVAX_USDT"}]),
        public_feed=Feed(),
    )
    assert out["pass"] is False
    assert "AVAX_USDT_OPEN_POSITION_PRESENT" in out["blockers"]
