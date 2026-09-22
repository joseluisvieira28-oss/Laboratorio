from __future__ import annotations

import unittest
from unittest.mock import patch

from radar import __main__ as cli


class _Runtime:
    last_interval=None

    def __init__(self, *, settings):
        self.settings=settings

    def run_loop(self, *, interval_seconds):
        type(self).last_interval=interval_seconds


class ForwardLoopCLITests(unittest.TestCase):
    def test_forward_loop_delegates_to_existing_runtime_without_http(self):
        _Runtime.last_interval=None
        with (
            patch("radar.config.Settings.from_env"),
            patch("radar.forward_web.ForwardShadowRuntime", _Runtime),
        ):
            code=cli.main(["forward-loop","--interval","30"])
        self.assertEqual(code,0)
        self.assertEqual(_Runtime.last_interval,30.0)


if __name__=="__main__":
    unittest.main()
