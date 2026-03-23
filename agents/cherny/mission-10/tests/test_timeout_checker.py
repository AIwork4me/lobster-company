"""测试 PR 超时检测。"""

import unittest
from datetime import datetime, timezone, timedelta
from pr_queue.timeout_checker import (
    parse_iso_time, get_wait_hours, is_timeout,
    get_timeout_prs, format_timeout_message,
)
from pr_queue.models import PullRequest, Config


def _make_pr(hours_ago=0, **kwargs):
    created = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    defaults = {
        "number": 1, "title": "Test PR", "author": "alice",
        "repo": "test/repo", "state": "open",
        "created_at": created.isoformat(),
        "updated_at": created.isoformat(),
        "changed_files": ["src/main.py"],
    }
    defaults.update(kwargs)
    return PullRequest(**defaults)


class TestParseIsoTime(unittest.TestCase):
    """ISO 8601 时间解析测试。"""

    def test_z_suffix(self):
        t = parse_iso_time("2026-03-22T10:00:00Z")
        self.assertEqual(t.year, 2026)
        self.assertEqual(t.month, 3)

    def test_with_timezone(self):
        t = parse_iso_time("2026-03-22T10:00:00+08:00")
        self.assertIsNotNone(t)

    def test_without_timezone(self):
        t = parse_iso_time("2026-03-22T10:00:00")
        self.assertIsNotNone(t)


class TestGetWaitHours(unittest.TestCase):
    """等待时长计算测试。"""

    def test_just_created(self):
        pr = _make_pr(hours_ago=0)
        hours = get_wait_hours(pr)
        self.assertLess(hours, 0.1)

    def test_24_hours_ago(self):
        pr = _make_pr(hours_ago=24)
        hours = get_wait_hours(pr)
        self.assertAlmostEqual(hours, 24, delta=0.1)

    def test_with_custom_now(self):
        pr = PullRequest(
            number=1, title="T", author="a", repo="r", state="open",
            created_at="2026-03-20T10:00:00Z",
            updated_at="2026-03-20T10:00:00Z",
        )
        now = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
        hours = get_wait_hours(pr, now)
        self.assertAlmostEqual(hours, 48, delta=0.1)


class TestIsTimeout(unittest.TestCase):
    """超时判断测试。"""

    def test_not_timeout(self):
        pr = _make_pr(hours_ago=12)
        config = Config(timeout_hours=24)
        self.assertFalse(is_timeout(pr, config))

    def test_exactly_timeout(self):
        pr = _make_pr(hours_ago=24)
        config = Config(timeout_hours=24)
        self.assertTrue(is_timeout(pr, config))

    def test_over_timeout(self):
        pr = _make_pr(hours_ago=48)
        config = Config(timeout_hours=24)
        self.assertTrue(is_timeout(pr, config))

    def test_closed_pr_never_timeout(self):
        pr = _make_pr(hours_ago=100, state="closed")
        config = Config(timeout_hours=24)
        self.assertFalse(is_timeout(pr, config))

    def test_custom_timeout_threshold(self):
        pr = _make_pr(hours_ago=12)
        config = Config(timeout_hours=10)
        self.assertTrue(is_timeout(pr, config))


class TestGetTimeoutPrs(unittest.TestCase):
    """批量超时检测测试。"""

    def test_filters_only_timeout_prs(self):
        prs = [
            _make_pr(number=1, hours_ago=12),
            _make_pr(number=2, hours_ago=30),
            _make_pr(number=3, hours_ago=50),
            _make_pr(number=4, hours_ago=5),
        ]
        config = Config(timeout_hours=24)
        result = get_timeout_prs(prs, config)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0].number, 3)  # 最长的排前面

    def test_empty_list(self):
        config = Config(timeout_hours=24)
        result = get_timeout_prs([], config)
        self.assertEqual(len(result), 0)

    def test_sorted_by_wait_time(self):
        prs = [
            _make_pr(number=1, hours_ago=30),
            _make_pr(number=2, hours_ago=48),
        ]
        config = Config(timeout_hours=24)
        result = get_timeout_prs(prs, config)
        self.assertGreater(result[0][1], result[1][1])


class TestFormatTimeoutMessage(unittest.TestCase):
    """超时消息格式化测试。"""

    def test_basic_message(self):
        pr = _make_pr(
            hours_ago=25,
            changed_files=["src/payment/checkout.py", "src/payment/refund.py"],
        )
        msg = format_timeout_message(pr, 25.5)
        self.assertIn("PR #1", msg)
        self.assertIn("25.5", msg)
        self.assertIn("checkout.py", msg)

    def test_truncates_long_file_list(self):
        files = [f"src/file{i}.py" for i in range(10)]
        pr = _make_pr(hours_ago=25, changed_files=files)
        msg = format_timeout_message(pr, 25.0)
        self.assertIn("10 个文件", msg)


if __name__ == "__main__":
    unittest.main()
