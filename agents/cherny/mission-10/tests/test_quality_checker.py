"""测试审查质量检测。"""

import unittest
from pr_queue.quality_checker import (
    is_superficial_review, find_high_risk_dirs, is_large_change,
    check_review_quality, check_all_reviews, format_quality_alert,
    QualityResult,
)
from pr_queue.models import PullRequest, Review, Config


def _make_pr(**kwargs):
    defaults = {
        "number": 1, "title": "Test PR", "author": "alice",
        "repo": "test/repo", "state": "open",
        "created_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-22T10:00:00Z",
    }
    defaults.update(kwargs)
    return PullRequest(**defaults)


class TestIsSuperficialReview(unittest.TestCase):
    """走过场式 Review 检测测试。"""

    def test_lgtm_is_superficial(self):
        r = Review("bob", "approved", "LGTM", "2026-03-21T10:00:00Z")
        self.assertTrue(is_superficial_review(r, Config()))

    def test_lgtm_lowercase(self):
        r = Review("bob", "approved", "lgtm", "2026-03-21T10:00:00Z")
        self.assertTrue(is_superficial_review(r, Config()))

    def test_chinese_superficial(self):
        r = Review("bob", "approved", "看起来没问题", "2026-03-21T10:00:00Z")
        self.assertTrue(is_superficial_review(r, Config()))

    def test_emoji_superficial(self):
        r = Review("bob", "approved", "👍", "2026-03-21T10:00:00Z")
        self.assertTrue(is_superficial_review(r, Config()))

    def test_empty_approved_is_superficial(self):
        r = Review("bob", "approved", "", "2026-03-21T10:00:00Z")
        self.assertTrue(is_superficial_review(r, Config()))

    def test_changes_requested_not_superficial(self):
        r = Review("bob", "changes_requested", "这里有问题", "2026-03-21T10:00:00Z")
        self.assertFalse(is_superficial_review(r, Config()))

    def test_commented_not_superficial(self):
        r = Review("bob", "commented", "建议重构这部分", "2026-03-21T10:00:00Z")
        self.assertFalse(is_superficial_review(r, Config()))

    def test_detailed_approved_not_superficial(self):
        r = Review("bob", "approved", "逻辑没问题，但第 42 行的变量名建议改一下", "2026-03-21T10:00:00Z")
        self.assertFalse(is_superficial_review(r, Config()))

    def test_contains_lgtm_in_detailed_review(self):
        """即使包含 LGTM 关键词，长评论也不应判定为走过场。"""
        r = Review("bob", "approved", "LGTM! 整体代码质量很好，测试覆盖也很全面。唯一建议是第 15 行的错误处理可以更细化。", "2026-03-21T10:00:00Z")
        # 按当前逻辑，只要包含关键词就算走过场——这是 PRD 的行为
        self.assertTrue(is_superficial_review(r, Config()))


class TestFindHighRiskDirs(unittest.TestCase):
    """高风险目录检测测试。"""

    def test_payment_dir_detected(self):
        pr = _make_pr(changed_files=["src/payment/checkout.py"])
        result = find_high_risk_dirs(pr, Config())
        self.assertIn("payment", result)

    def test_multiple_risk_dirs(self):
        pr = _make_pr(changed_files=["src/payment/checkout.py", "db/migration/001.sql"])
        result = find_high_risk_dirs(pr, Config())
        self.assertIn("payment", result)
        self.assertIn("migration", result)

    def test_no_risk_dirs(self):
        pr = _make_pr(changed_files=["src/utils/helper.py"])
        result = find_high_risk_dirs(pr, Config())
        self.assertEqual(len(result), 0)

    def test_case_insensitive(self):
        pr = _make_pr(changed_files=["src/Payment/checkout.py"])
        result = find_high_risk_dirs(pr, Config())
        self.assertIn("payment", result)

    def test_windows_style_path(self):
        pr = _make_pr(changed_files=["src\\payment\\checkout.py"])
        result = find_high_risk_dirs(pr, Config())
        self.assertIn("payment", result)


class TestIsLargeChange(unittest.TestCase):
    """大变更检测测试。"""

    def test_large_change_detected(self):
        pr = _make_pr(added_lines=150, deleted_lines=100)
        self.assertTrue(is_large_change(pr, Config(large_change_threshold=200)))

    def test_small_change_not_large(self):
        pr = _make_pr(added_lines=50, deleted_lines=30)
        self.assertFalse(is_large_change(pr, Config()))

    def test_exactly_at_threshold(self):
        pr = _make_pr(added_lines=200, deleted_lines=0)
        self.assertFalse(is_large_change(pr, Config(large_change_threshold=200)))


class TestCheckReviewQuality(unittest.TestCase):
    """综合审查质量检测测试。"""

    def test_normal_review(self):
        pr = _make_pr(
            changed_files=["src/utils/helper.py"],
            reviews=[Review("bob", "approved", "代码逻辑清晰，通过", "2026-03-21T10:00:00Z")],
        )
        result = check_review_quality(pr, Config())
        self.assertFalse(result.needs_rereview)
        self.assertFalse(result.is_superficial)
        self.assertEqual(result.reason, "审查正常")

    def test_superficial_plus_high_risk(self):
        pr = _make_pr(
            changed_files=["src/payment/checkout.py"],
            reviews=[Review("bob", "approved", "LGTM", "2026-03-21T10:00:00Z")],
        )
        result = check_review_quality(pr, Config())
        self.assertTrue(result.needs_rereview)
        self.assertTrue(result.is_superficial)
        self.assertTrue(result.is_high_risk)
        self.assertIn("走过场式 Approval", result.reason)

    def test_superficial_plus_large_change(self):
        pr = _make_pr(
            changed_files=["src/utils/big.py"],
            added_lines=150, deleted_lines=100,
            reviews=[Review("bob", "approved", "LGTM", "2026-03-21T10:00:00Z")],
        )
        result = check_review_quality(pr, Config())
        self.assertTrue(result.needs_rereview)
        self.assertIn("大规模变更", result.reason)

    def test_high_risk_no_review(self):
        pr = _make_pr(
            changed_files=["src/payment/checkout.py"],
            reviews=[],
        )
        result = check_review_quality(pr, Config())
        self.assertTrue(result.needs_rereview)
        self.assertIn("高风险目录", result.reason)

    def test_closed_pr_no_rereview(self):
        pr = _make_pr(
            state="closed",
            changed_files=["src/payment/checkout.py"],
            reviews=[],
        )
        result = check_review_quality(pr, Config())
        # closed PR 不触发无 Review 的高风险检测
        self.assertFalse(result.needs_rereview)

    def test_detailed_review_no_rereview(self):
        pr = _make_pr(
            changed_files=["src/payment/checkout.py"],
            reviews=[Review("bob", "approved", "代码审查完成，支付逻辑正确", "2026-03-21T10:00:00Z")],
        )
        result = check_review_quality(pr, Config())
        self.assertFalse(result.needs_rereview)

    def test_quality_result_fields(self):
        pr = _make_pr(changed_files=["src/auth/login.py"])
        result = check_review_quality(pr, Config())
        self.assertTrue(hasattr(result, "is_superficial"))
        self.assertTrue(hasattr(result, "is_high_risk"))
        self.assertTrue(hasattr(result, "risk_dirs"))
        self.assertTrue(hasattr(result, "needs_rereview"))
        self.assertTrue(hasattr(result, "reason"))


class TestCheckAllReviews(unittest.TestCase):
    """批量检测测试。"""

    def test_checks_all_prs(self):
        prs = [
            _make_pr(number=1, changed_files=["src/utils/a.py"]),
            _make_pr(number=2, changed_files=["src/payment/b.py"]),
        ]
        results = check_all_reviews(prs, Config())
        self.assertEqual(len(results), 2)


class TestFormatQualityAlert(unittest.TestCase):
    """质量警告消息格式化测试。"""

    def test_alert_contains_pr_info(self):
        pr = _make_pr(
            changed_files=["src/payment/checkout.py"],
            added_lines=100, deleted_lines=50,
            reviews=[Review("bob", "approved", "👍", "2026-03-21T10:00:00Z")],
        )
        result = check_review_quality(pr, Config())
        msg = format_quality_alert(result)
        self.assertIn("PR #1", msg)
        self.assertIn("payment", msg)
        self.assertIn("二次审查", msg)


if __name__ == "__main__":
    unittest.main()
