"""Project Pulse 项目健康诊断器 - 测试套件。

TDD：先定义期望行为，再实现功能。
覆盖：正常路径、异常路径、边界条件、数据完整性。
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from projectpulse.scanner import scan_project
from projectpulse.metrics import compute_file_metrics
from projectpulse.priority import prioritize_issues
from projectpulse.snapshot import save_snapshot, load_snapshot, compare_snapshots
from projectpulse.report import format_report, format_compact


class TestFileMetrics(unittest.TestCase):
    """文件级指标计算测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_empty_file_has_zero_metrics(self):
        """空文件应该返回全零指标。"""
        path = self._write("empty.py", "")
        metrics = compute_file_metrics(path)
        self.assertEqual(metrics["total_lines"], 0)
        self.assertEqual(metrics["code_lines"], 0)
        self.assertEqual(metrics["function_count"], 0)
        self.assertEqual(metrics["class_count"], 0)
        self.assertEqual(metrics["max_function_length"], 0)
        self.assertEqual(metrics["max_nesting_depth"], 0)

    def test_simple_function_metrics(self):
        """简单函数应该正确计算指标。"""
        code = (
            '"""Module docstring."""\n'
            'def add(a, b):\n'
            '    return a + b\n'
        )
        path = self._write("simple.py", code)
        metrics = compute_file_metrics(path)
        self.assertEqual(metrics["total_lines"], 3)
        self.assertEqual(metrics["function_count"], 1)
        self.assertEqual(metrics["class_count"], 0)
        self.assertEqual(metrics["max_function_length"], 2)  # def line + body
        self.assertTrue(metrics["has_module_docstring"])

    def test_class_metrics(self):
        """类应该被正确计数。"""
        code = (
            'class Dog:\n'
            '    def bark(self):\n'
            '        return "woof"\n'
            '\n'
            'class Cat:\n'
            '    def meow(self):\n'
            '        return "meow"\n'
        )
        path = self._write("classes.py", code)
        metrics = compute_file_metrics(path)
        self.assertEqual(metrics["class_count"], 2)
        self.assertEqual(metrics["function_count"], 2)

    def test_nesting_depth(self):
        """嵌套深度应该正确计算。"""
        code = (
            'def outer():\n'
            '    for i in range(10):\n'
            '        if i > 5:\n'
            '            x = i\n'
        )
        path = self._write("nested.py", code)
        metrics = compute_file_metrics(path)
        # def=1, for=2, if=3
        self.assertEqual(metrics["max_nesting_depth"], 3)

    def test_missing_docstring_detected(self):
        """缺少模块 docstring 应该被检测到。"""
        code = 'def foo():\n    pass\n'
        path = self._write("nodoc.py", code)
        metrics = compute_file_metrics(path)
        self.assertFalse(metrics["has_module_docstring"])

    def test_long_function_detected(self):
        """超过 50 行的函数应该被标记。"""
        lines = ['def long_func():\n'] + ['    x = {}\n'.format(i) for i in range(55)]
        code = "".join(lines)
        path = self._write("long.py", code)
        metrics = compute_file_metrics(path)
        self.assertEqual(metrics["max_function_length"], 56)  # def line + 55 body lines
        self.assertTrue(metrics["has_long_functions"])

    def test_nonexistent_file_raises_error(self):
        """不存在的文件应该抛出 FileNotFoundError。"""
        with self.assertRaises(FileNotFoundError):
            compute_file_metrics("/nonexistent/path.py")


class TestProjectScanner(unittest.TestCase):
    """项目扫描器测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write(self, relpath, content):
        full = os.path.join(self.tmpdir, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return full

    def test_scan_empty_directory(self):
        """空目录应该返回空结果。"""
        result = scan_project(self.tmpdir)
        self.assertEqual(len(result["files"]), 0)
        self.assertEqual(result["total_files"], 0)
        self.assertEqual(result["total_lines"], 0)

    def test_scan_finds_all_python_files(self):
        """扫描器应该找到所有 .py 文件。"""
        self._write("a.py", "x = 1\n")
        self._write("b.py", "y = 2\n")
        self._write("sub/c.py", "z = 3\n")
        result = scan_project(self.tmpdir)
        self.assertEqual(result["total_files"], 3)

    def test_scan_skips_non_python_files(self):
        """扫描器应该跳过非 .py 文件。"""
        self._write("readme.txt", "hello")
        self._write("data.json", "{}")
        self._write("main.py", "pass\n")
        result = scan_project(self.tmpdir)
        self.assertEqual(result["total_files"], 1)

    def test_scan_aggregates_metrics(self):
        """扫描器应该正确汇总行数。"""
        self._write("a.py", "x = 1\n")
        self._write("b.py", "y = 2\nz = 3\n")
        result = scan_project(self.tmpdir)
        self.assertEqual(result["total_lines"], 3)

    def test_scan_reports_average_metrics(self):
        """扫描器应该计算平均指标。"""
        self._write("a.py", "x = 1\n")
        self._write("b.py", "y = 2\n")
        result = scan_project(self.tmpdir)
        # 2 files, each 1 line
        self.assertEqual(result["avg_lines_per_file"], 1.0)

    def test_scan_nonexistent_directory_raises_error(self):
        """不存在的目录应该抛出 FileNotFoundError。"""
        with self.assertRaises(FileNotFoundError):
            scan_project("/nonexistent/project")


class TestIssuePrioritization(unittest.TestCase):
    """问题优先级排序测试。"""

    def test_issues_sorted_by_severity(self):
        """问题应该按严重程度降序排列。"""
        issues = [
            {"file": "a.py", "type": "warning", "message": "long function"},
            {"file": "b.py", "type": "critical", "message": "deep nesting"},
            {"file": "c.py", "type": "info", "message": "missing docstring"},
        ]
        prioritized = prioritize_issues(issues)
        self.assertEqual(prioritized[0]["type"], "critical")
        self.assertEqual(prioritized[1]["type"], "warning")
        self.assertEqual(prioritized[2]["type"], "info")

    def test_empty_issues_returns_empty(self):
        """空问题列表应该返回空列表。"""
        self.assertEqual(prioritize_issues([]), [])

    def test_critical_issues_first(self):
        """严重问题必须排在前面。"""
        issues = [
            {"file": "a.py", "type": "info", "message": "m1"},
            {"file": "b.py", "type": "warning", "message": "m2"},
            {"file": "c.py", "type": "critical", "message": "m3"},
            {"file": "d.py", "type": "critical", "message": "m4"},
            {"file": "e.py", "type": "warning", "message": "m5"},
        ]
        result = prioritize_issues(issues)
        types = [i["type"] for i in result]
        # All criticals before warnings, all warnings before info
        critical_end = types.index("warning") if "warning" in types else len(types)
        warning_end = types.index("info") if "info" in types else len(types)
        self.assertTrue(all(t == "critical" for t in types[:critical_end]))
        self.assertTrue(all(t == "warning" for t in types[critical_end:warning_end]))


class TestSnapshot(unittest.TestCase):
    """快照保存/加载/比较测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_save_and_load_roundtrip(self):
        """保存后加载应该得到相同数据。"""
        data = {
            "timestamp": "2026-03-22T12:00:00",
            "project_path": "/tmp/test",
            "total_files": 5,
            "total_lines": 100,
            "files": [{"path": "a.py", "total_lines": 10}],
        }
        path = os.path.join(self.tmpdir, "snap.json")
        save_snapshot(data, path)
        loaded = load_snapshot(path)
        self.assertEqual(loaded["total_files"], 5)
        self.assertEqual(loaded["total_lines"], 100)
        self.assertEqual(len(loaded["files"]), 1)

    def test_load_nonexistent_raises_error(self):
        """加载不存在的快照应该抛出 FileNotFoundError。"""
        with self.assertRaises(FileNotFoundError):
            load_snapshot("/nonexistent/snap.json")

    def test_compare_snapshots_detects_growth(self):
        """比较快照应该检测到文件增长。"""
        old = {
            "timestamp": "2026-03-21T12:00:00",
            "total_files": 2,
            "total_lines": 50,
            "files": [{"path": "a.py", "total_lines": 25, "code_lines": 20}],
        }
        new = {
            "timestamp": "2026-03-22T12:00:00",
            "total_files": 3,
            "total_lines": 80,
            "files": [
                {"path": "a.py", "total_lines": 40, "code_lines": 35},
                {"path": "b.py", "total_lines": 20, "code_lines": 15},
            ],
        }
        diff = compare_snapshots(old, new)
        self.assertEqual(diff["files_added"], 1)
        self.assertEqual(diff["lines_added"], 30)
        # a.py grew from 25 to 40
        self.assertTrue(any(c["path"] == "a.py" and c["lines_change"] == 15
                           for c in diff["file_changes"]))

    def test_save_creates_directory_if_needed(self):
        """保存快照应该自动创建目录。"""
        path = os.path.join(self.tmpdir, "sub", "dir", "snap.json")
        save_snapshot({"total_files": 1, "total_lines": 10, "files": []}, path)
        self.assertTrue(os.path.exists(path))


class TestReport(unittest.TestCase):
    """报告格式化测试。"""

    def test_format_report_returns_string(self):
        """报告应该返回字符串。"""
        report = format_report({
            "total_files": 1,
            "total_lines": 100,
            "issues": [],
            "top_files": [],
            "project_path": "/tmp/test",
        })
        self.assertIsInstance(report, str)

    def test_format_report_contains_project_info(self):
        """报告应该包含项目基本信息。"""
        report = format_report({
            "total_files": 5,
            "total_lines": 500,
            "issues": [{"file": "a.py", "type": "critical", "message": "test"}],
            "top_files": [{"path": "a.py", "total_lines": 200}],
            "project_path": "/tmp/test",
        })
        self.assertIn("5", report)
        self.assertIn("500", report)

    def test_format_compact_is_shorter(self):
        """紧凑报告应该比完整报告短。"""
        data = {
            "total_files": 5,
            "total_lines": 500,
            "issues": [
                {"file": "a.py", "type": "critical", "message": "deep nesting"},
                {"file": "b.py", "type": "warning", "message": "long function"},
            ],
            "top_files": [{"path": "a.py", "total_lines": 200}],
            "project_path": "/tmp/test",
        }
        full = format_report(data)
        compact = format_compact(data)
        self.assertLess(len(compact), len(full))

    def test_format_report_handles_no_issues(self):
        """没有问题时报告不应该崩溃。"""
        report = format_report({
            "total_files": 0,
            "total_lines": 0,
            "issues": [],
            "top_files": [],
            "project_path": "/tmp/test",
        })
        self.assertIsInstance(report, str)


class TestIntegration(unittest.TestCase):
    """集成测试：端到端扫描真实文件。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write(self, relpath, content):
        full = os.path.join(self.tmpdir, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

    def test_full_scan_of_realistic_project(self):
        """对一个"真实"小项目做完整扫描。"""
        self._write("__init__.py", '"""Package."""\n')
        self._write("utils.py", (
            '"""Utility functions."""\n'
            'import os\n'
            '\n'
            'def get_path(name):\n'
            '    return os.path.join("/tmp", name)\n'
        ))
        self._write("core.py", (
            'class Engine:\n'
            '    def run(self):\n'
            '        for i in range(10):\n'
            '            if i % 2 == 0:\n'
            '                print(i)\n'
        ))
        self._write("bad.py", (
            'def very_long_function():\n'
            + '    x = 1\n' * 55
            + '\n'
            'def nested_deep():\n'
            '    for a in range(5):\n'
            '        for b in range(5):\n'
            '            for c in range(5):\n'
            '                for d in range(5):\n'
            '                    pass\n'
        ))

        result = scan_project(self.tmpdir)

        # Basic sanity checks
        self.assertEqual(result["total_files"], 4)
        self.assertGreater(result["total_lines"], 0)
        self.assertGreater(len(result["issues"]), 0)  # bad.py should have issues

        # bad.py should be flagged for long function
        long_func_issues = [
            i for i in result["issues"]
            if "long" in i["message"].lower() and "bad.py" in i["file"]
        ]
        self.assertGreater(len(long_func_issues), 0)

        # bad.py should be flagged for deep nesting
        deep_issues = [
            i for i in result["issues"]
            if "nest" in i["message"].lower() and "bad.py" in i["file"]
        ]
        self.assertGreater(len(deep_issues), 0)

        # Report should work
        report = format_report(result)
        self.assertIn("bad.py", report)


if __name__ == "__main__":
    unittest.main()
