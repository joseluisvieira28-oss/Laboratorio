import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from dream_account.models import Candle
from research.phase_b_h01_discovery_runner_v01 import (
    EFFECTIVE_END_UTC,
    EFFECTIVE_START_UTC,
    HOLDOUT_2026_AUTHORIZED,
    H01_FREEZE_FINGERPRINT,
    LIVE_AUTHORIZED,
    EXCHANGE_MUTATION_AUTHORIZED,
    _freeze_bindings,
    run_h01_discovery,
)
from research.phase_b_h01_mexc_adapter_audit_v01 import source_partition_bounds
from research.phase_b_h01_mexc_discovery_access_v01 import (
    AUTHORIZATION_DOCUMENT_TYPE,
    AUTHORIZATION_STATUS,
    DISCOVERY_END_MONTH,
    DISCOVERY_START_MONTH,
    EXPECTED_MONTHS,
    FAMILY_ID,
    FROZEN_UNIVERSE,
    HYPOTHESIS_ID,
)
from research.phase_b_h01_research_evaluator_v01 import BASE_COHORT_SOURCE
from research.phase_b_research_evaluator_v01 import (
    BootstrapInterval,
    EvaluationMetrics,
    FixedCohortCostMetrics,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "research" / "phase_b_h01_discovery_runner_v01.py"
STEP = 15 * 60 * 1000


def canonical_hash(payload):
    clone = dict(payload)
    clone.pop("fingerprint", None)
    encoded = json.dumps(
        clone,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_authorization(path):
    payload = {
        "document_type": AUTHORIZATION_DOCUMENT_TYPE,
        "version": "0.1",
        "status": AUTHORIZATION_STATUS,
        "hypothesis_id": HYPOTHESIS_ID,
        "family_id": FAMILY_ID,
        "source": "OFFICIAL_MEXC_SPOT_HISTORICAL_ONLY",
        "timeframe": "15m",
        "source_partition_timezone": "UTC+08:00",
        "allowed_start_month": DISCOVERY_START_MONTH,
        "allowed_end_month": DISCOVERY_END_MONTH,
        "universe": list(FROZEN_UNIVERSE),
        "cross_exchange_backfill_allowed": False,
        "interpolation_allowed": False,
        "validation_2025_access_authorized": False,
        "holdout_2026_access_authorized": False,
        "network_download_authorized": False,
        "exchange_mutation_authorized": False,
        "live_trading_authorized": False,
        "fingerprint": "",
    }
    payload["fingerprint"] = canonical_hash(payload)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return payload


def prefix(symbol):
    return f"{symbol[:-4]}_USDT"


def make_expected_empty_files(raw_root):
    raw_root.mkdir(parents=True, exist_ok=True)
    for symbol in FROZEN_UNIVERSE:
        for month in EXPECTED_MONTHS:
            (raw_root / f"{prefix(symbol)}-Min15-{month}-01.csv").write_bytes(b"")


def candle(open_time):
    return Candle(
        open_time=open_time,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        volume=1.0,
        close_time=open_time + STEP - 1,
        closed=True,
    )


def audit_package(symbol, month):
    start, end = source_partition_bounds(month)
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    candles = [candle(start_ms), candle(end_ms - STEP)]
    if month == DISCOVERY_START_MONTH:
        effective_start_ms = int(
            __import__("datetime").datetime.fromisoformat(
                EFFECTIVE_START_UTC.replace("Z", "+00:00")
            ).timestamp()
            * 1000
        )
        candles.append(candle(effective_start_ms))
    candles.sort(key=lambda item: item.open_time)
    manifest = SimpleNamespace(
        status="PASS_H01_MONTH",
        reasons=(),
        fingerprint=f"audit-{symbol}-{month}",
        row_count=len(candles),
        detected_gap_count=0,
        missing_candle_count=0,
    )
    return SimpleNamespace(manifest=manifest, candles=tuple(candles))


def positive_base_metrics():
    return EvaluationMetrics(
        cost_scenario="BASE_SENSITIVITY",
        raw_geometry_count=100,
        net_rr_rejected_count=0,
        selected_trade_count=100,
        overlap_skipped_count=0,
        unresolved_trade_count=0,
        resolved_trade_count=100,
        net_expectancy_r=0.20,
        median_net_r=0.10,
        win_rate=0.55,
        loss_rate=0.45,
        profit_factor_r=1.20,
        tp1_reach_rate=0.60,
        same_bar_ambiguity_rate=0.0,
        time_exit_rate=0.0,
        stop_gap_rate=0.0,
        signal_frequency_per_30d=5.0,
        symbol_distribution={"BTCUSDT": 100},
        contiguous_segment_count=1,
        detected_gap_count=0,
    )


def positive_stress_metrics():
    return FixedCohortCostMetrics(
        cost_scenario="STRESS",
        cohort_source=BASE_COHORT_SOURCE,
        selected_trade_count=100,
        resolved_trade_count=100,
        unresolved_trade_count=0,
        net_expectancy_r=0.10,
        median_net_r=0.05,
        profit_factor_r=1.10,
        net_rr_below_minimum_count=0,
        net_rr_violation_rate=0.0,
    )


def positive_bootstrap():
    return BootstrapInterval(
        method="UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP",
        repetitions=5000,
        seed=230911,
        confidence=0.95,
        sample_days=50,
        lower=0.05,
        point_estimate=0.20,
        upper=0.35,
        undefined_reason=None,
    )


class PhaseBH01DiscoveryRunnerTests(unittest.TestCase):
    def test_frozen_authority_bindings_are_self_consistent(self):
        h01, _, start_ms, end_ms = _freeze_bindings()
        self.assertEqual(h01["fingerprint"], H01_FREEZE_FINGERPRINT)
        self.assertFalse(h01["authority_boundary"]["this_file_authorizes_2025_data_access"])
        self.assertEqual(
            start_ms,
            int(__import__("datetime").datetime.fromisoformat(
                EFFECTIVE_START_UTC.replace("Z", "+00:00")
            ).timestamp() * 1000,
        )
        self.assertEqual(
            end_ms,
            int(__import__("datetime").datetime.fromisoformat(
                EFFECTIVE_END_UTC.replace("Z", "+00:00")
            ).timestamp() * 1000,
        )

    def test_missing_explicit_authorization_blocks_before_market_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            raw.mkdir()
            sentinel = raw / "BTC_USDT-Min15-2025-01-01.csv"
            sentinel.write_bytes(b"DO_NOT_READ")
            output = root / "output"

            receipt = run_h01_discovery(
                raw,
                output,
                authorization_path=root / "missing-authorization.json",
            )

            self.assertEqual(receipt.status, "BLOCKED_PRE_H01_DISCOVERY")
            self.assertTrue(receipt.reasons[0].startswith("DATA_ACCESS_AUTHORIZATION:"))
            self.assertFalse(receipt.source_market_bytes_read)
            self.assertFalse(receipt.h01_evaluation_performed)
            self.assertFalse(output.exists())
            self.assertEqual(sentinel.read_bytes(), b"DO_NOT_READ")

    def test_valid_authorization_but_missing_source_blocks_before_adapter(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            write_authorization(auth)
            with patch(
                "research.phase_b_h01_discovery_runner_v01.adapt_mexc_bulk_csv"
            ) as adapt:
                receipt = run_h01_discovery(
                    root / "raw",
                    root / "output",
                    authorization_path=auth,
                )
            self.assertEqual(receipt.status, "BLOCKED_PRE_H01_DISCOVERY")
            self.assertTrue(receipt.reasons[0].startswith("SOURCE_PREFLIGHT:"))
            self.assertFalse(receipt.source_market_bytes_read)
            self.assertFalse(receipt.h01_evaluation_performed)
            adapt.assert_not_called()

    def test_orchestrator_uses_only_exact_discovery_partitions_and_never_unlocks_data(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            output = root / "output"
            auth = root / "auth.json"
            write_authorization(auth)
            make_expected_empty_files(raw)

            adapter_result = SimpleNamespace(status="PASS_ADAPTER_ONLY")

            def audit_side_effect(*args, **kwargs):
                return audit_package(kwargs["symbol"], kwargs["month"])

            with patch(
                "research.phase_b_h01_discovery_runner_v01.adapt_mexc_bulk_csv",
                return_value=adapter_result,
            ) as adapt, patch(
                "research.phase_b_h01_discovery_runner_v01.write_adapter_receipt"
            ) as write_adapter, patch(
                "research.phase_b_h01_discovery_runner_v01.audit_h01_month",
                side_effect=audit_side_effect,
            ) as audit, patch(
                "research.phase_b_h01_discovery_runner_v01.evaluate_h01_universe",
                return_value=([], positive_base_metrics()),
            ) as evaluate, patch(
                "research.phase_b_h01_discovery_runner_v01.reprice_h01_fixed_cohort",
                return_value=positive_stress_metrics(),
            ), patch(
                "research.phase_b_h01_discovery_runner_v01.day_block_bootstrap_expectancy",
                return_value=positive_bootstrap(),
            ):
                receipt = run_h01_discovery(
                    raw,
                    output,
                    authorization_path=auth,
                )

            self.assertEqual(receipt.status, "H01_DISCOVERY_COMPLETE")
            self.assertTrue(receipt.h01_evaluation_performed)
            self.assertTrue(receipt.validation_unlock_eligible)
            self.assertFalse(receipt.validation_2025_access_performed)
            self.assertFalse(receipt.holdout_2026_access_performed)
            self.assertFalse(receipt.network_access_performed)
            self.assertFalse(receipt.exchange_mutation_performed)
            self.assertFalse(receipt.submitted_to_exchange)
            self.assertEqual(receipt.decision["classification"], "SURVIVES")
            self.assertEqual(adapt.call_count, len(FROZEN_UNIVERSE) * len(EXPECTED_MONTHS))
            self.assertEqual(write_adapter.call_count, adapt.call_count)
            self.assertEqual(audit.call_count, adapt.call_count)
            evaluate.assert_called_once()

            audited_months = {call.kwargs["month"] for call in audit.call_args_list}
            audited_symbols = {call.kwargs["symbol"] for call in audit.call_args_list}
            self.assertEqual(audited_months, set(EXPECTED_MONTHS))
            self.assertEqual(audited_symbols, set(FROZEN_UNIVERSE))
            self.assertFalse(any(month > DISCOVERY_END_MONTH for month in audited_months))

    def test_runner_itself_has_no_network_exchange_or_live_route(self):
        text = MODULE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests",
            "import urllib",
            "import websockets",
            "import socket",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
            "mexc_client",
            "execution_layer",
            "/api/v3/order",
        ):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("2025-09-01.csv", text)
        self.assertNotIn("2025-12-01.csv", text)
        self.assertNotIn("2026-01-01.csv", text)
        self.assertFalse(LIVE_AUTHORIZED)
        self.assertFalse(EXCHANGE_MUTATION_AUTHORIZED)
        self.assertFalse(HOLDOUT_2026_AUTHORIZED)


if __name__ == "__main__":
    unittest.main()
