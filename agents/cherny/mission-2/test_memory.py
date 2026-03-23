"""Agent Memory Manager - 单元测试"""

import json
import os
import tempfile
import unittest
from pathlib import Path

# 确保能导入 memory 模块
import sys
sys.path.insert(0, str(Path(__file__).parent))
import memory


class TestMemoryManager(unittest.TestCase):
    """使用临时目录测试所有记忆管理功能。"""

    def setUp(self):
        """每个测试用例创建一个临时 JSON 文件。"""
        self.tmpdir = tempfile.mkdtemp()
        self.filepath = Path(self.tmpdir) / "test_memory.json"

    def _add_sample(self, content: str, tags: list) -> dict:
        return memory.add_memory(self.filepath, content, tags)

    # ---- 1. 添加记忆 → 能读取到 ----
    def test_add_and_list(self):
        self._add_sample("今天学会了Python的HTML解析", ["学习", "python"])
        self._add_sample("完成了项目文档撰写", ["工作", "文档"])
        results = memory.list_memories(self.filepath)
        self.assertEqual(len(results), 2)
        contents = [m["content"] for m in results]
        self.assertIn("今天学会了Python的HTML解析", contents)
        self.assertIn("完成了项目文档撰写", contents)

    def test_add_auto_increment_id(self):
        e1 = self._add_sample("第一条", ["a"])
        e2 = self._add_sample("第二条", ["b"])
        self.assertEqual(e1["id"], 1)
        self.assertEqual(e2["id"], 2)

    def test_add_preserves_tags(self):
        e = self._add_sample("测试标签", ["学习", "python", "web"])
        self.assertEqual(e["tags"], ["学习", "python", "web"])

    def test_add_timestamps(self):
        e = self._add_sample("时间测试", ["test"])
        self.assertIsNotNone(e["created_at"])
        self.assertIsNotNone(e["updated_at"])
        # created_at 和 updated_at 应该格式一致
        self.assertEqual(e["created_at"], e["updated_at"])

    # ---- 2. 按标签过滤 → 只返回匹配的 ----
    def test_filter_by_tag(self):
        self._add_sample("Python学习笔记", ["学习", "python"])
        self._add_sample("买菜清单", ["生活"])
        self._add_sample("机器学习入门", ["学习", "ai"])
        results = memory.list_memories(self.filepath, tag="学习")
        self.assertEqual(len(results), 2)
        for m in results:
            self.assertIn("学习", m["tags"])

    def test_filter_nonexistent_tag(self):
        self._add_sample("随机内容", ["a"])
        results = memory.list_memories(self.filepath, tag="不存在的标签")
        self.assertEqual(len(results), 0)

    def test_filter_with_limit(self):
        for i in range(10):
            self._add_sample(f"记忆{i}", ["tag"])
        results = memory.list_memories(self.filepath, tag="tag", limit=3)
        self.assertEqual(len(results), 3)

    # ---- 3. 搜索 → 能找到包含关键词的 ----
    def test_search_keyword(self):
        self._add_sample("今天学会了HTML解析", ["学习"])
        self._add_sample("Python是一门好语言", ["python"])
        self._add_sample("HTML和CSS是前端基础", ["web"])
        results = memory.search_memories(self.filepath, "HTML")
        self.assertEqual(len(results), 2)
        contents = [m["content"] for m in results]
        self.assertIn("今天学会了HTML解析", contents)
        self.assertIn("HTML和CSS是前端基础", contents)

    def test_search_case_insensitive(self):
        self._add_sample("html解析很实用", ["学习"])
        results = memory.search_memories(self.filepath, "HTML")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        self._add_sample("不相关的内容", ["test"])
        results = memory.search_memories(self.filepath, "xyz不存在")
        self.assertEqual(len(results), 0)

    # ---- 4. 删除 → 列表中不再出现 ----
    def test_delete_existing(self):
        e1 = self._add_sample("要删除的", ["temp"])
        self._add_sample("保留的", ["keep"])
        result = memory.delete_memory(self.filepath, e1["id"])
        self.assertTrue(result)
        remaining = memory.list_memories(self.filepath)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["content"], "保留的")

    def test_delete_nonexistent(self):
        result = memory.delete_memory(self.filepath, 999)
        self.assertFalse(result)

    def test_delete_then_add_id_not_reused(self):
        e1 = self._add_sample("第一条", ["a"])
        memory.delete_memory(self.filepath, e1["id"])
        e2 = self._add_sample("第二条", ["b"])
        # ID 不应该复用被删除的 ID
        self.assertEqual(e2["id"], e1["id"] + 1)

    # ---- 5. stats → 返回正确的统计数据 ----
    def test_stats_empty(self):
        stats = memory.get_stats(self.filepath)
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["recent_7_days"], 0)
        self.assertEqual(stats["tag_distribution"], {})

    def test_stats_total_and_tags(self):
        self._add_sample("内容1", ["学习", "python"])
        self._add_sample("内容2", ["工作"])
        self._add_sample("内容3", ["学习", "ai"])
        stats = memory.get_stats(self.filepath)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["tag_distribution"]["学习"], 2)
        self.assertEqual(stats["tag_distribution"]["python"], 1)
        self.assertEqual(stats["tag_distribution"]["ai"], 1)

    def test_stats_recent_7_days(self):
        self._add_sample("近期记忆", ["new"])
        stats = memory.get_stats(self.filepath)
        self.assertEqual(stats["recent_7_days"], 1)


if __name__ == "__main__":
    unittest.main()
