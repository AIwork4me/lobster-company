"""测试每周报告生成。"""

import unittest
from datetime import datetime, timezone, timedelta
from pr_queue.report import (
    generate_weekly_report, format_weekly_report, WeeklyStats,
    _get_week_range,
)
from pr_queue.models import PullRequest, Review, Config


def _make_pr(number=1, days_ago=3, reviews=None, changed_files=None, **kwargs):
    created = datetime.now(timezone.utc) - timedelta(days=days_ago)
    review_time = created + timedelta(hours=12)
    return PullRequest(
        number=number, title=f"PR {number}", author="alice",
        repo="test/repo", state="open",
        created_at=created.isoformat(),
        updated_at=created.isoformat(),
        reviews=reviews or [],
        changed_files=changed_files or ["src/main.py"],
        added_lines=kwargs.pop("added_lines", 0),
        deleted_lines=kwargs.pop("deleted_lines", 0),
        **kwargs,
    )


class TestGetWeekRange(unittest.TestCase):
    """周范围计算测试。"""

    def test_returns_monday_and_sunday(self):
        # 用一个已知的周一
        monday = datetime(2026, 3, 16, 0, 0, 0, tzinfo=timezone.utc)
        start, end = _get_week_range(monday)
        self.assertEqual(start.weekday(), 0)  # Monday
        self.assertEqual(end.weekday(), 6)    # Sunday


class TestGenerateWeeklyReport(unittest.TestCase):
    """每周报告生成测试。"""

    def test_empty_prs(self):
        config = Config()
        stats = generate_weekly_report([], config)
        self.assertEqual(stats.total_prs, 0)
        self.assertEqual(stats.avg_review_hours, 0)

    def test_total_prs_count(self):
        prs = [_make_pr(number=i, days_ago=i) for i in range(1, 6)]
        config = Config()
        start = datetime.now(timezone.utc) - timedelta(days=10)
        end = datetime.now(timezone.utc)
        stats = generate_weekly_report(prs, config, week_start=start, week_end=end)
        self.assertEqual(stats.total_prs, 5)

    def test_reviewed_prs(self):
        prs = [
            _make_pr(number=1, days_ago=1, reviews=[
                Review("bob", "approved", "LGTM", ""),
            ]),
            _make_pr(number=2, days_ago=2, reviews=[]),
        ]
        config = Config()
        start = datetime.now(timezone.utc) - timedelta(days=10)
        end = datetime.now(timezone.utc)
        stats = generate_weekly_report(prs, config, week_start=start, week_end=end)
        self.assertEqual(stats.reviewed_prs, 1)

    def test_superficial_count(self):
        prs = [_make_pr(number=1, days_ago=1, reviews=[
            Review("bob", "approved", "LGTM", ""),
            Review("charlie", "approved", "👍", ""),
        ])]
        config = Config()
        start = datetime.now(timezone.utc) - timedelta(days=10)
        end = datetime.now(timezone.utc)
        stats = generate_weekly_report(prs, config, week_start=start, week_end=end)
        self.assertEqual(stats.superficial_count, 2)

    def test_most_active_reviewer(self):
        prs = [_make_pr(number=1, days_ago=1, reviews=[
            Review("bob", "approved", "LGTM", ""),
            Review("bob", "approved", "OK", ""),
            Review("alice", "approved", "Good", ""),
        ])]
        config = Config()
        start = datetime.now(timezone.utc) - timedelta(days=10)
        end = datetime.now(timezone.utc)
        stats = generate_weekly_report(prs, config, week_start=start, week_end=end)
        self.assertEqual(stats.most_active_reviewer, "bob")

    def test_most_active_with_no_reviews(self):
        stats = generate_weekly_report([], Config())
        self.assertEqual(stats.most_active_reviewer, "无")

    def test_high_risk_count(self):
        prs = [_make_pr(number=1, days_ago=1, changed_files=["src/payment/a.py"])]
        config = Config()
        start = datetime.now(timezone.utc) - timedelta(days=10)
        end = datetime.now(timezone.utc)
        stats = generate_weekly_report(prs, config, week_start=start, week_end=end)
        self.assertEqual(stats.high_risk_count, 1)

    def test_code_line_totals(self):
        prs = [
            _make_pr(number=1, days_ago=1, added_lines=100, deleted_lines=50),
            _make_pr(number=2, days_ago=2, added_lines=200, deleted_lines=30),
        ]
        config = Config()
        start = datetime.now(timezone.utc) - timedelta(days=10)
        end = datetime.now(timezone.utc)
        stats = generate_weekly_report(prs, config, week_start=start, week_end=end)
        self.assertEqual(stats.total_added_lines, 300)
        self.assertEqual(stats.total_deleted_lines, 80)

    def test_custom_week_range(self):
        start = datetime(2026, 3, 16, tzinfo=timezone.utc)
        end = datetime(2026, 3, 22, tzinfo=timezone.utc)
        pr = _make_pr(days_ago=3)
        config = Config()
        stats = generate_weekly_report([pr], config, week_start=start, week_end=end)
        self.assertGreaterEqual(stats.total_prs, 0)

    def test_prs_outside_range_excluded(self):
        """超出时间范围的 PR 不计入统计。"""
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 7, tzinfo=timezone.utc)
        # 最近 3 天创建的 PR 不在 1 月范围
        pr = _make_pr(days_ago=3)
        config = Config()
        stats = generate_weekly_report([pr], config, week_start=start, week_end=end)
        self.assertEqual(stats.total_prs, 0)

    def test_stats_fields_all_present(self):
        stats = generate_weekly_report([], Config())
        self.assertTrue(hasattr(stats, "total_prs"))
        self.assertTrue(hasattr(stats, "avg_review_hours"))
        self.assertTrue(hasattr(stats, "timeout_count"))
        self.assertTrue(hasattr(stats, "superficial_count"))
        self.assertTrue(hasattr(stats, "most_active_reviewer"))


class TestFormatWeeklyReport(unittest.TestCase):
    """报告格式化测试。"""

    def test_report_contains_key_info(self):
        stats = WeeklyStats(
            total_prs=10, reviewed_prs=8, avg_review_hours=12.5,
            timeout_count=2, superficial_count=3, high_risk_count=1,
            needs_rereview_count=1, total_added_lines=500,
            total_deleted_lines=200, most_active_reviewer="alice",
            start_date="2026-03-16", end_date="2026-03-22",
        )
        msg = format_weekly_report(stats)
        self.assertIn("10", msg)
        self.assertIn("alice", msg)
        self.assertIn("2026-03-16", msg)
        self.assertIn("2026-03-22", msg)
        self.assertIn("12.5", msg)


if __name__ == "__main__":
    unittest.main()
