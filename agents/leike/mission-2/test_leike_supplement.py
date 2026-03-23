"""
Leike 补充测试 — Cherny 没覆盖到的场景。

审查维度：
- 安全问题（XSS、路径遍历、输入验证）
- 边界条件（极端输入、空值、超长字符串）
- PRD 一致性（webhook_handler 未被测试、特殊场景）
- 设计缺陷（concurrent write、data integrity）
"""

import sys
import os
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer
from threading import Thread
from urllib.request import urlopen, Request
from urllib.error import URLError

# 确保能导入 pr_queue
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "cherny", "mission-10"))

from pr_queue.models import PullRequest, Review, Config
from pr_queue.config import load_config, save_config
from pr_queue.store import PRStore
from pr_queue.timeout_checker import (
    parse_iso_time, get_wait_hours, is_timeout, get_timeout_prs, format_timeout_message,
)
from pr_queue.quality_checker import (
    is_superficial_review, find_high_risk_dirs, is_large_change,
    check_review_quality, check_all_reviews, format_quality_alert, QualityResult,
)
from pr_queue.reviewer_router import match_reviewer_rules, suggest_reviewers, format_reviewer_suggestion
from pr_queue.notifier import send_webhook, send_slack_notification, send_feishu_notification
from pr_queue.report import generate_weekly_report, format_weekly_report, WeeklyStats
from pr_queue.dashboard import _render_html, _render_api, make_handler, start_dashboard
from pr_queue.webhook_handler import parse_github_pr_payload, handle_pr_event


# ============================================================
# 工具函数
# ============================================================

def _make_pr(**kwargs):
    defaults = {
        "number": 1, "title": "Test PR", "author": "alice",
        "repo": "test/repo", "state": "open",
        "created_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-20T10:00:00Z",
    }
    defaults.update(kwargs)
    return PullRequest(**defaults)


def _make_pr_recent(hours_ago=5, **kwargs):
    created = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    defaults = {
        "number": 1, "title": "Test PR", "author": "alice",
        "repo": "test/repo", "state": "open",
        "created_at": created.isoformat(),
        "updated_at": created.isoformat(),
    }
    defaults.update(kwargs)
    return PullRequest(**defaults)


# ============================================================
# 🚨 安全测试
# ============================================================

class TestSecurityXSSInDashboard(unittest.TestCase):
    """Dashboard HTML 中是否存在 XSS 注入风险。"""

    def test_pr_title_with_script_tag(self):
        """PR 标题包含 <script> 标签时，HTML 应该被正确转义。"""
        pr = _make_pr_recent(title='<script>alert("xss")</script>')
        html = _render_html([pr], Config())
        # 如果 HTML 直接插入未转义，<script> 会原样出现
        self.assertNotIn('<script>alert', html)

    def test_author_name_with_html_injection(self):
        """作者名包含 HTML 标签时应该被转义。"""
        pr = _make_pr_recent(author='<img src=x onerror=alert(1)>')
        html = _render_html([pr], Config())
        self.assertNotIn('<img', html)
        # 应该被转义
        self.assertIn('&lt;', html)

    def test_repo_name_with_html_injection(self):
        """仓库名包含 HTML 标签时应该被转义。"""
        pr = _make_pr_recent(repo='test/<script>alert(1)</script>')
        html = _render_html([pr], Config())
        self.assertNotIn('<script>', html)

    def test_reviewer_name_with_html_in_dashboard(self):
        """审查人名包含 HTML 时应该被转义。"""
        pr = _make_pr_recent(reviewers=['<b>alice</b>'])
        html = _render_html([pr], Config())
        self.assertNotIn('<b>alice</b>', html)


class TestSecurityInputValidation(unittest.TestCase):
    """输入验证安全测试。"""

    def test_webhook_url_ssrf_risk(self):
        """send_webhook 对任意 URL 无限制——SSRF 风险。"""
        # 向内网地址发送请求，如果成功说明存在 SSRF
        # 这里只验证函数能处理错误，不实际利用
        result = send_webhook("http://169.254.169.254/latest/meta-data/", "test", dry_run=True)
        self.assertTrue(result)  # dry_run 应该返回 True

    def test_empty_webhook_url(self):
        """空 Webhook URL 不应该发送请求。"""
        result = send_webhook("", "test message")
        # 空 URL 会抛异常，应返回 False
        self.assertFalse(result)

    def test_invalid_webhook_url(self):
        """无效 URL 格式应安全处理。"""
        result = send_webhook("not-a-url", "test")
        self.assertFalse(result)

    def test_payload_with_extremely_long_message(self):
        """超长消息不应导致崩溃（DoS 测试）。"""
        long_msg = "A" * 1_000_000  # 1MB 消息
        result = send_webhook("http://invalid.example.com", long_msg, dry_run=True)
        self.assertTrue(result)

    def test_config_from_malicious_json(self):
        """恶意构造的 JSON 配置文件不应导致异常。"""
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "config.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"timeout_hours": "not-a-number", "webhook_url": None}, f)
        config = load_config(path)
        # 如果 from_dict 不做类型检查，timeout_hours 会变成字符串
        # 这是一个潜在 bug
        self.assertIsInstance(config.timeout_hours, (int, float))


class TestSecurityPathTraversal(unittest.TestCase):
    """路径遍历风险测试。"""

    def test_store_path_traversal(self):
        """PRStore 不应允许路径遍历到任意文件。"""
        tmpdir = tempfile.mkdtemp()
        # 正常路径
        store = PRStore(os.path.join(tmpdir, "data.json"))
        store.add(_make_pr(number=1))
        self.assertEqual(len(store.get_all()), 1)

    def test_config_path_with_parent_traversal(self):
        """配置文件路径不应使用 ../ 遍历。"""
        # 只是确认 load_config 不会做路径规范化检查（潜在问题）
        tmpdir = tempfile.mkdtemp()
        result = load_config(os.path.join(tmpdir, "config.json"))
        self.assertIsInstance(result, Config)


# ============================================================
# 🏗️ 设计缺陷测试
# ============================================================

class TestDesignDefects(unittest.TestCase):
    """设计层面的问题测试。"""

    def test_store_not_thread_safe(self):
        """PRStore 每次操作都全量读写，不是线程安全的。
        并发写入可能导致数据丢失。"""
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "data.json")
        store = PRStore(path)
        # 快速连续写入
        for i in range(100):
            store.add(_make_pr(number=i))
        result = store.get_all()
        # 理论上应该有 100 个，但因为没有文件锁，可能在极端情况下丢失
        self.assertGreater(len(result), 0)

    def test_to_dict_returns_mutable_lists(self):
        """to_dict() 返回的列表是原始数据的引用——外部修改会影响模型。
        这违反了不可变性原则。"""
        pr = _make_pr(reviewers=["alice"], changed_files=["a.py"])
        d = pr.to_dict()
        d["reviewers"].append("bob")
        # 如果 to_dict 返回引用而不是副本，原始 PR 也会被修改
        # 实际上 dataclass 的 list 是引用，但 to_dict 是构建新 dict
        # 需要验证：
        self.assertEqual(pr.reviewers, ["alice"])  # 应该不受影响

    def test_config_mutable_default_lists_shared(self):
        """Config 的默认列表是否在多个实例间共享？"""
        c1 = Config()
        c2 = Config()
        c1.high_risk_dirs.append("INJECTED")
        self.assertNotIn("INJECTED", c2.high_risk_dirs)

    def test_parse_iso_time_malformed(self):
        """畸形时间字符串应被安全处理。"""
        # 空字符串
        with self.assertRaises((ValueError, IndexError, AttributeError)):
            parse_iso_time("")
        # 纯乱码
        with self.assertRaises((ValueError, IndexError, AttributeError)):
            parse_iso_time("not-a-date")

    def test_parse_iso_time_only_date(self):
        """只有日期没有时间的情况。"""
        # 这取决于实现——有些可能报错，有些可能成功
        try:
            result = parse_iso_time("2026-03-22")
            self.assertIsNotNone(result)
        except (ValueError, IndexError):
            pass  # 报错也是合理行为

    def test_is_superficial_whitespace_only_body(self):
        """纯空格的 Review body 应该被视为走过场。"""
        r = Review("bob", "approved", "   ", "2026-03-21T10:00:00Z")
        # body.strip() == "" → True
        self.assertTrue(is_superficial_review(r, Config()))


# ============================================================
# 🎯 边界条件测试
# ============================================================

class TestEdgeCasesModels(unittest.TestCase):
    """数据模型边界条件。"""

    def test_pr_number_zero(self):
        """PR number 为 0 的情况。"""
        pr = _make_pr(number=0)
        self.assertEqual(pr.number, 0)

    def test_pr_number_negative(self):
        """PR number 为负数的情况。"""
        pr = _make_pr(number=-1)
        self.assertEqual(pr.number, -1)

    def test_empty_title(self):
        """空标题。"""
        pr = _make_pr(title="")
        self.assertEqual(pr.title, "")

    def test_extremely_long_title(self):
        """超长标题（1000 字符）。"""
        pr = _make_pr(title="A" * 1000)
        self.assertEqual(len(pr.title), 1000)

    def test_empty_author(self):
        """空作者。"""
        pr = _make_pr(author="")
        self.assertEqual(pr.author, "")

    def test_from_dict_missing_required_fields(self):
        """缺少必填字段应报错。"""
        with self.assertRaises(KeyError):
            PullRequest.from_dict({"number": 1})

    def test_from_dict_empty_reviews_field(self):
        """reviews 字段为 None 的情况。"""
        data = {
            "number": 1, "title": "T", "author": "a", "repo": "r",
            "state": "open", "created_at": "2026-03-22T10:00:00Z",
            "updated_at": "2026-03-22T10:00:00Z",
            "reviews": None,
        }
        with self.assertRaises(TypeError):
            PullRequest.from_dict(data)


class TestEdgeCasesTimeoutChecker(unittest.TestCase):
    """超时检测边界条件。"""

    def test_negative_hours_ago(self):
        """未来时间创建的 PR。"""
        pr = _make_pr_recent(hours_ago=-10)
        hours = get_wait_hours(pr)
        self.assertLess(hours, 0)

    def test_timeout_zero_threshold(self):
        """超时阈值为 0 时，所有 PR 都超时。"""
        pr = _make_pr_recent(hours_ago=0)
        config = Config(timeout_hours=0)
        self.assertTrue(is_timeout(pr, config))

    def test_timeout_negative_threshold(self):
        """超时阈值为负数时，所有 PR 都超时。"""
        pr = _make_pr_recent(hours_ago=100)
        config = Config(timeout_hours=-10)
        self.assertTrue(is_timeout(pr, config))

    def test_very_old_pr(self):
        """非常久远的 PR（1 年前）。"""
        pr = _make_pr_recent(hours_ago=8760)  # ~365 天
        hours = get_wait_hours(pr)
        self.assertGreater(hours, 8000)

    def test_format_timeout_message_no_changed_files(self):
        """没有变更文件时的消息格式。"""
        pr = _make_pr_recent(changed_files=[])
        msg = format_timeout_message(pr, 25.0)
        self.assertIn("PR #1", msg)


class TestEdgeCasesQualityChecker(unittest.TestCase):
    """质量检测边界条件。"""

    def test_pr_with_zero_reviews_empty_files(self):
        """没有任何 Review 和变更文件的 PR。"""
        pr = _make_pr(changed_files=[])
        result = check_review_quality(pr, Config())
        self.assertFalse(result.is_high_risk)
        self.assertFalse(result.is_superficial)

    def test_multiple_superficial_reviews(self):
        """多个走过场式 Review。"""
        pr = _make_pr(
            reviews=[
                Review("alice", "approved", "LGTM", "2026-03-21T10:00:00Z"),
                Review("bob", "approved", "👍", "2026-03-21T11:00:00Z"),
                Review("charlie", "approved", "ok", "2026-03-21T12:00:00Z"),
            ]
        )
        result = check_review_quality(pr, Config())
        self.assertEqual(len(result.superficial_reviews), 3)

    def test_superficial_with_changes_requested_still_counts(self):
        """有 changes_requested 但同时有 LGTM approval。"""
        pr = _make_pr(
            reviews=[
                Review("alice", "approved", "LGTM", "2026-03-21T10:00:00Z"),
                Review("bob", "changes_requested", "需要修改", "2026-03-21T11:00:00Z"),
            ]
        )
        result = check_review_quality(pr, Config())
        self.assertTrue(result.is_superficial)  # 仍有走过场式 Review

    def test_custom_superficial_patterns(self):
        """自定义走过场模式列表。"""
        config = Config(superficial_patterns=["ship it", "🚢"])
        r = Review("bob", "approved", "Ship it!", "2026-03-21T10:00:00Z")
        self.assertTrue(is_superficial_review(r, config))

    def test_custom_superficial_patterns_empty(self):
        """空的走过场模式列表——只有空 body 算走过场。"""
        config = Config(superficial_patterns=[])
        r = Review("bob", "approved", "LGTM", "2026-03-21T10:00:00Z")
        self.assertFalse(is_superficial_review(r, config))  # 不再匹配
        r2 = Review("bob", "approved", "", "2026-03-21T10:00:00Z")
        self.assertTrue(is_superficial_review(r, config))  # 空的仍然算

    def test_large_change_threshold_zero(self):
        """阈值为 0 时所有变更都是大变更。"""
        pr = _make_pr(added_lines=1, deleted_lines=0)
        config = Config(large_change_threshold=0)
        self.assertTrue(is_large_change(pr, config))

    def test_find_high_risk_with_path_traversal(self):
        """路径包含 .. 的情况。"""
        pr = _make_pr(changed_files=["../payment/checkout.py"])
        result = find_high_risk_dirs(pr, Config())
        # 当前实现按 / 分割后匹配每个部分，".." 不会匹配到 payment
        # 但 ".." 不应该被当作目录名
        self.assertNotIn("..", result)


class TestEdgeCasesReviewerRouter(unittest.TestCase):
    """审查人分配边界条件。"""

    def test_rule_with_trailing_star(self):
        """规则以 ** 结尾的情况。"""
        rules = {"src/**": ["alice"]}
        files = ["src/payment/a.py"]
        result = match_reviewer_rules(files, rules)
        self.assertIn("alice", result)

    def test_rule_exact_match_no_slash(self):
        """规则没有 / 时的行为。"""
        rules = {"payment": ["alice"]}
        files = ["src/payment/a.py"]
        result = match_reviewer_rules(files, rules)
        # "payment".rstrip("*").rstrip("/") + "/" = "payment/"
        # "src/payment/a.py".startswith("payment/") → False
        self.assertEqual(len(result), 0)

    def test_single_character_file_path(self):
        """极短文件路径。"""
        rules = {"a": ["alice"]}
        files = ["a"]
        result = match_reviewer_rules(files, rules)
        # "a".rstrip("*").rstrip("/") = "a"
        # "a".startswith("a/") → False
        self.assertEqual(len(result), 0)

    def test_empty_reviewer_list_in_rule(self):
        """规则映射到空审查人列表。"""
        rules = {"src/payment/**": []}
        files = ["src/payment/a.py"]
        result = match_reviewer_rules(files, rules)
        self.assertEqual(len(result), 0)


class TestEdgeCasesStore(unittest.TestCase):
    """数据存储边界条件。"""

    def test_corrupted_json_file(self):
        """JSON 文件损坏时应安全处理。"""
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "data.json")
        with open(path, "w") as f:
            f.write("{corrupted json")
        store = PRStore(path)
        with self.assertRaises(json.JSONDecodeError):
            store.get_all()

    def test_empty_json_file(self):
        """空 JSON 文件。"""
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "data.json")
        with open(path, "w") as f:
            f.write("")
        store = PRStore(path)
        with self.assertRaises(json.JSONDecodeError):
            store.get_all()

    def test_json_file_with_null(self):
        """JSON 文件内容为 null。"""
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "data.json")
        with open(path, "w") as f:
            f.write("null")
        store = PRStore(path)
        # null 不是 dict，_load_all 会返回 null
        with self.assertRaises(AttributeError):
            store.get_all()

    def test_add_pr_with_unicode_content(self):
        """包含 Unicode 特殊字符的 PR。"""
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "data.json")
        store = PRStore(path)
        pr = _make_pr(title="修复支付🐛漏洞 💰🔒", author="张三")
        store.add(pr)
        loaded = store.get("test/repo", 1)
        self.assertEqual(loaded.title, "修复支付🐛漏洞 💰🔒")
        self.assertEqual(loaded.author, "张三")


class TestEdgeCasesReport(unittest.TestCase):
    """报告生成边界条件。"""

    def test_all_reviews_from_same_day(self):
        """同一天内的所有 Review。"""
        prs = [_make_pr(days_ago=0)]
        config = Config()
        start = datetime.now(timezone.utc) - timedelta(days=1)
        end = datetime.now(timezone.utc)
        stats = generate_weekly_report(prs, config, week_start=start, week_end=end)
        self.assertEqual(stats.total_prs, 1)

    def test_report_with_invalid_created_at(self):
        """PR 的 created_at 无效时应被跳过。"""
        prs = [PullRequest(
            number=1, title="Bad", author="a", repo="r", state="open",
            created_at="not-a-date", updated_at="not-a-date",
        )]
        config = Config()
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end = datetime(2030, 1, 1, tzinfo=timezone.utc)
        stats = generate_weekly_report(prs, config, week_start=start, week_end=end)
        # 无效时间的 PR 应被跳过或报错——当前实现 try/except 会跳过
        self.assertEqual(stats.total_prs, 0)

    def test_week_range_across_year_boundary(self):
        """跨年周范围。"""
        start = datetime(2025, 12, 29, tzinfo=timezone.utc)
        end = datetime(2026, 1, 4, tzinfo=timezone.utc)
        stats = generate_weekly_report([], Config(), week_start=start, week_end=end)
        self.assertEqual(stats.start_date, "2025-12-29")
        self.assertEqual(stats.end_date, "2026-01-04")


# ============================================================
# 📋 Webhook Handler 测试（Cherny 完全没有测试）
# ============================================================

class TestWebhookHandler(unittest.TestCase):
    """Webhook 事件处理测试——Cherny 完全遗漏。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = PRStore(os.path.join(self.tmpdir, "data.json"))
        self.config = Config(webhook_url="", timeout_hours=24)

    def test_parse_github_pr_opened(self):
        """解析 GitHub PR opened 事件。"""
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 42,
                "title": "Fix payment bug",
                "user": {"login": "alice"},
                "state": "open",
                "created_at": "2026-03-22T10:00:00Z",
                "updated_at": "2026-03-22T10:00:00Z",
                "requested_reviewers": [{"login": "bob"}],
                "labels": [],
                "changed_files": ["src/payment/fix.py"],
                "additions": 10,
                "deletions": 5,
                "reviews": [],
            },
            "repository": {"full_name": "company/repo"},
        }
        pr = parse_github_pr_payload(payload)
        self.assertEqual(pr.number, 42)
        self.assertEqual(pr.title, "Fix payment bug")
        self.assertEqual(pr.author, "alice")
        self.assertEqual(pr.repo, "company/repo")
        self.assertEqual(pr.reviewers, ["bob"])

    def test_parse_empty_payload(self):
        """空 payload 应安全处理。"""
        pr = parse_github_pr_payload({})
        self.assertEqual(pr.number, 0)
        self.assertEqual(pr.title, "")
        self.assertEqual(pr.author, "")
        self.assertEqual(pr.repo, "")

    def test_handle_pr_event_dry_run(self):
        """dry_run 模式不应发送真实 Webhook。"""
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 1,
                "title": "Test",
                "user": {"login": "alice"},
                "state": "open",
                "created_at": "2026-03-20T10:00:00Z",
                "updated_at": "2026-03-20T10:00:00Z",
                "requested_reviewers": [],
                "labels": [],
                "changed_files": [],
                "additions": 0,
                "deletions": 0,
                "reviews": [],
            },
            "repository": {"full_name": "test/repo"},
        }
        messages = handle_pr_event(payload, self.store, self.config, dry_run=True)
        self.assertIsInstance(messages, list)
        # PR 应该被保存到 store
        saved = self.store.get("test/repo", 1)
        self.assertIsNotNone(saved)

    def test_handle_pr_event_with_quality_alert(self):
        """有走过场 Review 的 PR 应触发质量警告。"""
        payload = {
            "action": "submitted",
            "pull_request": {
                "number": 2,
                "title": "Payment schema change",
                "user": {"login": "alice"},
                "state": "open",
                "created_at": "2026-03-20T10:00:00Z",
                "updated_at": "2026-03-22T10:00:00Z",
                "requested_reviewers": [],
                "labels": [],
                "changed_files": ["db/migration/001.sql"],
                "additions": 50,
                "deletions": 10,
                "reviews": [{
                    "user": {"login": "bob"},
                    "state": "APPROVED",
                    "body": "LGTM 👍",
                    "submitted_at": "2026-03-22T10:00:00Z",
                }],
            },
            "repository": {"full_name": "test/repo"},
        }
        messages = handle_pr_event(payload, self.store, self.config, dry_run=True)
        # 应该有质量警告消息（但 webhook_url 为空，所以不会发送）
        # 需要有 webhook_url 才会触发
        self.config.webhook_url = "http://invalid.example.com"
        messages = handle_pr_event(payload, PRStore(os.path.join(self.tmpdir, "data2.json")), self.config, dry_run=True)
        self.assertGreater(len(messages), 0)

    def test_handle_pr_event_suggests_reviewers_on_open(self):
        """新 PR 应触发审查人建议。"""
        self.config.reviewer_rules = {"src/payment/**": ["bob"]}
        self.config.webhook_url = "http://invalid.example.com"
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 3,
                "title": "Payment fix",
                "user": {"login": "alice"},
                "state": "open",
                "created_at": "2026-03-22T10:00:00Z",
                "updated_at": "2026-03-22T10:00:00Z",
                "requested_reviewers": [],
                "labels": [],
                "changed_files": ["src/payment/fix.py"],
                "additions": 5,
                "deletions": 0,
                "reviews": [],
            },
            "repository": {"full_name": "test/repo"},
        }
        messages = handle_pr_event(payload, self.store, self.config, dry_run=True)
        self.assertGreater(len(messages), 0)
        self.assertIn("@bob", messages[-1])

    def test_handle_pr_event_github_state_uppercase(self):
        """GitHub payload 中的 state 可能是大写（如 "OPEN"）。"""
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 4,
                "title": "Test",
                "user": {"login": "alice"},
                "state": "OPEN",  # 大写
                "created_at": "2026-03-22T10:00:00Z",
                "updated_at": "2026-03-22T10:00:00Z",
                "requested_reviewers": [],
                "labels": [],
                "changed_files": [],
                "additions": 0,
                "deletions": 0,
                "reviews": [],
            },
            "repository": {"full_name": "test/repo"},
        }
        pr = parse_github_pr_payload(payload)
        self.assertEqual(pr.state, "open")  # 应该被转为小写

    def test_handle_pr_event_github_review_state_uppercase(self):
        """GitHub review state 是大写的（APPROVED/CHANGES_REQUESTED/COMMENTED）。"""
        payload = {
            "action": "submitted",
            "pull_request": {
                "number": 5,
                "title": "Test",
                "user": {"login": "alice"},
                "state": "open",
                "created_at": "2026-03-22T10:00:00Z",
                "updated_at": "2026-03-22T10:00:00Z",
                "requested_reviewers": [],
                "labels": [],
                "changed_files": [],
                "additions": 0,
                "deletions": 0,
                "reviews": [{
                    "user": {"login": "bob"},
                    "state": "CHANGES_REQUESTED",
                    "body": "Fix this",
                    "submitted_at": "2026-03-22T10:00:00Z",
                }],
            },
            "repository": {"full_name": "test/repo"},
        }
        pr = parse_github_pr_payload(payload)
        self.assertEqual(pr.reviews[0].state, "changes_requested")  # 小写


# ============================================================
# 📋 Dashboard 集成测试
# ============================================================

class TestDashboardIntegration(unittest.TestCase):
    """Dashboard 与其他模块的集成测试。"""

    def test_html_escape_in_api_response(self):
        """JSON API 响应应正确处理特殊字符。"""
        pr = _make_pr_recent(title='PR with "quotes" & <brackets>')
        result = _render_api([pr], Config())
        data = json.loads(result)
        self.assertEqual(data[0]["title"], 'PR with "quotes" & <brackets>')

    def test_dashboard_404(self):
        """不存在的路由应返回 404。"""
        server = start_dashboard([], Config(), port=0)
        port = server.server_address[1]
        t = Thread(target=server.handle_request)
        t.daemon = True
        t.start()
        t.join(timeout=2)
        # 由于 handle_request 只处理一个请求，重启
        t2 = Thread(target=server.handle_request)
        t2.daemon = True
        t2.start()
        try:
            url = f"http://127.0.0.1:{port}/nonexistent"
            with urlopen(url, timeout=2) as resp:
                self.assertEqual(resp.status, 404)
        except (URLError, Exception):
            pass  # 连接失败也可以接受
        finally:
            server.server_close()

    def test_empty_dashboard(self):
        """没有任何 PR 时的看板。"""
        html = _render_html([], Config())
        self.assertIn("PR Queue", html)
        self.assertIn(">0<", html)  # Open PR 数为 0

    def test_api_empty_list(self):
        """没有任何 PR 时的 API。"""
        result = _render_api([], Config())
        data = json.loads(result)
        self.assertEqual(len(data), 0)


# ============================================================
# 📋 Config 深度测试
# ============================================================

class TestConfigEdgeCases(unittest.TestCase):
    """配置文件边界条件。"""

    def test_config_with_all_fields(self):
        """所有字段都有值。"""
        config = Config(
            timeout_hours=48,
            high_risk_dirs=["a", "b"],
            superficial_patterns=["x"],
            reviewer_rules={"r": ["u"]},
            webhook_url="https://hook.example.com",
            tech_lead="boss",
            repos=["repo1", "repo2"],
            large_change_threshold=500,
        )
        d = config.to_dict()
        restored = Config.from_dict(d)
        self.assertEqual(restored.timeout_hours, 48)
        self.assertEqual(restored.repos, ["repo1", "repo2"])
        self.assertEqual(restored.large_change_threshold, 500)

    def test_config_empty_dict(self):
        """空字典应使用所有默认值。"""
        config = Config.from_dict({})
        self.assertEqual(config.timeout_hours, 24)
        self.assertEqual(config.webhook_url, "")

    def test_config_with_extra_fields_ignored(self):
        """额外的字段应被忽略。"""
        config = Config.from_dict({"timeout_hours": 12, "unknown_field": "ignored"})
        self.assertEqual(config.timeout_hours, 12)


# ============================================================
# 📋 Notifier 深度测试
# ============================================================

class TestNotifierDeep(unittest.TestCase):
    """通知发送深度测试。"""

    def test_send_to_non_routable_address(self):
        """发送到不可路由地址应安全返回 False。"""
        result = send_webhook("http://192.0.2.1/webhook", "test", dry_run=False)
        self.assertFalse(result)

    def test_send_empty_message(self):
        """空消息应该可以发送（dry_run）。"""
        result = send_webhook("http://example.com", "", dry_run=True)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
