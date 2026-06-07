"""budget_app 단위 테스트(표준 라이브러리 unittest 만 사용).

실행: python -m unittest discover -s tests
외부 의존성이 없으므로 평가 환경에서 바로 재현할 수 있다.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from budget_app import cli, storage
from budget_app.errors import (
    CategoryInUseError,
    NotFoundError,
    ValidationError,
)
from budget_app.models import Transaction
from budget_app.services import BudgetService, SearchFilter


class StorageTest(unittest.TestCase):
    """저수준 스트리밍/원자적 쓰기 검증."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "data.jsonl"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_reverse_stream_yields_newest_first(self) -> None:
        for i in range(1, 6):
            storage.append_line(self.path, f"line{i}")
        self.assertEqual(
            list(storage.iter_lines_reverse(self.path)),
            ["line5", "line4", "line3", "line2", "line1"],
        )

    def test_reverse_stream_crosses_block_boundary(self) -> None:
        for i in range(200):
            storage.append_line(self.path, f"row-{i:04d}")
        reversed_lines = list(storage.iter_lines_reverse(self.path, block_size=16))
        self.assertEqual(len(reversed_lines), 200)
        self.assertEqual(reversed_lines[0], "row-0199")
        self.assertEqual(reversed_lines[-1], "row-0000")

    def test_reverse_stream_missing_file_is_empty(self) -> None:
        self.assertEqual(list(storage.iter_lines_reverse(self.path)), [])

    def test_atomic_write_replaces_content(self) -> None:
        storage.append_line(self.path, "old")
        storage.atomic_write_lines(self.path, ["a", "b"])
        self.assertEqual(list(storage.iter_lines_forward(self.path)), ["a", "b"])


class ModelTest(unittest.TestCase):
    def test_transaction_roundtrip(self) -> None:
        tx = Transaction("TX-1", "expense", "2024-01-01", 100, "food", "memo", ["t"])
        self.assertEqual(Transaction.from_dict(tx.to_dict()), tx)


class ServiceTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.service = BudgetService(Path(self._tmp.name))
        self.service.bootstrap()  # 기본 카테고리 생성

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _add(self, **kwargs) -> Transaction:
        defaults = dict(date="2024-01-10", type="expense", category="food", amount=1000)
        defaults.update(kwargs)
        return self.service.create_transaction(**defaults)


class ValidationTest(ServiceTestBase):
    def test_bad_date_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self._add(date="2024-13-40")

    def test_non_positive_amount_rejected(self) -> None:
        for bad in (0, -5):
            with self.assertRaises(ValidationError):
                self._add(amount=bad)

    def test_invalid_type_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self._add(type="spend")

    def test_unknown_category_rejected(self) -> None:
        with self.assertRaises(NotFoundError):
            self._add(category="nope")


class CrudTest(ServiceTestBase):
    def test_ids_are_sequential(self) -> None:
        t1 = self._add()
        t2 = self._add()
        self.assertEqual((t1.id, t2.id), ("TX-000001", "TX-000002"))

    def test_list_limit_and_recent_order(self) -> None:
        for day in range(1, 6):
            self._add(date=f"2024-01-0{day}", amount=day * 100)
        rows = self.service.list_transactions(limit=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].id, "TX-000005")  # 가장 최근 입력 먼저

    def test_update_changes_only_given_fields(self) -> None:
        tx = self._add(memo="orig")
        updated = self.service.update_transaction(tx.id, amount=2000)
        self.assertEqual(updated.amount, 2000)
        self.assertEqual(updated.memo, "orig")

    def test_update_missing_id_raises(self) -> None:
        with self.assertRaises(NotFoundError):
            self.service.update_transaction("TX-999", amount=1)

    def test_delete_missing_id_raises(self) -> None:
        with self.assertRaises(NotFoundError):
            self.service.delete_transaction("TX-999")

    def test_delete_removes_record(self) -> None:
        tx = self._add()
        self.service.delete_transaction(tx.id)
        self.assertEqual(self.service.list_transactions(limit=10), [])


class SearchTest(ServiceTestBase):
    def setUp(self) -> None:
        super().setUp()
        self._add(date="2024-01-05", type="income", category="salary", amount=300, memo="pay")
        self._add(date="2024-02-10", type="expense", category="food", amount=50, tags=["meal"])
        self._add(date="2024-03-15", type="expense", category="transport", amount=20, memo="bus")

    def test_filter_by_type(self) -> None:
        rows = self.service.search(SearchFilter(type="expense"))
        self.assertEqual({r.category for r in rows}, {"food", "transport"})

    def test_filter_by_date_range(self) -> None:
        rows = self.service.search(SearchFilter(date_from="2024-02-01", date_to="2024-02-28"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].category, "food")

    def test_filter_by_tag_and_query(self) -> None:
        self.assertEqual(len(self.service.search(SearchFilter(tag="meal"))), 1)
        self.assertEqual(len(self.service.search(SearchFilter(query="bus"))), 1)


class SummaryBudgetTest(ServiceTestBase):
    def test_summary_totals_and_top(self) -> None:
        self._add(date="2024-01-01", type="income", category="salary", amount=1000)
        self._add(date="2024-01-02", type="expense", category="food", amount=300)
        self._add(date="2024-01-03", type="expense", category="rent", amount=500)
        result = self.service.summarize("2024-01", top=1)
        self.assertEqual(result.total_income, 1000)
        self.assertEqual(result.total_expense, 800)
        self.assertEqual(result.balance, 200)
        self.assertEqual(result.top_expenses, [("rent", 500)])

    def test_summary_no_data(self) -> None:
        self.assertFalse(self.service.summarize("2099-01", top=3).has_data)

    def test_budget_usage_and_over(self) -> None:
        self._add(date="2024-01-02", type="expense", category="food", amount=600)
        self.service.set_budget("2024-01", 500)
        result = self.service.summarize("2024-01", top=3)
        self.assertEqual(result.budget, 500)
        self.assertEqual(result.usage_rate, 120.0)
        self.assertTrue(result.over_budget)


class CategoryTest(ServiceTestBase):
    def test_add_and_duplicate(self) -> None:
        self.assertTrue(self.service.add_category("cafe"))
        self.assertFalse(self.service.add_category("cafe"))

    def test_remove_in_use_blocked(self) -> None:
        self._add(category="food")
        with self.assertRaises(CategoryInUseError):
            self.service.remove_category("food")

    def test_remove_in_use_with_into_migrates(self) -> None:
        self._add(category="food")
        self.service.add_category("cafe")
        moved = self.service.remove_category("food", into="cafe")
        self.assertEqual(moved, 1)
        self.assertNotIn("food", self.service.list_categories())
        self.assertEqual(self.service.list_transactions(limit=1)[0].category, "cafe")


class ImportExportTest(ServiceTestBase):
    def test_export_then_import_roundtrip(self) -> None:
        self._add(date="2024-01-10", category="food", amount=100, memo="a", tags=["x", "y"])
        out = Path(self._tmp.name) / "out.csv"
        count = self.service.export_csv(out, SearchFilter(month="2024-01"))
        self.assertEqual(count, 1)
        imported, skipped, _ = self.service.import_csv(out)
        self.assertEqual((imported, skipped), (1, 0))
        rows = self.service.list_transactions(limit=10)
        self.assertEqual(rows[0].tags, ["x", "y"])

    def test_import_skips_unknown_category(self) -> None:
        csv_path = Path(self._tmp.name) / "in.csv"
        csv_path.write_text(
            "date,type,category,amount,memo,tags\n"
            "2024-01-01,expense,food,100,ok,\n"
            "2024-01-02,expense,ghost,200,bad,\n",
            encoding="utf-8",
        )
        imported, skipped, reasons = self.service.import_csv(csv_path)
        self.assertEqual((imported, skipped), (1, 1))
        self.assertEqual(len(reasons), 1)


class BackupRecurringTest(ServiceTestBase):
    def test_backup_copies_files(self) -> None:
        self._add()
        backup_dir = self.service.backup("20240101-000000")
        self.assertTrue((backup_dir / "transactions.jsonl").exists())

    def test_recurring_apply_is_idempotent(self) -> None:
        self.service.add_recurring(type="expense", day=25, category="rent", amount=500)
        self.assertEqual(self.service.apply_recurring("2024-03"), (1, 0))
        self.assertEqual(self.service.apply_recurring("2024-03"), (0, 1))


class CliTest(unittest.TestCase):
    """CLI 진입점의 종료 코드와 출력 스모크 테스트."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_list_returns_zero(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli.main(["list", "--data-dir", self.data_dir])
        self.assertEqual(code, 0)

    def test_delete_missing_returns_nonzero(self) -> None:
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            code = cli.main(["delete", "--id", "TX-404", "--data-dir", self.data_dir])
        self.assertNotEqual(code, 0)
        self.assertIn("[오류]", err.getvalue())

    def test_add_then_summary_via_cli(self) -> None:
        answers = iter(["2024-06-01", "expense", "food", "7000", "lunch", ""])
        with mock.patch("builtins.input", lambda *_: next(answers)), redirect_stdout(io.StringIO()):
            code = cli.main(["add", "--data-dir", self.data_dir])
        self.assertEqual(code, 0)
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli.main(["summary", "--month", "2024-06", "--data-dir", self.data_dir])
        self.assertEqual(code, 0)
        self.assertIn("총 지출: 7,000원", out.getvalue())


if __name__ == "__main__":
    unittest.main()
