#!/usr/bin/env python3
"""Deterministic static QA for AAVE R1 V0.3.1 Portal stream retry semantics."""
from __future__ import annotations

import copy
import json
from collections import Counter

import requests

import r1_scaled_ledger_audit_v01 as base


class FakeResponse:
    def __init__(self, rows, fail_after_index=None):
        self.rows = rows
        self.fail_after_index = fail_after_index
        self.closed = False

    def iter_lines(self, decode_unicode=True):
        for idx, row in enumerate(self.rows):
            yield json.dumps(row)
            if self.fail_after_index is not None and idx == self.fail_after_index:
                raise requests.exceptions.ChunkedEncodingError("synthetic truncated stream")

    def close(self):
        self.closed = True


def main() -> int:
    original_from = base.FROM_BLOCK
    original_to = base.TO_BLOCK
    original_window = base.MAX_HTTP_BLOCK_WINDOW
    original_post = base.post_portal
    original_sleep = base.time.sleep

    calls = []
    responses = []

    row_100 = {"header": {"number": 100, "timestamp": 1}, "logs": []}
    row_101 = {"header": {"number": 101, "timestamp": 2}, "logs": []}

    def fake_post(body, stats):
        calls.append(copy.deepcopy(body))
        stats["http_attempts"] += 1
        if len(calls) == 1:
            r = FakeResponse([row_100], fail_after_index=0)
        elif len(calls) == 2:
            r = FakeResponse([row_100, row_101])
        else:
            raise AssertionError("unexpected extra Portal call")
        responses.append(r)
        stats["successful_http_responses"] += 1
        return r

    try:
        base.FROM_BLOCK = 100
        base.TO_BLOCK = 101
        base.MAX_HTTP_BLOCK_WINDOW = 2
        base.post_portal = fake_post
        base.time.sleep = lambda _: None

        stats = Counter()
        rows = list(base.stream_portal([], False, stats))

        assert [r["header"]["number"] for r in rows] == [100, 101]
        assert len(calls) == 2
        assert calls[0] == calls[1]
        assert calls[0]["fromBlock"] == 100
        assert calls[0]["toBlock"] == 101
        assert stats["stream_read_failures"] == 1
        assert stats["stream_read_retries"] == 1
        assert stats["stream_window_attempts"] == 2
        assert stats["stream_window_successes"] == 1
        assert stats["portal_rows"] == 2
        assert all(r.closed for r in responses)
    finally:
        base.FROM_BLOCK = original_from
        base.TO_BLOCK = original_to
        base.MAX_HTTP_BLOCK_WINDOW = original_window
        base.post_portal = original_post
        base.time.sleep = original_sleep

    print(json.dumps({
        "classification": "R1_STREAM_TRANSPORT_QA_PASS",
        "same_window_retried": True,
        "partial_window_discarded": True,
        "stream_read_retries": 1,
        "yielded_rows": 2,
        "scientific_semantics_changed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
