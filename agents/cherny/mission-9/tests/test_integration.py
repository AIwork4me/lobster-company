"""集成测试：完整对话流程测试。"""

import sys
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta

_test_dir = tempfile.mkdtemp()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import assistant.config as _cfg
_cfg.DATA_DIR = type(_cfg.DATA_DIR)(_test_dir)
_cfg.TODOS_FILE = _cfg.DATA_DIR / "todos.json"
_cfg.BOOKMARKS_FILE = _cfg.DATA_DIR / "bookmarks.json"

from assistant.cli import Assistant


class TestAssistantIntegration(unittest.TestCase):
    """完整对话流程集成测试。"""

    def setUp(self):
        _cfg.TODOS_FILE.write_text("[]", encoding="utf-8")
        _cfg.BOOKMARKS_FILE.write_text("[]", encoding="utf-8")
        self.assistant = Assistant()

    def _handle(self, text: str) -> str:
        return self.assistant._handle_input(text)

    def test_full_todo_lifecycle(self):
        """完整待办生命周期：创建 -> 查看 -> 完成。"""
        r = self._handle("明天下午三点开会 #工作")
        self.assertIn("已创建", r)
        self.assertIn("开会", r)

        r = self._handle("今天有什么事")
        self.assertIn("待办", r)

        r = self._handle("完成了 #1")
        self.assertIn("已完成", r)

        r = self._handle("今天有什么事")
        self.assertIn("暂无", r)

    def test_help_command(self):
        r = self._handle("帮助")
        self.assertIn("使用说明", r)

    def test_stats_command(self):
        r = self._handle("统计")
        self.assertIn("统计报告", r)

    def test_bookmark_lifecycle(self):
        """收藏生命周期：创建 -> 查看。"""
        r = self._handle("收藏这个 https://example.com Python 学习教程")
        self.assertIn("已收藏", r)
        self.assertIn("学习资料", r)

        r = self._handle("待阅读")
        self.assertIn("待回顾", r)

    def test_create_todo_with_person(self):
        r = self._handle("明天把报价单发给张总")
        self.assertIn("已创建", r)
        self.assertIn("张总", r)

    def test_delete_todo(self):
        self._handle("创建一个临时任务")
        r = self._handle("删除 #1")
        self.assertIn("已删除", r)

    def test_unknown_command(self):
        # 随机文字在 MVP 中默认创建待办（宽容策略）
        r = self._handle("xyz随机文字abc")
        self.assertIn("已创建", r)

    def test_multiple_todos(self):
        self._handle("明天下午开会 #工作")
        self._handle("下周写月报 #工作")
        r = self._handle("今天有什么事")
        self.assertIn("开会", r)
        self.assertIn("月报", r)

    def test_create_with_tags(self):
        r = self._handle("写项目报告 #工作 #紧急")
        self.assertIn("已创建", r)
        self.assertIn("工作", r)
        self.assertIn("紧急", r)

    def test_complete_nonexistent(self):
        r = self._handle("完成了 #999")
        self.assertIn("未找到", r)

    def test_stats_with_data(self):
        self._handle("写报告 #工作")
        todo = self.assistant.todo_mgr.create("测试")
        self.assistant.todo_mgr.complete(todo_id=todo.id)
        r = self._handle("统计")
        self.assertIn("本周统计", r)
        self.assertIn("完成率", r)


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
