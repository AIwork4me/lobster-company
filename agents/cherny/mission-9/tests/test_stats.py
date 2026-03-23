"""数据统计模块测试。"""

import sys
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant.models import Todo
from assistant.stats import WeeklyStats


class TestWeeklyStats(unittest.TestCase):
    """统计模块测试。"""

    def test_completion_rate_all_completed(self):
        todos = [
            Todo(id=1, content="done", status="completed",
                 completed_at=datetime.now(), created_at=datetime.now()),
            Todo(id=2, content="done2", status="completed",
                 completed_at=datetime.now(), created_at=datetime.now()),
        ]
        stats = WeeklyStats(todos)
        self.assertEqual(stats.completion_rate(), 100.0)

    def test_completion_rate_none_completed(self):
        todos = [
            Todo(id=1, content="pending", status="pending",
                 created_at=datetime.now()),
        ]
        stats = WeeklyStats(todos)
        self.assertEqual(stats.completion_rate(), 0.0)

    def test_completion_rate_partial(self):
        todos = [
            Todo(id=1, content="done", status="completed",
                 completed_at=datetime.now(), created_at=datetime.now()),
            Todo(id=2, content="pending", status="pending",
                 created_at=datetime.now()),
            Todo(id=3, content="pending", status="pending",
                 created_at=datetime.now()),
        ]
        stats = WeeklyStats(todos)
        self.assertAlmostEqual(stats.completion_rate(), 33.33, places=1)

    def test_overdue_rate(self):
        todos = [
            Todo(id=1, content="overdue", status="pending",
                 deadline=datetime.now() - timedelta(hours=1),
                 created_at=datetime.now()),
            Todo(id=2, content="ok", status="pending",
                 deadline=datetime.now() + timedelta(days=3),
                 created_at=datetime.now()),
        ]
        stats = WeeklyStats(todos)
        self.assertEqual(stats.overdue_rate(), 50.0)

    def test_overdue_rate_no_pending(self):
        todos = [
            Todo(id=1, content="done", status="completed",
                 completed_at=datetime.now(), created_at=datetime.now()),
        ]
        stats = WeeklyStats(todos)
        self.assertEqual(stats.overdue_rate(), 0.0)

    def test_tag_distribution(self):
        todos = [
            Todo(id=1, content="t", tags=["工作", "紧急"], created_at=datetime.now()),
            Todo(id=2, content="t", tags=["工作"], created_at=datetime.now()),
            Todo(id=3, content="t", tags=["学习"], created_at=datetime.now()),
        ]
        stats = WeeklyStats(todos)
        dist = stats.tag_distribution()
        self.assertEqual(dist["工作"], 2)
        self.assertEqual(dist["学习"], 1)

    def test_daily_completion(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        todos = [
            Todo(id=1, content="d1", status="completed",
                 completed_at=today, created_at=today),
            Todo(id=2, content="d2", status="completed",
                 completed_at=today, created_at=today),
            Todo(id=3, content="d3", status="completed",
                 completed_at=yesterday, created_at=yesterday),
        ]
        stats = WeeklyStats(todos)
        daily = stats.daily_completion()
        today_key = today.strftime("%m-%d")
        self.assertEqual(daily.get(today_key), 2)

    def test_summary_output(self):
        todos = [
            Todo(id=1, content="done", status="completed",
                 completed_at=datetime.now(), created_at=datetime.now()),
            Todo(id=2, content="pending", status="pending",
                 created_at=datetime.now()),
        ]
        stats = WeeklyStats(todos)
        summary = stats.summary()
        self.assertIn("本周统计", summary)
        self.assertIn("完成率", summary)

    def test_empty_todos(self):
        stats = WeeklyStats([])
        self.assertEqual(stats.completion_rate(), 0.0)
        self.assertEqual(stats.overdue_rate(), 0.0)


if __name__ == "__main__":
    unittest.main()
