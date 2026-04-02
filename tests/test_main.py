import unittest

from main import Matrix, generate_cross_pattern, generate_x_pattern, normalize_label


class FoundationTests(unittest.TestCase):
    def test_matrix_rejects_non_square_input(self) -> None:
        with self.assertRaises(ValueError):
            Matrix([[1, 0, 1], [0, 1, 0]])

    def test_normalize_label_variants(self) -> None:
        self.assertEqual(normalize_label("+"), "Cross")
        self.assertEqual(normalize_label("cross"), "Cross")
        self.assertEqual(normalize_label("x"), "X")

    def test_generate_cross_and_x_patterns(self) -> None:
        cross = generate_cross_pattern(5)
        x_pattern = generate_x_pattern(5)

        self.assertEqual(cross.values[2], [1.0, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual([row[2] for row in cross.values], [1.0, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual(x_pattern.values[0][0], 1.0)
        self.assertEqual(x_pattern.values[0][4], 1.0)
        self.assertEqual(x_pattern.values[2][2], 1.0)


if __name__ == "__main__":
    unittest.main()
