#!/usr/bin/env python3
"""Deterministic transport QA for AAVE R1 global-state V0.4.1."""
from __future__ import annotations

import copy
import json
from collections import Counter

import requests

import r1_global_state_v01 as base


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


def test_truncated_page_retry():
    original_post = base.post
    original_sleep = base.time.sleep
    original_window = base.WINDOW
    calls = []
    responses = []

    row_100 = {"header": {"number": 100, "timestamp": 1}, "logs": []}
    row_101 = {"header": {"number": 101, "timestamp": 2}, "logs": []}

    def fake_post(body, stats):
        calls.append(copy.deepcopy(body))
        if len(calls) == 1:
            r = FakeResponse([row_100], fail_after_index=0)
        elif len(calls) == 2:
            r = FakeResponse([row_100, row_101])
        else:
            raise AssertionError("unexpected extra retry")
        responses.append(r)
        stats["http_attempts"] += 1
        stats["successful_http_responses"] += 1
        return r

    try:
        base.post = fake_post
        base.time.sleep = lambda _: None
        base.WINDOW = 2
        stats = Counter()
        rows = list(base.stream(100, 101, [], stats))
        assert [x["header"]["number"] for x in rows] == [100, 101]
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
        base.post = original_post
        base.time.sleep = original_sleep
        base.WINDOW = original_window


def test_empty_window_semantics():
    original_post = base.post
    original_window = base.WINDOW
    calls = []

    def fake_post(body, stats):
        calls.append(copy.deepcopy(body))
        stats["http_attempts"] += 1
        stats["successful_http_responses"] += 1
        return FakeResponse([])

    try:
        base.post = fake_post
        base.WINDOW = 2
        stats = Counter()
        rows = list(base.stream(200, 201, [], stats))
        assert rows == []
        assert len(calls) == 1
        assert calls[0]["fromBlock"] == 200
        assert calls[0]["toBlock"] == 201
        assert stats["empty_windows"] == 1
        assert stats["portal_rows"] == 0
        assert stats["stream_window_successes"] == 1
    finally:
        base.post = original_post
        base.WINDOW = original_window


def main() -> int:
    test_truncated_page_retry()
    test_empty_window_semantics()
    print(json.dumps({
        "classification": "R1_GLOBAL_STREAM_TRANSPORT_QA_PASS",
        "partial_page_discarded": True,
        "same_window_retried": True,
        "empty_window_semantics_preserved": True,
        "scientific_semantics_changed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
