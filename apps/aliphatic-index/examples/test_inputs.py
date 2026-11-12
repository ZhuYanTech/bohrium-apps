import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from run_aliphatic_index import calculate, write_results


class InputTests(unittest.TestCase):
    def test_text_fasta_and_csv(self):
        single, = calculate("av i\nl")
        self.assertEqual((single["protein_id"], single["aliphatic_index"]), ("Sequence", "292.500000"))
        fasta = calculate(">B|note\nAVIL\n>A\nLL")
        table = calculate('name,seq\n"B|note","AVIL"\nA,LL\n', "csv")
        self.assertEqual(table, fasta)
        with TemporaryDirectory() as temporary:
            dest = Path(temporary)
            write_results("AVIL", dest)
            with (dest / "results.csv").open() as handle:
                self.assertEqual(list(csv.reader(handle))[-1], ["Sequence", "4", "292.50"])

    def test_first_pdb_model_and_modified_residue(self):
        def atom(record, serial, residue, chain, index):
            return f"{record:6}{serial:5}  CA  {residue:3} {chain}{index:4}    0.0"
        pdb = "\n".join([
            "MODEL        1", atom("ATOM", 1, "ALA", "A", 1),
            atom("HETATM", 2, "MSE", "A", 2), atom("ATOM", 3, "VAL", "B", 1),
            "ENDMDL", "MODEL        2", atom("ATOM", 4, "LEU", "A", 1), "ENDMDL",
        ])
        a, b = calculate(pdb, "pdb", "example")
        self.assertEqual((a["protein_id"], a["length"], a["aliphatic_index"]), ("example_A", 2, "50.000000"))
        self.assertEqual((b["protein_id"], b["length"], b["aliphatic_index"]), ("example_B", 1, "290.000000"))

    def test_invalid_inputs(self):
        for data, fmt in [(">ok\nAA\n>bad\nAX", "fasta"), ("id,sequence\nx\n", "csv"),
                          ("id,sequence\nx,AA,extra\n", "csv"), (">empty\n", "fasta")]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                calculate(data, fmt)


if __name__ == "__main__":
    unittest.main()
