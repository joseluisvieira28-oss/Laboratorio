from __future__ import annotations

import unittest
from unittest.mock import patch

from radar.supabase_pooler_probe import (
    PROJECT_REGION,
    SupabasePoolerProbeError,
    discover_session_pooler,
    probe_one,
    probe_from_env,
)

EXPECTED_CHAIN_HEAD = "f8b85ba3d45dcb426e37d1a1da543cff61a85d9ea0a01ddc1a07662b9e7c02cd"


class FakeCursor:
    def __init__(self):
        self._row = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql):
        normalized = " ".join(sql.split()).upper()
        if normalized == "SET TRANSACTION READ ONLY":
            self._row = None
            return
        if "FROM RADAR_EVENTS" in normalized:
            self._row = (1032, 1, 1032, EXPECTED_CHAIN_HEAD)
            return
        if normalized == "SELECT COUNT(*) FROM RADAR_EVENT_KEYS":
            self._row = (954,)
            return
        raise AssertionError(normalized)

    def fetchone(self):
        return self._row


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return FakeCursor()


def connector_for_index(index: int):
    expected = f"aws-{index}-{PROJECT_REGION}.pooler.supabase.com"

    def connect(**kwargs):
        assert kwargs["sslmode"] == "require"
        assert kwargs["port"] == 5432
        assert kwargs["dbname"] == "postgres"
        assert kwargs["user"].startswith("radar_runtime.")
        assert kwargs["password"] == "secret"
        if kwargs["host"] != expected:
            raise OSError("tenant or user not found")
        return FakeConnection()

    return connect


class SupabasePoolerProbeTests(unittest.TestCase):
    def test_one_exact_host_is_selected_without_mutation(self):
        result = discover_session_pooler(
            password="secret",
            expected_events=1032,
            expected_keys=954,
            expected_chain_head=EXPECTED_CHAIN_HEAD,
            indices=(0, 1, 2),
            connect_fn=connector_for_index(1),
        )
        self.assertEqual(result["classification"], "EXACT_SESSION_POOLER_DISCOVERED")
        self.assertEqual(
            result["selected_host"],
            f"aws-1-{PROJECT_REGION}.pooler.supabase.com",
        )
        self.assertFalse(result["database_mutation"])
        self.assertFalse(result["secret_value_exposed"])
        self.assertFalse(result["final_cutover_authorized"])
        self.assertEqual(
            sum(1 for x in result["results"] if x["accepted"]),
            1,
        )

    def test_no_matching_host_fails_closed(self):
        result = discover_session_pooler(
            password="secret",
            expected_events=1032,
            expected_keys=954,
            expected_chain_head=EXPECTED_CHAIN_HEAD,
            indices=(0, 1),
            connect_fn=connector_for_index(9),
        )
        self.assertEqual(
            result["classification"],
            "NO_EXACT_SESSION_POOLER_DISCOVERED",
        )
        self.assertIsNone(result["selected_host"])
        self.assertTrue(all(not x["accepted"] for x in result["results"]))

    def test_reachable_but_wrong_boundary_is_not_accepted(self):
        class WrongCursor(FakeCursor):
            def execute(self, sql):
                normalized = " ".join(sql.split()).upper()
                if normalized == "SET TRANSACTION READ ONLY":
                    self._row = None
                    return
                if "FROM RADAR_EVENTS" in normalized:
                    self._row = (1033, 1, 1033, "f" * 64)
                    return
                if normalized == "SELECT COUNT(*) FROM RADAR_EVENT_KEYS":
                    self._row = (955,)
                    return
                raise AssertionError(normalized)

        class WrongConnection(FakeConnection):
            def cursor(self):
                return WrongCursor()

        item = probe_one(
            host="aws-0-eu-central-1.pooler.supabase.com",
            password="secret",
            expected_events=1032,
            expected_keys=954,
            expected_chain_head=EXPECTED_CHAIN_HEAD,
            connect_fn=lambda **_kwargs: WrongConnection(),
        )
        self.assertEqual(item["status"], "REACHABLE_NOT_EQUIVALENT")
        self.assertFalse(item["accepted"])

    def test_connection_error_redacts_password(self):
        secret = "super-secret-value"

        def broken(**_kwargs):
            raise OSError(f"synthetic failure leaked {secret}")

        item = probe_one(
            host="aws-0-eu-central-1.pooler.supabase.com",
            password=secret,
            expected_events=1032,
            expected_keys=954,
            expected_chain_head=EXPECTED_CHAIN_HEAD,
            connect_fn=broken,
        )
        self.assertEqual(item["status"], "CONNECT_FAIL")
        self.assertNotIn(secret, item["error"])
        self.assertIn("[REDACTED]", item["error"])

    def test_password_is_required(self):
        with self.assertRaisesRegex(SupabasePoolerProbeError, "password is required"):
            probe_one(
                host="aws-0-eu-central-1.pooler.supabase.com",
                password="",
                expected_events=1032,
                expected_keys=954,
                expected_chain_head=EXPECTED_CHAIN_HEAD,
                connect_fn=connector_for_index(0),
            )


    def test_env_probe_requires_explicit_audited_identity(self):
        with patch.dict(
            "os.environ",
            {"RADAR_SUPABASE_POOLER_PASSWORD": "secret"},
            clear=True,
        ):
            with self.assertRaisesRegex(
                SupabasePoolerProbeError,
                "RADAR_SUPABASE_POOLER_EXPECTED_EVENTS is required",
            ):
                probe_from_env()

    def test_env_probe_rejects_invalid_chain_head(self):
        with patch.dict(
            "os.environ",
            {
                "RADAR_SUPABASE_POOLER_PASSWORD": "secret",
                "RADAR_SUPABASE_POOLER_EXPECTED_EVENTS": "1035",
                "RADAR_SUPABASE_POOLER_EXPECTED_KEYS": "957",
                "RADAR_SUPABASE_POOLER_EXPECTED_CHAIN_HEAD": "not-a-hash",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                SupabasePoolerProbeError,
                "must be 64 hex chars",
            ):
                probe_from_env()


if __name__ == "__main__":
    unittest.main()
