import unittest

from main import Matrix, generate_cross_pattern, generate_x_pattern, normalize_label
from main import EPSILON, benchmark_mac, judge_scores, mac_1d, mac_2d


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


class MacTests(unittest.TestCase):
    def test_mac_scores_and_flattened_scores_match(self) -> None:
        cross = generate_cross_pattern(3)
        x_pattern = generate_x_pattern(3)

        self.assertEqual(mac_2d(cross, cross), 5.0)
        self.assertEqual(mac_2d(cross, x_pattern), 1.0)
        self.assertEqual(mac_2d(cross, x_pattern), mac_1d(cross.flatten(), x_pattern.flatten()))

    def test_judge_scores_uses_epsilon_for_ties(self) -> None:
        self.assertEqual(judge_scores(1.0, 1.0 + (EPSILON / 2)), "UNDECIDED")
        self.assertEqual(judge_scores(5.0, 1.0), "Cross")
        self.assertEqual(judge_scores(1.0, 5.0), "X")

    def test_benchmark_mac_returns_non_negative_milliseconds(self) -> None:
        cross = generate_cross_pattern(5)
        average_ms = benchmark_mac(cross, cross, runs=10, use_flatten=False)
        self.assertGreaterEqual(average_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
