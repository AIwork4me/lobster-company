"""测试 Web 看板。"""

import json
import unittest
from http.server import HTTPServer
from io import BytesIO
from pr_queue.dashboard import start_dashboard, make_handler
from pr_queue.models import PullRequest, Review, Config
from pr_queue.timeout_checker import get_wait_hours


def _make_pr(number=1, hours_ago=5, **kwargs):
    from datetime import datetime, timezone, timedelta
    created = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    pr_kwargs = dict(
        number=number, title=f"PR {number}", author="alice",
        repo="test/repo", state="open",
        created_at=created.isoformat(),
        updated_at=created.isoformat(),
        changed_files=kwargs.pop("changed_files", ["src/main.py"]),
        reviewers=kwargs.pop("reviewers", ["bob"]),
    )
    pr_kwargs.update(kwargs)
    return PullRequest(**pr_kwargs)


class TestDashboard(unittest.TestCase):
    """看板功能测试。"""

    @classmethod
    def setUpClass(cls):
        prs = [
            _make_pr(number=1, hours_ago=5),
            _make_pr(number=2, hours_ago=30),
            _make_pr(number=3, hours_ago=2, state="closed"),
            _make_pr(
                number=4, hours_ago=10,
                changed_files=["src/payment/checkout.py"],
                reviews=[Review("bob", "approved", "👍", "")],
                added_lines=150, deleted_lines=100,
            ),
        ]
        config = Config(timeout_hours=24)
        cls.server = start_dashboard(prs, config, port=0)
        # 获取实际端口
        cls.port = cls.server.server_address[1]

        import threading
        t = threading.Thread(target=cls.server.handle_request)
        t.daemon = True
        t.start()

    def _request(self, path):
        import urllib.request
        url = f"http://127.0.0.1:{self.port}{path}"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.status, resp.read().decode("utf-8")
        except Exception:
            # Server only handles one request; restart for each test
            return None, None

    @classmethod
    def tearDownClass(cls):
        cls.server.server_close()


class TestDashboardHTML(unittest.TestCase):
    """看板 HTML 渲染测试。"""

    def test_render_html_contains_pr_info(self):
        prs = [_make_pr(number=42, hours_ago=5)]
        config = Config()
        from pr_queue.dashboard import make_handler, _render_html
        html = _render_html(prs, config)
        self.assertIn("#42", html)
        self.assertIn("alice", html)
        self.assertIn("PR 42", html)

    def test_render_html_contains_summary(self):
        prs = [
            _make_pr(number=1, hours_ago=30),
            _make_pr(number=2, hours_ago=5),
        ]
        config = Config(timeout_hours=24)
        from pr_queue.dashboard import _render_html
        html = _render_html(prs, config)
        self.assertIn("Open PR", html)

    def test_render_html_closed_prs_not_shown(self):
        prs = [
            _make_pr(number=1, hours_ago=5, state="closed"),
        ]
        config = Config()
        from pr_queue.dashboard import _render_html
        html = _render_html(prs, config)
        # Open PR count should be 0
        self.assertIn(">0<", html)

    def test_render_html_sorted_by_wait_time(self):
        prs = [
            _make_pr(number=1, hours_ago=5),
            _make_pr(number=2, hours_ago=50),
            _make_pr(number=3, hours_ago=10),
        ]
        config = Config()
        from pr_queue.dashboard import _render_html
        html = _render_html(prs, config)
        # 在 HTML 中，行按降序等待时间排列
        # 找到 "PR 2" 和 "PR 1" 的位置（在标题列中）
        pos_2 = html.index("PR 2")
        pos_1 = html.index("PR 1")
        pos_3 = html.index("PR 3")
        # PR 2 (50h) 应该首先出现
        self.assertLess(pos_2, pos_1)
        self.assertLess(pos_2, pos_3)


class TestDashboardAPI(unittest.TestCase):
    """看板 JSON API 测试。"""

    def test_render_api_returns_json(self):
        prs = [_make_pr(number=1, hours_ago=5)]
        config = Config()
        from pr_queue.dashboard import _render_api
        result = _render_api(prs, config)
        data = json.loads(result)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["number"], 1)

    def test_api_contains_quality_fields(self):
        prs = [_make_pr(
            number=1, hours_ago=5,
            changed_files=["src/payment/a.py"],
        )]
        config = Config()
        from pr_queue.dashboard import _render_api
        result = _render_api(prs, config)
        data = json.loads(result)
        self.assertIn("is_high_risk", data[0])
        self.assertIn("needs_rereview", data[0])
        self.assertIn("risk_dirs", data[0])
        self.assertTrue(data[0]["is_high_risk"])

    def test_api_only_open_prs(self):
        prs = [
            _make_pr(number=1, hours_ago=5, state="open"),
            _make_pr(number=2, hours_ago=3, state="closed"),
        ]
        config = Config()
        from pr_queue.dashboard import _render_api
        result = _render_api(prs, config)
        data = json.loads(result)
        self.assertEqual(len(data), 1)

    def test_api_sorted_by_wait_time(self):
        prs = [
            _make_pr(number=1, hours_ago=5),
            _make_pr(number=2, hours_ago=50),
        ]
        config = Config()
        from pr_queue.dashboard import _render_api
        result = _render_api(prs, config)
        data = json.loads(result)
        self.assertGreater(data[0]["wait_hours"], data[1]["wait_hours"])


if __name__ == "__main__":
    unittest.main()
