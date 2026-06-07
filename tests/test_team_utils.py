"""Git 협업 유틸 함수의 기대 동작을 검증한다."""

from pathlib import Path
import tempfile
import unittest

from src.team_utils import (
    branch_name,
    commit_message_status,
    conflict_marker_report,
    pr_body_status,
)


class TeamUtilsTest(unittest.TestCase):
    """팀 협업 규칙을 코드로 확인하는 테스트 모음."""

    def test_branch_name_normalizes_member_and_topic(self):
        """팀원 이름과 작업 주제를 feature 브랜치 규칙에 맞게 정규화한다."""
        self.assertEqual(
            branch_name("Kim Min Seo", "Add Math Utils!"),
            "feature/kim-min-seo-add-math-utils",
        )

    def test_commit_message_status_rejects_vague_messages(self):
        """금지어만 있는 커밋 메시지와 대상이 없는 메시지를 거부한다."""
        self.assertFalse(commit_message_status("update").valid)
        self.assertFalse(commit_message_status("fix: bug fix").valid)
        self.assertTrue(commit_message_status("docs: add conflict runbook").valid)

    def test_pr_body_status_requires_issue_what_why_and_how(self):
        """PR 본문에는 이슈 연결, 변경 사항, 변경 이유, 검증 방법이 있어야 한다."""
        good_body = """
        Closes #12
        ## 변경 사항(What)
        - 브랜치 규칙을 추가했다.
        ## 변경 이유(Why)
        - 리뷰 기준을 맞추기 위해서다.
        ## 테스트/검증(How)
        - python -m unittest discover -s tests
        """
        bad_body = "LGTM"

        self.assertEqual(pr_body_status(good_body).missing, [])
        self.assertIn("연결 이슈", pr_body_status(bad_body).missing)
        self.assertIn("검증 방법", pr_body_status(bad_body).missing)

    def test_conflict_marker_report_counts_files_and_lines(self):
        """충돌 마커가 있는 파일 경로와 라인 번호를 보고한다."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            conflicted = root / "README.md"
            conflicted.write_text(
                "before\n<<<<<<< HEAD\nmain\n=======\nfeature\n>>>>>>> feature/x\n",
                encoding="utf-8",
            )
            clean = root / "src.py"
            clean.write_text("print('clean')\n", encoding="utf-8")

            report = conflict_marker_report(root)

        self.assertEqual(report.total_markers, 3)
        self.assertEqual(report.files[0].path, "README.md")
        self.assertEqual(report.files[0].lines, [2, 4, 6])


if __name__ == "__main__":
    unittest.main()
