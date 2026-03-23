"""NLP 解析器测试。"""

import sys
import os
import unittest
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant.nlp import (
    parse_command, extract_time, classify_content,
    extract_review_time, _extract_url, _extract_tags, _extract_person,
)


class TestExtractUrl(unittest.TestCase):
    """URL 提取测试。"""

    def test_http_url(self):
        self.assertEqual(
            _extract_url("收藏这个 https://example.com/article 行业报告"),
            "https://example.com/article",
        )

    def test_no_url(self):
        self.assertIsNone(_extract_url("明天下午三点开会"))

    def test_url_with_punctuation(self):
        self.assertIsNotNone(_extract_url("看这个 https://example.com/，不错"))


class TestExtractTags(unittest.TestCase):
    """标签提取测试。"""

    def test_single_tag(self):
        self.assertEqual(_extract_tags("会议 #工作"), ["工作"])

    def test_multiple_tags(self):
        self.assertEqual(
            _extract_tags("报价 #工作 #紧急 #张总"),
            ["工作", "紧急", "张总"],
        )

    def test_no_tags(self):
        self.assertEqual(_extract_tags("明天下午开会"), [])


class TestExtractPerson(unittest.TestCase):
    """关联人提取测试。"""

    def test_send_to_person(self):
        result = _extract_person("把报价单发给张总")
        self.assertEqual(result, "张总")

    def test_tell_person(self):
        result = _extract_person("告诉李明下午开会")
        self.assertEqual(result, "李明")

    def test_meet_person(self):
        result = _extract_person("约王经理周五下午")
        self.assertEqual(result, "王经理")

    def test_no_person(self):
        self.assertIsNone(_extract_person("明天完成项目报告"))


class TestExtractTime(unittest.TestCase):
    """时间提取测试。"""

    def test_tomorrow(self):
        result = extract_time("明天下午三点")
        if result is not None:
            expected_date = (datetime.now() + timedelta(days=1)).date()
            self.assertEqual(result.date(), expected_date)

    def test_today(self):
        result = extract_time("今天下午五点")
        if result is not None:
            self.assertEqual(result.date(), datetime.now().date())

    def test_day_after_tomorrow(self):
        result = extract_time("后天上午十点")
        if result is not None:
            expected_date = (datetime.now() + timedelta(days=2)).date()
            self.assertEqual(result.date(), expected_date)

    def test_no_time(self):
        result = extract_time("写一份项目报告")
        self.assertIsNone(result)

    def test_month_day(self):
        result = extract_time("3月25日下午两点")
        if result is not None:
            self.assertEqual(result.month, 3)
            self.assertEqual(result.day, 25)

    def test_relative_days(self):
        result = extract_time("3天后")
        if result is not None:
            expected = (datetime.now() + timedelta(days=3)).date()
            self.assertEqual(result.date(), expected)


class TestClassifyContent(unittest.TestCase):
    """内容自动分类测试。"""

    def test_article(self):
        self.assertEqual(classify_content("行业趋势分析文章", None), "待阅读")

    def test_tool(self):
        self.assertEqual(classify_content("推荐一个好用的工具", None), "工具推荐")

    def test_learning(self):
        self.assertEqual(classify_content("Python 学习教程", None), "学习资料")

    def test_unknown(self):
        self.assertEqual(classify_content("随便记点东西", None), "未分类")

    def test_url_article(self):
        self.assertEqual(
            classify_content("值得看", "https://blog.example.com/article"),
            "待阅读",
        )


class TestExtractReviewTime(unittest.TestCase):
    """回顾时间提取测试。"""

    def test_weekend(self):
        result = extract_review_time("周末看一下")
        self.assertIsNotNone(result)

    def test_relative_days(self):
        result = extract_review_time("3天后看")
        if result is not None:
            expected = (datetime.now() + timedelta(days=3)).date()
            self.assertEqual(result.date(), expected)

    def test_default(self):
        result = extract_review_time("记一下这个")
        if result is not None:
            expected = (datetime.now() + timedelta(days=7)).date()
            self.assertEqual(result.date(), expected)


class TestParseCommand(unittest.TestCase):
    """命令解析集成测试。"""

    def test_create_todo_with_time(self):
        cmd = parse_command("明天下午三点前把报价单发给张总")
        self.assertEqual(cmd.intent, "create_todo")
        self.assertEqual(cmd.person, "张总")
        self.assertIsNotNone(cmd.deadline)

    def test_create_todo_with_tags(self):
        cmd = parse_command("完成项目报告 #工作 #紧急")
        self.assertEqual(cmd.intent, "create_todo")
        self.assertIn("工作", cmd.tags)
        self.assertIn("紧急", cmd.tags)

    def test_list_todos(self):
        cmd = parse_command("今天有什么事")
        self.assertEqual(cmd.intent, "list_todos")

    def test_complete_by_id(self):
        cmd = parse_command("完成了 #3")
        self.assertEqual(cmd.intent, "complete")
        self.assertEqual(cmd.todo_id, 3)

    def test_complete_by_content(self):
        cmd = parse_command("做完了报价单")
        self.assertEqual(cmd.intent, "complete")
        self.assertIn("报价单", cmd.content)

    def test_delete_by_id(self):
        cmd = parse_command("删除 #5")
        self.assertEqual(cmd.intent, "delete")
        self.assertEqual(cmd.todo_id, 5)

    def test_add_bookmark_with_url(self):
        cmd = parse_command("收藏这个 https://example.com/article 行业报告")
        self.assertEqual(cmd.intent, "add_bookmark")
        self.assertEqual(cmd.url, "https://example.com/article")

    def test_list_bookmarks(self):
        cmd = parse_command("待阅读")
        self.assertEqual(cmd.intent, "list_bookmarks")

    def test_stats(self):
        cmd = parse_command("本周统计")
        self.assertEqual(cmd.intent, "stats")

    def test_help(self):
        cmd = parse_command("帮助")
        self.assertEqual(cmd.intent, "help")

    def test_empty_input(self):
        cmd = parse_command("")
        self.assertEqual(cmd.intent, "unknown")

    def test_exit_not_parsed(self):
        """退出命令由 CLI 层处理，NLP 不解析。"""
        cmd = parse_command("退出")
        self.assertIn(cmd.intent, ("unknown", "create_todo"))


if __name__ == "__main__":
    unittest.main()
