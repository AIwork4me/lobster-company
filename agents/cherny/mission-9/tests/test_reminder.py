"""提醒模块测试。"""

import sys
import os
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant.models import Todo
from assistant.reminder import generate_daily_summary


class TestGenerateDailySummary(unittest.TestCase):
    """每日摘要生成测试。"""

    def test_empty_list(self):
        result = generate_daily_summary([])
        self.assertIn("无待办", result)

    def test_overdue_todo(self):
        todo = Todo(
            id=1, content="逾期任务",
            deadline=datetime.now() - timedelta(hours=1),
            priority=1, status="pending",
        )
        result = generate_daily_summary([todo])
        self.assertIn("逾期", result)
        self.assertIn("逾期任务", result)

    def test_today_due(self):
        todo = Todo(
            id=2, content="今天任务",
            deadline=datetime.now() + timedelta(hours=3),
            priority=2, status="pending",
        )
        result = generate_daily_summary([todo])
        self.assertIn("今天", result)

    def test_mixed_todos(self):
        todos = [
            Todo(id=1, content="逾期", deadline=datetime.now() - timedelta(hours=1),
                 priority=1, status="pending"),
            Todo(id=2, content="今天", deadline=datetime.now() + timedelta(hours=3),
                 priority=2, status="pending"),
            Todo(id=3, content="下周", deadline=datetime.now() + timedelta(days=5),
                 priority=4, status="pending"),
        ]
        result = generate_daily_summary(todos)
        self.assertIn("逾期", result)
        self.assertIn("今日截止", result)
        self.assertIn("近期待办", result)

    def test_todo_with_tags(self):
        todo = Todo(
            id=1, content="任务", tags=["工作", "紧急"],
            deadline=datetime.now() - timedelta(hours=1),
            priority=1, status="pending",
        )
        result = generate_daily_summary([todo])
        self.assertIn("工作", result)

    def test_todo_with_person(self):
        todo = Todo(
            id=1, content="任务", person="张总",
            deadline=datetime.now() - timedelta(hours=1),
            priority=1, status="pending",
        )
        result = generate_daily_summary([todo])
        self.assertIn("张总", result)

    def test_no_deadline_todo(self):
        todo = Todo(id=1, content="随便做", priority=5, status="pending")
        result = generate_daily_summary([todo])
        self.assertIn("随便做", result)
        self.assertIn("无截止时间", result)


class TestFormatDeadline(unittest.TestCase):
    """截止时间格式化测试。"""

    def test_overdue(self):
        from assistant.reminder import _format_deadline
        todo = Todo(id=1, content="test", deadline=datetime.now() - timedelta(days=2))
        result = _format_deadline(todo)
        self.assertIn("逾期", result)
        self.assertIn("2 天", result)

    def test_today(self):
        from assistant.reminder import _format_deadline
        todo = Todo(id=1, content="test", deadline=datetime.now() + timedelta(hours=3))
        result = _format_deadline(todo)
        self.assertIn("今天", result)

    def test_tomorrow(self):
        from assistant.reminder import _format_deadline
        todo = Todo(id=1, content="test", deadline=datetime.now() + timedelta(days=1))
        result = _format_deadline(todo)
        self.assertIn("明天", result)

    def test_no_deadline(self):
        from assistant.reminder import _format_deadline
        todo = Todo(id=1, content="test")
        result = _format_deadline(todo)
        self.assertEqual(result, "无截止时间")


if __name__ == "__main__":
    unittest.main()
