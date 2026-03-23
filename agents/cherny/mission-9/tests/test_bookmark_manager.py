"""收藏管理器测试。"""

import sys
import os
import shutil
import tempfile
import unittest

_test_dir = tempfile.mkdtemp()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import assistant.config as _cfg
_cfg.DATA_DIR = type(_cfg.DATA_DIR)(_test_dir)
_cfg.TODOS_FILE = _cfg.DATA_DIR / "todos.json"
_cfg.BOOKMARKS_FILE = _cfg.DATA_DIR / "bookmarks.json"

from assistant.bookmark_manager import BookmarkManager


class TestBookmarkManager(unittest.TestCase):
    """收藏管理器测试。"""

    def setUp(self):
        _cfg.TODOS_FILE.write_text("[]", encoding="utf-8")
        _cfg.BOOKMARKS_FILE.write_text("[]", encoding="utf-8")
        self.mgr = BookmarkManager()

    def test_create_basic(self):
        bm = self.mgr.create("行业趋势分析")
        self.assertEqual(bm.content, "行业趋势分析")
        self.assertFalse(bm.reviewed)

    def test_create_with_url(self):
        bm = self.mgr.create("好文章", url="https://example.com/article")
        self.assertEqual(bm.url, "https://example.com/article")

    def test_create_auto_category(self):
        bm = self.mgr.create("Python 学习教程")
        self.assertEqual(bm.category, "学习资料")

    def test_create_manual_category(self):
        bm = self.mgr.create("自定义", category="我的分类")
        self.assertEqual(bm.category, "我的分类")

    def test_create_url_auto_category(self):
        bm = self.mgr.create("行业趋势", url="https://blog.example.com/article")
        self.assertEqual(bm.category, "待阅读")

    def test_create_review_time_default(self):
        bm = self.mgr.create("随便记")
        self.assertIsNotNone(bm.remind_at)

    def test_list_all(self):
        self.mgr.create("收藏1")
        self.mgr.create("收藏2")
        all_items = self.mgr.list_all()
        self.assertEqual(len(all_items), 2)

    def test_list_by_category(self):
        self.mgr.create("学习教程")
        self.mgr.create("好工具", category="工具推荐")
        results = self.mgr.list_by_category("学习资料")
        self.assertEqual(len(results), 1)

    def test_list_unreviewed(self):
        bm = self.mgr.create("未看")
        unreviewed = self.mgr.list_unreviewed()
        self.assertEqual(len(unreviewed), 1)
        self.mgr.mark_reviewed(bm.id)
        unreviewed = self.mgr.list_unreviewed()
        self.assertEqual(len(unreviewed), 0)

    def test_mark_reviewed(self):
        bm = self.mgr.create("测试")
        result = self.mgr.mark_reviewed(bm.id)
        self.assertTrue(result.reviewed)

    def test_mark_reviewed_nonexistent(self):
        result = self.mgr.mark_reviewed(999)
        self.assertIsNone(result)

    def test_delete(self):
        bm = self.mgr.create("删除测试")
        ok = self.mgr.delete(bm.id)
        self.assertTrue(ok)
        self.assertIsNone(self.mgr.get_by_id(bm.id))

    def test_delete_nonexistent(self):
        ok = self.mgr.delete(999)
        self.assertFalse(ok)

    def test_get_by_id(self):
        bm = self.mgr.create("查找测试")
        found = self.mgr.get_by_id(bm.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.content, "查找测试")

    def test_get_categories(self):
        self.mgr.create("教程")
        self.mgr.create("工具", category="工具推荐")
        cats = self.mgr.get_categories()
        self.assertIn("学习资料", cats)
        self.assertIn("工具推荐", cats)

    def test_persistence(self):
        self.mgr.create("持久化测试", url="https://example.com")
        mgr2 = BookmarkManager()
        items = mgr2.list_all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].url, "https://example.com")


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
