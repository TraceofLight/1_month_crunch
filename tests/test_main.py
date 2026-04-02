import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from main import Matrix, generate_cross_pattern, generate_x_pattern, normalize_label
from main import EPSILON, benchmark_mac, judge_scores, mac_1d, mac_2d
from main import analyze_data_file, save_default_data


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


class JsonAnalysisTests(unittest.TestCase):
    def test_save_default_data_writes_required_sections(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)
            payload = json.loads(data_path.read_text(encoding="utf-8"))

        self.assertEqual(sorted(payload["filters"].keys()), ["size_13", "size_25", "size_5"])
        self.assertIn("size_5_1", payload["patterns"])
        self.assertIn("size_25_3", payload["patterns"])

    def test_analyze_data_file_returns_summary_and_fail_reasons(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)
            report = analyze_data_file(data_path)

        self.assertEqual(report["summary"]["total"], 8)
        self.assertEqual(report["summary"]["passed"], 6)
        self.assertEqual(report["summary"]["failed"], 2)
        self.assertIn("size_13_3", {item["case_id"] for item in report["results"]})
        self.assertIn("size_25_3", {item["case_id"] for item in report["failures"]})

from main import parse_matrix_row, run_manual_mode


class ConsoleFlowTests(unittest.TestCase):
    def test_parse_matrix_row_validates_column_count_and_numbers(self) -> None:
        self.assertEqual(parse_matrix_row("1 0 1", 3), [1.0, 0.0, 1.0])

        with self.assertRaises(ValueError):
            parse_matrix_row("1 0", 3)

        with self.assertRaises(ValueError):
            parse_matrix_row("1 a 0", 3)

    def test_run_manual_mode_retries_invalid_input_and_returns_decision(self) -> None:
        answers = iter(
            [
                "1 0",
                "0 1 0",
                "1 1 1",
                "0 1 0",
                "1 0 1",
                "0 1 0",
                "1 0 1",
                "1 0 1",
                "0 1 0",
                "1 0 1",
            ]
        )
        output: list[str] = []

        result = run_manual_mode(input_func=lambda _: next(answers), output_func=output.append)

        self.assertEqual(result["decision"], "B")
        self.assertTrue(any("입력 형식 오류" in line for line in output))


if __name__ == "__main__":
    unittest.main()
