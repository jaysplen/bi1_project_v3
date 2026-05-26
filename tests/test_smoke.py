"""
Three smoke tests for the analytics pipeline. They re-run the relevant W and
check that artefacts and headline KPIs land in a sensible range.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))

from bi_pipeline import EXPORTS, METRICS_PATH, load_data, run_w1, run_w2, run_w3  # noqa: E402


class TestBaseSmoke(unittest.TestCase):
    """Three smoke tests, one per work package."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = load_data()

    def test_w1_rules_and_pareto(self):
        m = run_w1(self.raw)
        rules_csv = EXPORTS / "w1" / "w1_rules.csv"
        self.assertTrue(rules_csv.is_file(), "w1_rules.csv was not produced")
        self.assertGreater(m["rules_count"], 0, "no association rules found")
        self.assertGreaterEqual(m["pareto_cov80_parts"], 5, "Pareto cov80 unreasonably small")

    def test_w2_decision_tree_is_useful(self):
        m = run_w2(self.raw)
        # A depth-6 tree should beat the trivial mean-only baseline clearly.
        self.assertGreater(m["r2"], 0.40, f"W2 R² too low ({m['r2']:.3f})")
        self.assertLess(m["mae"], 3.0, f"W2 MAE too high ({m['mae']:.3f})")

    def test_w3_decision_tree_is_useful(self):
        m = run_w3(self.raw)
        # A single tree at a fixed threshold should catch a noticeable share
        # of failures while keeping accuracy above chance.
        self.assertGreaterEqual(m["recall_failure"], 0.10,
                                f"W3 recall too low ({m['recall_failure']:.3f})")
        self.assertGreater(m["accuracy"], 0.60,
                           f"W3 accuracy too low ({m['accuracy']:.3f})")

    def test_metrics_summary_written(self):
        # main() writes a combined summary; here we just confirm it can be
        # produced and loaded.
        m_w1 = run_w1(self.raw)
        m_w2 = run_w2(self.raw)
        m_w3 = run_w3(self.raw)
        METRICS_PATH.write_text(
            json.dumps({"w1": m_w1, "w2": m_w2, "w3": m_w3}, indent=2)
        )
        self.assertTrue(METRICS_PATH.is_file())
        summary = json.loads(METRICS_PATH.read_text())
        self.assertIn("w1", summary)
        self.assertIn("w2", summary)
        self.assertIn("w3", summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
