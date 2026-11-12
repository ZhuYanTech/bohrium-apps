import unittest

from run_posebusters import summarize


class SummaryTests(unittest.TestCase):
    def test_mixed_assessment_states(self):
        rows = [
            {"mol_pred_loaded": "True", "bond_lengths": "True", "number_clashes": "0"},
            {"mol_pred_loaded": "True", "bond_lengths": ""},
            {"mol_pred_loaded": "False", "bond_lengths": ""},
            {"mol_pred_loaded": "", "bond_lengths": ""},
        ]
        summary, _ = summarize(rows, "mol")
        self.assertEqual(
            [(r["通过项数"], r["未通过项数"], r["未评估项数"], r["PB_valid"]) for r in summary],
            [(2, 0, 0, "是"), (1, 0, 1, "未评估"), (0, 1, 1, "否"), (0, 0, 2, "未评估")],
        )
        self.assertTrue(all(r["检查项总数"] == 2 for r in summary))

    def test_no_check_has_a_verdict(self):
        summary, _ = summarize([{"mol_pred_loaded": ""}], "mol")
        self.assertEqual(summary[0]["PB_valid"], "未评估")
        self.assertEqual(summary[0]["通过项数"], 0)


if __name__ == "__main__":
    unittest.main()
