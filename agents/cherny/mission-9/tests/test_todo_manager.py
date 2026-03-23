"""待办管理器测试。"""

import sys
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta

# 必须在导入 assistant 模块之前设置临时数据路径
_test_dir = tempfile.mkdtemp()

# 先修改 config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import assistant.config as _cfg
_cfg.DATA_DIR = type(_cfg.DATA_DIR)(_test_dir)
_cfg.TODOS_FILE = _cfg.DATA_DIR / "todos.json"
_cfg.BOOKMARKS_FILE = _cfg.DATA_DIR / "bookmarks.json"

from assistant.todo_manager import TodoManager


class TestTodoManager(unittest.TestCase):
    """待办管理器测试。"""

    def setUp(self):
        """每个测试前清理数据文件。"""
        # 清空数据文件，确保隔离
        _cfg.TODOS_FILE.write_text("[]", encoding="utf-8")
        _cfg.BOOKMARKS_FILE.write_text("[]", encoding="utf-8")
        self.mgr = TodoManager()

    def test_create_basic(self):
        todo = self.mgr.create("完成项目报告")
        self.assertEqual(todo.content, "完成项目报告")
        self.assertEqual(todo.status, "pending")

    def test_create_with_deadline(self):
        deadline = datetime.now() + timedelta(days=1)
        todo = self.mgr.create("开会", deadline=deadline)
        self.assertEqual(todo.deadline, deadline)

    def test_create_with_tags(self):
        todo = self.mgr.create("写报告", tags=["工作", "紧急"])
        self.assertEqual(todo.tags, ["工作", "紧急"])

    def test_create_with_person(self):
        todo = self.mgr.create("发报价单", person="张总")
        self.assertEqual(todo.person, "张总")

    def test_create_auto_id(self):
        t1 = self.mgr.create("任务1")
        t2 = self.mgr.create("任务2")
        self.assertEqual(t2.id, t1.id + 1)

    def test_list_pending_empty(self):
        self.assertEqual(self.mgr.list_pending(), [])

    def test_list_pending_sorted(self):
        today = datetime.now()
        self.mgr.create("逾期任务", deadline=today - timedelta(hours=1))
        self.mgr.create("不紧急", deadline=today + timedelta(days=7))
        self.mgr.create("今天截止", deadline=today + timedelta(hours=2))

        pending = self.mgr.list_pending()
        self.assertEqual(pending[0].priority, 1)  # overdue first
        self.assertEqual(pending[1].priority, 2)  # today

    def test_complete_by_id(self):
        todo = self.mgr.create("写报告")
        result = self.mgr.complete(todo_id=todo.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "completed")

    def test_complete_by_content(self):
        self.mgr.create("写报告")
        result = self.mgr.complete(content_match="报告")
        self.assertIsNotNone(result)

    def test_complete_nonexistent(self):
        result = self.mgr.complete(todo_id=999)
        self.assertIsNone(result)

    def test_delete_by_id(self):
        todo = self.mgr.create("临时任务")
        ok = self.mgr.delete(todo_id=todo.id)
        self.assertTrue(ok)
        self.assertEqual(len(self.mgr.list_pending()), 0)

    def test_delete_nonexistent(self):
        ok = self.mgr.delete(todo_id=999)
        self.assertFalse(ok)

    def test_search(self):
        self.mgr.create("写项目报告")
        self.mgr.create("买咖啡")
        results = self.mgr.search("项目")
        self.assertEqual(len(results), 1)
        self.assertIn("项目", results[0].content)

    def test_get_by_id(self):
        todo = self.mgr.create("测试任务")
        found = self.mgr.get_by_id(todo.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.content, "测试任务")

    def test_get_due_today(self):
        today = datetime.now()
        self.mgr.create("今天任务", deadline=today + timedelta(hours=1))
        self.mgr.create("明天任务", deadline=today + timedelta(days=1))
        due = self.mgr.get_due_today()
        self.assertEqual(len(due), 1)

    def test_get_overdue(self):
        overdue_time = datetime.now() - timedelta(hours=1)
        self.mgr.create("逾期任务", deadline=overdue_time)
        overdue = self.mgr.get_overdue()
        self.assertEqual(len(overdue), 1)

    def test_count_by_status(self):
        self.mgr.create("任务1")
        todo = self.mgr.create("任务2")
        self.mgr.complete(todo_id=todo.id)
        counts = self.mgr.count_by_status()
        self.assertEqual(counts["pending"], 1)
        self.assertEqual(counts["completed"], 1)

    def test_persistence(self):
        """数据持久化测试。"""
        self.mgr.create("持久化测试")
        mgr2 = TodoManager()
        pending = mgr2.list_pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].content, "持久化测试")

    def test_priority_no_deadline(self):
        todo = self.mgr.create("无截止时间")
        self.assertEqual(todo.priority, 5)


class TestTodoPriorityCalc(unittest.TestCase):
    """优先级计算详细测试。"""

    def setUp(self):
        _cfg.TODOS_FILE.write_text("[]", encoding="utf-8")
        self.mgr = TodoManager()

    def test_overdue_is_highest(self):
        todo = self.mgr.create("逾期", deadline=datetime.now() - timedelta(hours=1))
        self.assertEqual(todo.priority, 1)

    def test_today_is_high(self):
        todo = self.mgr.create("今天", deadline=datetime.now() + timedelta(hours=3))
        self.assertEqual(todo.priority, 2)

    def test_within_3_days(self):
        todo = self.mgr.create("3天内", deadline=datetime.now() + timedelta(days=2))
        self.assertEqual(todo.priority, 3)

    def test_this_week(self):
        todo = self.mgr.create("本周", deadline=datetime.now() + timedelta(days=5))
        self.assertEqual(todo.priority, 4)

    def test_later_is_low(self):
        todo = self.mgr.create("以后", deadline=datetime.now() + timedelta(days=30))
        self.assertEqual(todo.priority, 5)


def _cleanup():
    try:
        shutil.rmtree(_test_dir, ignore_errors=True)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        _cleanup()
