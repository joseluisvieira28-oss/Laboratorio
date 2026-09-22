from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from radar import __main__ as cli


class _Runtime:
    def __init__(self, *, settings):
        self.settings=settings

    def run_cycle(self):
        return {
            "health":"OK",
            "mode":"PUBLIC_SHADOW_ONLY",
            "authenticated_exchange_api_used":False,
            "orders_created":False,
            "exchange_mutation_performed":False,
            "live_capital_enabled":False,
        }


class _BadRuntime(_Runtime):
    def run_cycle(self):
        out=super().run_cycle()
        out["health"]="DEGRADED_FAIL_CLOSED"
        return out


class ForwardOnceCLITests(unittest.TestCase):
    def test_forward_once_runs_exactly_one_existing_runtime_cycle(self):
        with (
            patch("radar.config.Settings.from_env"),
            patch("radar.forward_web.ForwardShadowRuntime", _Runtime),
            patch("builtins.print") as printer,
        ):
            code=cli.main(["forward-once"])
        self.assertEqual(code,0)
        payload=json.loads(printer.call_args.args[0])
        self.assertEqual(payload["health"],"OK")
        self.assertFalse(payload["orders_created"])
        self.assertFalse(payload["exchange_mutation_performed"])
        self.assertFalse(payload["live_capital_enabled"])

    def test_forward_once_returns_nonzero_on_degraded_state(self):
        with (
            patch("radar.config.Settings.from_env"),
            patch("radar.forward_web.ForwardShadowRuntime", _BadRuntime),
            patch("builtins.print"),
        ):
            code=cli.main(["forward-once"])
        self.assertEqual(code,2)


if __name__=="__main__":
    unittest.main()
