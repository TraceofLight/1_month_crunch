import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from main import Matrix, generate_cross_pattern, generate_x_pattern, normalize_label
from main import EPSILON, benchmark_mac, judge_scores, mac_1d, mac_2d
from main import analyze_data_file, main, save_default_data


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

    def test_parse_matrix_row_rejects_non_binary_numbers(self) -> None:
        with self.assertRaises(ValueError):
            parse_matrix_row("1 2 0", 3)

        with self.assertRaises(ValueError):
            parse_matrix_row("-1 0 1", 3)

        with self.assertRaises(ValueError):
            parse_matrix_row("0.5 0 1", 3)

    def test_run_manual_mode_retries_non_binary_row_input(self) -> None:
        answers = iter(
            [
                "1 2 0",
                "0 1 0",
                "1 1 1",
                "0 1 0",
                "1 0 1",
                "0 1 0",
                "1 0 1",
                "1 0 1",
                "0 1 0",
                "1 0 1",
                "0 1 0",
                "1 0 1",
            ]
        )
        output: list[str] = []

        result = run_manual_mode(input_func=lambda _: next(answers), output_func=output.append)

        self.assertEqual(result["decision"], "B")
        self.assertTrue(any("입력 형식 오류" in line for line in output))
        self.assertGreaterEqual(output.count("필터 A (3줄 입력, 공백 구분)"), 2)


from main import append_generated_pattern_case, main, run_json_mode, run_pattern_generator_mode, safe_main


class BonusFeatureTests(unittest.TestCase):
    def test_append_generated_pattern_case_adds_new_case(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)

            case_id = append_generated_pattern_case(data_path, generate_cross_pattern(7), "Cross")
            payload = json.loads(data_path.read_text(encoding="utf-8"))

        self.assertEqual(case_id, "size_7_1")
        self.assertIn("size_7_1", payload["patterns"])
        self.assertEqual(payload["patterns"]["size_7_1"]["expected"], "+")

    def test_run_pattern_generator_mode_retries_invalid_size_and_prints_benchmark(self) -> None:
        answers = iter(["4", "5", "1", "n"])
        output: list[str] = []

        result = run_pattern_generator_mode(input_func=lambda _: next(answers), output_func=output.append)

        self.assertEqual(result["label"], "Cross")
        self.assertEqual(result["size"], 5)
        self.assertIsNone(result["saved_case_id"])
        self.assertTrue(any("홀수" in line for line in output))
        self.assertTrue(any("2D" in line for line in output))
        self.assertTrue(any("1D" in line for line in output))

    def test_analyze_data_file_reports_missing_related_filters_as_readable_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)
            append_generated_pattern_case(data_path, generate_cross_pattern(7), "Cross")

            report = analyze_data_file(data_path)

        reasons = {item["case_id"]: item["reason"] for item in report["failures"]}
        self.assertIn("size_7_1", reasons)
        self.assertIn("관련 필터", reasons["size_7_1"])
        self.assertIn("판정", reasons["size_7_1"])


class EntryPointTests(unittest.TestCase):
    def test_main_dispatches_pattern_generator_mode(self) -> None:
        output: list[str] = []

        with patch("main.run_pattern_generator_mode") as generator_mode:
            main(input_func=lambda _: "3", output_func=output.append)

        generator_mode.assert_called_once()

    def test_safe_main_handles_keyboard_interrupt(self) -> None:
        output: list[str] = []

        safe_main(input_func=lambda _: (_ for _ in ()).throw(KeyboardInterrupt()), output_func=output.append)

        self.assertTrue(any("종료" in line for line in output))

    def test_safe_main_handles_eof_error(self) -> None:
        output: list[str] = []

        safe_main(input_func=lambda _: (_ for _ in ()).throw(EOFError()), output_func=output.append)

        self.assertTrue(any("입력이 종료" in line or "종료" in line for line in output))


class OutputFormatTests(unittest.TestCase):
    def test_main_menu_includes_mode_header_and_generator_option(self) -> None:
        output: list[str] = []

        main(input_func=lambda _: "9", output_func=output.append)

        self.assertEqual(output[0], "=== Mini NPU Simulator ===")
        self.assertIn("[모드 선택]", output)
        self.assertIn("1. 사용자 입력 (3x3)", output)
        self.assertIn("2. data.json 분석", output)
        self.assertIn("3. 패턴 생성기 (보너스)", output)

    def test_run_manual_mode_prints_section_headers(self) -> None:
        answers = iter(
            [
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

        run_manual_mode(input_func=lambda _: next(answers), output_func=output.append)

        self.assertIn("# [1] 필터 입력", output)
        self.assertIn("# [2] 패턴 입력", output)
        self.assertIn("# [3] MAC 결과", output)
        self.assertTrue(any(line.startswith("A 점수:") for line in output))
        self.assertTrue(any(line.startswith("B 점수:") for line in output))
        self.assertTrue(any(line.startswith("판정:") for line in output))

    def test_run_json_mode_prints_sectioned_sample_like_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)
            output: list[str] = []

            run_json_mode(data_path=data_path, output_func=output.append)

        self.assertIn("# [1] 필터 로드", output)
        self.assertIn("# [2] 패턴 분석 (라벨 정규화 적용)", output)
        self.assertIn("# [3] 성능 분석 (평균/10회)", output)
        self.assertIn("# [4] 결과 요약", output)
        self.assertIn("--- size_5_1 ---", output)
        self.assertTrue(any(line.startswith("Cross 점수:") for line in output))
        self.assertTrue(any(line.startswith("X 점수:") for line in output))
        self.assertTrue(any(line.startswith("판정:") for line in output))


if __name__ == "__main__":
    unittest.main()
