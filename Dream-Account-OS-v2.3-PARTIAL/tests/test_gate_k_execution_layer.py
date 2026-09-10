from datetime import datetime, timedelta, timezone
import unittest

from dream_account.execution_layer import (
    ExecutionMode,
    MEXCAuthenticatedAdapter,
    MockMEXCExecutionAdapter,
    OrderState,
    SafetyContext,
    TradeProposal,
    create_shadow_intent,
    make_idempotency_key,
    validate_proposal,
)


NOW = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)


def proposal(**overrides):
    payload = dict(
        proposal_id="p-001",
        authority_id="AUTH-001",
        evidence_fingerprint="abc123",
        created_at_utc=(NOW - timedelta(seconds=1)).isoformat(),
        expires_at_utc=(NOW + timedelta(minutes=5)).isoformat(),
        symbol="BTCUSDT",
        market_type="SPOT",
        side="BUY",
        order_type="LIMIT",
        reference_price=100.0,
        quantity=0.01,
        stop_spec={"type": "price", "value": 95.0},
        exit_spec={"type": "price", "value": 110.0},
        max_slippage_bps=10.0,
        risk_allocation_id="RISK-001",
        execution_mode=ExecutionMode.SHADOW,
    )
    payload.update(overrides)
    return TradeProposal(**payload)


def safety(**overrides):
    payload = dict(market_data_timestamp_utc=(NOW - timedelta(seconds=2)).isoformat())
    payload.update(overrides)
    return SafetyContext(**payload)


class GateKExecutionLayerTests(unittest.TestCase):
    def test_valid_shadow_proposal(self):
        result = validate_proposal(proposal(), safety(), now_utc=NOW)
        self.assertTrue(result.accepted)
        self.assertEqual(result.state, OrderState.VALIDATED)

    def test_shadow_is_default(self):
        p = proposal()
        self.assertEqual(p.execution_mode, ExecutionMode.SHADOW)

    def test_live_modes_rejected(self):
        for mode in (ExecutionMode.MICRO_LIVE, ExecutionMode.CONTROLLED_LIVE):
            result = validate_proposal(proposal(execution_mode=mode), safety(), now_utc=NOW)
            self.assertFalse(result.accepted)
            self.assertIn("gate_k_shadow_only", result.reasons)
            with self.assertRaises(RuntimeError):
                create_shadow_intent(proposal(execution_mode=mode))

    def test_live_adapter_is_hard_disabled(self):
        p = proposal()
        intent = create_shadow_intent(p)
        with self.assertRaises(RuntimeError):
            MEXCAuthenticatedAdapter().submit(p, intent)

    def test_mock_adapter_never_submits_and_is_idempotent(self):
        p = proposal()
        intent = create_shadow_intent(p)
        adapter = MockMEXCExecutionAdapter()
        first = adapter.submit(p, intent)
        second = adapter.submit(p, intent)
        self.assertIs(first, second)
        self.assertFalse(first.submitted_to_exchange)
        self.assertEqual(first.state, OrderState.SHADOW_RECORDED)
        self.assertEqual(len(adapter.receipts), 1)

    def test_idempotency_key_is_stable_per_leg(self):
        self.assertEqual(make_idempotency_key("p1", "ENTRY"), make_idempotency_key("p1", "ENTRY"))
        self.assertNotEqual(make_idempotency_key("p1", "ENTRY"), make_idempotency_key("p1", "EXIT"))

    def test_missing_authority_rejected(self):
        result = validate_proposal(proposal(authority_id=""), safety(), now_utc=NOW)
        self.assertFalse(result.accepted)
        self.assertIn("missing_authority_id", result.reasons)

    def test_expired_rejected(self):
        result = validate_proposal(
            proposal(expires_at_utc=(NOW - timedelta(milliseconds=1)).isoformat()),
            safety(),
            now_utc=NOW,
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.state, OrderState.EXPIRED)

    def test_stale_market_data_rejected(self):
        result = validate_proposal(
            proposal(),
            safety(market_data_timestamp_utc=(NOW - timedelta(seconds=31)).isoformat()),
            now_utc=NOW,
        )
        self.assertFalse(result.accepted)
        self.assertIn("stale_market_data", result.reasons)

    def test_future_market_data_rejected(self):
        result = validate_proposal(
            proposal(),
            safety(market_data_timestamp_utc=(NOW + timedelta(seconds=1)).isoformat()),
            now_utc=NOW,
        )
        self.assertFalse(result.accepted)
        self.assertIn("future_market_data", result.reasons)

    def test_symbol_not_api_tradable_rejected(self):
        result = validate_proposal(proposal(), safety(api_tradable=False), now_utc=NOW)
        self.assertFalse(result.accepted)
        self.assertIn("symbol_not_api_tradable", result.reasons)

    def test_precision_and_minimum_rejected(self):
        result = validate_proposal(
            proposal(), safety(precision_valid=False, minimum_valid=False), now_utc=NOW
        )
        self.assertIn("precision_invalid", result.reasons)
        self.assertIn("minimum_invalid", result.reasons)

    def test_slippage_breach_rejected(self):
        result = validate_proposal(
            proposal(max_slippage_bps=5.0), safety(observed_slippage_bps=5.1), now_utc=NOW
        )
        self.assertIn("slippage_breach", result.reasons)

    def test_kill_switch_rejected(self):
        result = validate_proposal(proposal(), safety(kill_switch=True), now_utc=NOW)
        self.assertFalse(result.accepted)
        self.assertEqual(result.state, OrderState.KILL_SWITCHED)

    def test_daily_loss_lock_rejected(self):
        result = validate_proposal(proposal(), safety(daily_loss_locked=True), now_utc=NOW)
        self.assertIn("daily_loss_lock", result.reasons)

    def test_unresolved_reconciliation_rejected(self):
        result = validate_proposal(proposal(), safety(reconciliation_clear=False), now_utc=NOW)
        self.assertIn("reconciliation_required", result.reasons)

    def test_storage_unsafe_rejected(self):
        result = validate_proposal(proposal(), safety(storage_safe=False), now_utc=NOW)
        self.assertIn("storage_unsafe", result.reasons)

    def test_auth_unhealthy_rejected(self):
        result = validate_proposal(proposal(), safety(auth_healthy=False), now_utc=NOW)
        self.assertIn("auth_unhealthy", result.reasons)

    def test_clock_skew_rejected(self):
        result = validate_proposal(proposal(), safety(clock_skew_ms=5001), now_utc=NOW)
        self.assertIn("clock_skew", result.reasons)

    def test_invalid_numeric_fields_rejected(self):
        result = validate_proposal(
            proposal(reference_price=0, quantity=0, max_slippage_bps=-1), safety(), now_utc=NOW
        )
        self.assertIn("invalid_reference_price", result.reasons)
        self.assertIn("invalid_quantity", result.reasons)
        self.assertIn("invalid_slippage_limit", result.reasons)

    def test_missing_stop_rejected(self):
        result = validate_proposal(proposal(stop_spec={}), safety(), now_utc=NOW)
        self.assertIn("missing_stop_spec", result.reasons)

    def test_invalid_timestamp_rejected(self):
        result = validate_proposal(proposal(created_at_utc="not-a-time"), safety(), now_utc=NOW)
        self.assertEqual(result.reasons, ("invalid_timestamp",))


if __name__ == "__main__":
    unittest.main()
