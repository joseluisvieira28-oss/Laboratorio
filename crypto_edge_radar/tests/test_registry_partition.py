import json
from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[1]


class RegistryPartitionTests(unittest.TestCase):
    def _load(self,name):
        return json.loads((ROOT/name).read_text(encoding="utf-8"))

    def test_active_archive_and_protected_are_pairwise_disjoint(self):
        active=self._load("deployment_registry_v1.json")
        archive=self._load("archive_registry_v1.json")
        protected=self._load("protected_research_registry_v1.json")

        a={x["strategy_id"] for x in active["candidates"]}
        z={x["strategy_id"] for x in archive["candidates"]}
        p={x["research_id"] for x in protected["entries"]}

        self.assertEqual(len(a),6)
        self.assertEqual(len(z),21)
        self.assertEqual(len(p),6)
        self.assertFalse(a & z)
        self.assertFalse(a & p)
        self.assertFalse(z & p)

    def test_protected_research_is_not_silently_no_edge_or_motorized(self):
        protected=self._load("protected_research_registry_v1.json")
        for row in protected["entries"]:
            self.assertFalse(row["motor_eligible_now"],row)
            self.assertFalse(row.get("no_edge_claim",False),row)

    def test_active_registry_safety_is_still_no_capital_no_orders(self):
        active=self._load("deployment_registry_v1.json")
        safety=active["operational_shadow_v09"]["safety"]
        self.assertFalse(safety["authenticated_exchange_api_enabled"])
        self.assertFalse(safety["orders_created"])
        self.assertFalse(safety["exchange_mutation_performed"])
        self.assertFalse(safety["live_capital_enabled"])
        self.assertFalse(safety["merge_main"])


if __name__=="__main__":
    unittest.main()
