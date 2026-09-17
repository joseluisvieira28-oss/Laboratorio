from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from radar.web import assert_writable_storage, build_handler


class RenderWebRuntimeTests(unittest.TestCase):
    def _start_server(self, status_path: str):
        server = ThreadingHTTPServer(("127.0.0.1", 0), build_handler(status_path))
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def test_health_ok_returns_200(self):
        with TemporaryDirectory() as tmp:
            status = Path(tmp) / "status.json"
            status.write_text(
                json.dumps(
                    {
                        "service": "CRYPTO_EDGE_RADAR",
                        "version": "0.4",
                        "mode": "PUBLIC_SHADOW_ONLY",
                        "health": "OK",
                        "cycle": 7,
                        "provider": "TEST_PUBLIC",
                        "consecutive_failures": 0,
                    }
                ),
                encoding="utf-8",
            )
            server, thread = self._start_server(str(status))
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/health", timeout=2) as response:
                    payload = json.loads(response.read())
                    self.assertEqual(response.status, 200)
                    self.assertEqual(payload["health"], "OK")
                    self.assertEqual(payload["cycle"], 7)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_health_fail_closed_returns_503(self):
        with TemporaryDirectory() as tmp:
            status = Path(tmp) / "status.json"
            status.write_text(
                json.dumps(
                    {
                        "service": "CRYPTO_EDGE_RADAR",
                        "version": "0.4",
                        "mode": "PUBLIC_SHADOW_ONLY",
                        "health": "FAIL_CLOSED",
                        "cycle": 3,
                        "provider": "TEST_PUBLIC",
                        "consecutive_failures": 2,
                    }
                ),
                encoding="utf-8",
            )
            server, thread = self._start_server(str(status))
            try:
                with self.assertRaises(HTTPError) as caught:
                    urlopen(f"http://127.0.0.1:{server.server_port}/health", timeout=2)
                self.assertEqual(caught.exception.code, 503)
                payload = json.loads(caught.exception.read())
                self.assertEqual(payload["health"], "FAIL_CLOSED")
                self.assertEqual(payload["consecutive_failures"], 2)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_status_exposes_full_persisted_status(self):
        with TemporaryDirectory() as tmp:
            status = Path(tmp) / "status.json"
            expected = {"health": "OK", "cycle": 11, "valid_signal_count": 0}
            status.write_text(json.dumps(expected), encoding="utf-8")
            server, thread = self._start_server(str(status))
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/status", timeout=2) as response:
                    self.assertEqual(json.loads(response.read()), expected)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_storage_probe_accepts_writable_paths(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            assert_writable_storage(
                str(base / "db" / "radar.sqlite3"),
                str(base / "state" / "status.json"),
                str(base / "events" / "notifications.jsonl"),
            )
            self.assertTrue((base / "db").is_dir())
            self.assertTrue((base / "state").is_dir())
            self.assertTrue((base / "events").is_dir())


if __name__ == "__main__":
    unittest.main()
