"""代码质量分析器的测试套件。"""

import os
import sys
import unittest
from pathlib import Path

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from codeanalyzer.analyzer import analyze_source, analyze_file
from codeanalyzer.stats import collect_stats, CodeStats
from codeanalyzer.checks import run_checks, Severity, Issue
from codeanalyzer.complexity import analyze_complexity, get_complexity_level
from codeanalyzer.duplicates import detect_duplicates
from codeanalyzer.report import calculate_score, format_report, format_json, AnalysisReport
from codeanalyzer.stats import FunctionInfo, ClassInfo


# ══════════════════════════════════════════════════════════════
# 测试用的代码片段
# ══════════════════════════════════════════════════════════════

CLEAN_CODE = '''"""一个简洁的模块。"""

def greet(name: str) -> str:
    """返回问候语。"""
    return f"Hello, {name}!"

class Greeter:
    """问候类。"""

    def __init__(self, greeting: str = "Hello"):
        self.greeting = greeting

    def say(self, name: str) -> str:
        """向某人问好。"""
        return f"{self.greeting}, {name}!"
'''

BARE_EXCEPT_CODE = '''def risky():
    try:
        do_something()
    except:
        pass
    try:
        do_more()
    except Exception:
        pass
'''

LARGE_FUNCTION_CODE = '''def process_data(data):
    """一个超长的函数。"""
    result = []
    for item in data:
        # 模拟 60 行
        x = item
        y = x + 1
        z = y * 2
        w = z / 3
        a = w + x
        b = a - y
        c = b * z
        d = c / w
        e = d + a
        f = e - b
        g = f * c
        h = g / d
        i = h + e
        j = i - f
        k = j * g
        l = k / h
        m = l + i
        n = m - j
        o = n * k
        p = o / l
        q = p + m
        r = q - n
        s = r * o
        t = s / p
        u = t + q
        v = u - r
        ww = v * s
        xx = ww / t
        yy = xx + u
        zz = yy - v
        aa = zz * ww
        bb = aa / xx
        cc = bb + yy
        dd = cc - zz
        ee = dd * aa
        ff = ee / bb
        gg = ff + cc
        hh = gg - dd
        ii = hh * ee
        jj = ii / ff
        kk = jj + gg
        ll = kk - hh
        mm = ll * ii
        nn = mm / jj
        oo = nn + kk
        pp = oo - ll
        result.append(pp)
    return result
'''

COMPLEX_CODE = '''def complex_logic(x, y, z):
    """高复杂度函数。"""
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(x):
                    if y % i == 0:
                        while z > 0:
                            z -= 1
                            if z % 2 == 0:
                                return True
                            elif z % 3 == 0:
                                continue
            elif z < 0:
                return False
        elif y < 0:
            pass
    elif x < 0:
        return False
    return None
'''

DUPLICATE_CODE = '''def foo():
    x = 1
    y = x + 2
    z = y * 3
    w = z - 4
    return w

def bar():
    x = 1
    y = x + 2
    z = y * 3
    w = z - 4
    return w
'''

DANGEROUS_CODE = '''def unsafe():
    user_input = "import os"
    eval(user_input)
    exec("print('hello')")
'''

MANY_PARAMS_CODE = '''def too_many_params(a, b, c, d, e, f, g, h):
    return a + b + c + d + e + f + g + h
'''

EMPTY_CLASS_CODE = '''class EmptyClass:
    pass
'''

NO_DOCSTRING_CODE = '''def foo():
    return 42

class Bar:
    pass
'''

DEEP_NESTING_CODE = '''def deeply_nested():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        return "deep"
'''


# ══════════════════════════════════════════════════════════════
# 测试类
# ══════════════════════════════════════════════════════════════

class TestStatsCollector(unittest.TestCase):
    """测试代码统计分析。"""

    def test_clean_code_stats(self):
        stats = collect_stats(CLEAN_CODE)
        self.assertGreater(stats.total_lines, 0)
        self.assertGreater(stats.code_lines, 0)
        self.assertGreater(stats.comment_lines, 0)  # 有 docstring
        self.assertEqual(stats.function_count, 3)  # greet, __init__, say
        self.assertEqual(stats.class_count, 1)  # Greeter

    def test_function_line_count(self):
        stats = collect_stats(CLEAN_CODE)
        greet = next(f for f in stats.functions if f.name == "greet")
        self.assertGreater(greet.line_count, 0)

    def test_class_info(self):
        stats = collect_stats(CLEAN_CODE)
        self.assertEqual(len(stats.classes), 1)
        self.assertEqual(stats.classes[0].name, "Greeter")
        self.assertEqual(stats.classes[0].method_count, 2)

    def test_empty_file(self):
        stats = collect_stats("")
        # "".splitlines() 返回 []，长度为 0
        self.assertEqual(stats.total_lines, 0)
        self.assertEqual(stats.function_count, 0)
        self.assertEqual(stats.class_count, 0)


class TestIssueChecker(unittest.TestCase):
    """测试问题检测。"""

    def test_bare_except(self):
        issues = run_checks(BARE_EXCEPT_CODE)
        critical = [i for i in issues if i.rule_id == "E001"]
        self.assertTrue(len(critical) >= 1, "应检测到裸 except")

    def test_empty_except_body(self):
        issues = run_checks(BARE_EXCEPT_CODE)
        empty = [i for i in issues if i.rule_id == "E003"]
        self.assertTrue(len(empty) >= 1, "应检测到空 except 体")

    def test_large_function(self):
        issues = run_checks(LARGE_FUNCTION_CODE)
        large = [i for i in issues if i.rule_id == "F001"]
        self.assertTrue(len(large) >= 1, "应检测到超大函数")

    def test_dangerous_eval(self):
        issues = run_checks(DANGEROUS_CODE)
        eval_issues = [i for i in issues if i.rule_id == "D001" and "eval" in i.message]
        self.assertTrue(len(eval_issues) >= 1, "应检测到 eval 的使用")

    def test_dangerous_exec(self):
        issues = run_checks(DANGEROUS_CODE)
        exec_issues = [i for i in issues if i.rule_id == "D001" and "exec" in i.message]
        self.assertTrue(len(exec_issues) >= 1, "应检测到 exec 的使用")

    def test_many_params(self):
        issues = run_checks(MANY_PARAMS_CODE)
        param_issues = [i for i in issues if i.rule_id in ("F003", "F004")]
        self.assertTrue(len(param_issues) >= 1, "应检测到参数过多")

    def test_no_issues_for_clean_code(self):
        issues = run_checks(CLEAN_CODE)
        critical = [i for i in issues if i.severity == Severity.CRITICAL]
        self.assertEqual(len(critical), 0, "干净代码不应有严重问题")

    def test_syntax_error(self):
        issues = run_checks("def broken(:\n  pass")
        self.assertTrue(len(issues) == 1)
        self.assertEqual(issues[0].rule_id, "S001")

    def test_wildcard_import(self):
        code = "from os import *\n"
        issues = run_checks(code)
        wildcard = [i for i in issues if i.rule_id == "I001"]
        self.assertTrue(len(wildcard) >= 1, "应检测到通配符导入")

    def test_deep_nesting(self):
        issues = run_checks(DEEP_NESTING_CODE)
        nesting = [i for i in issues if i.rule_id == "N001"]
        self.assertTrue(len(nesting) >= 1, "应检测到嵌套过深")


class TestComplexity(unittest.TestCase):
    """测试圈复杂度分析。"""

    def test_simple_function(self):
        source = "def foo():\n    return 1\n"
        from codeanalyzer.stats import collect_stats
        stats = collect_stats(source)
        funcs = analyze_complexity(source, stats.functions)
        self.assertEqual(funcs[0].complexity, 1)

    def test_complex_function(self):
        stats = collect_stats(COMPLEX_CODE)
        funcs = analyze_complexity(COMPLEX_CODE, stats.functions)
        self.assertGreater(funcs[0].complexity, 5, "复杂函数的圈复杂度应大于 5")

    def test_complexity_levels(self):
        self.assertEqual(get_complexity_level(3), "低")
        self.assertEqual(get_complexity_level(8), "中")
        self.assertEqual(get_complexity_level(15), "高")
        self.assertEqual(get_complexity_level(25), "极高")


class TestDuplicates(unittest.TestCase):
    """测试重复代码检测。"""

    def test_detects_exact_duplicates(self):
        dups = detect_duplicates(DUPLICATE_CODE, min_lines=3, threshold=0.8)
        self.assertGreater(len(dups), 0, "应检测到重复代码块")

    def test_no_duplicates_in_clean_code(self):
        dups = detect_duplicates(CLEAN_CODE, min_lines=3, threshold=0.8)
        self.assertEqual(len(dups), 0, "干净代码不应有重复")

    def test_different_code_not_flagged(self):
        code = "def a():\n    return 1\n\ndef b():\n    return 2\n"
        dups = detect_duplicates(code, min_lines=3, threshold=0.8)
        # 这两个函数太短，不应被检测
        self.assertEqual(len(dups), 0)


class TestScoreCalculation(unittest.TestCase):
    """测试评分计算。"""

    def test_perfect_score_for_clean_code(self):
        stats = collect_stats(CLEAN_CODE)
        issues = []
        dups = []
        score = calculate_score(stats, issues, dups)
        self.assertGreater(score, 80, "干净代码的评分应较高")

    def test_score_decreases_with_issues(self):
        stats = collect_stats("def f():\n    pass\n")
        issues = [
            Issue(Severity.CRITICAL, "T001", "test", 1),
            Issue(Severity.CRITICAL, "T002", "test", 1),
        ]
        score = calculate_score(stats, issues, [])
        self.assertLess(score, 80, "有严重问题时评分应下降")

    def test_score_never_negative(self):
        stats = collect_stats("x")
        issues = [Issue(Severity.CRITICAL, "T001", "test", 1)] * 20
        score = calculate_score(stats, issues, [])
        self.assertGreaterEqual(score, 0)

    def test_score_never_exceeds_100(self):
        stats = collect_stats(CLEAN_CODE)
        score = calculate_score(stats, [], [])
        self.assertLessEqual(score, 100)


class TestIntegration(unittest.TestCase):
    """集成测试。"""

    def test_full_analysis_clean(self):
        report = analyze_source(CLEAN_CODE, "clean.py")
        self.assertGreater(report.score, 70)
        self.assertEqual(len(report.stats.classes), 1)
        self.assertGreater(report.stats.function_count, 0)

    def test_full_analysis_problematic(self):
        code = BARE_EXCEPT_CODE + "\n" + DANGEROUS_CODE
        report = analyze_source(code, "bad.py")
        self.assertLess(report.score, 50)
        self.assertGreater(report.critical_count, 0)

    def test_report_format(self):
        report = analyze_source(CLEAN_CODE, "clean.py")
        text = format_report(report)
        self.assertIn("代码质量分析报告", text)
        self.assertIn("评分", text)
        self.assertIn("代码统计", text)

    def test_json_format(self):
        report = analyze_source(CLEAN_CODE, "clean.py")
        data = format_json(report)
        self.assertIn("score", data)
        self.assertIn("stats", data)
        self.assertIn("issues", data)
        self.assertIsInstance(data["score"], int)

    def test_analyze_file(self):
        """测试分析实际文件。"""
        # 分析自身的一个源文件
        tests_dir = Path(__file__).parent
        stats_file = tests_dir.parent / "codeanalyzer" / "stats.py"
        if stats_file.exists():
            report = analyze_file(str(stats_file))
            self.assertGreater(report.score, 0)
            self.assertGreater(report.stats.function_count, 0)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            analyze_file("/nonexistent/file.py")

    def test_non_python_file(self):
        # 直接传入非 .py 后缀路径，应触发 ValueError
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not python")
            tmp_path = f.name
        try:
            with self.assertRaises(ValueError):
                analyze_file(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestReportGeneration(unittest.TestCase):
    """测试报告生成。"""

    def test_report_contains_all_sections(self):
        report = analyze_source(DANGEROUS_CODE + "\n" + DUPLICATE_CODE, "test.py")
        text = format_report(report)
        # 检查各部分
        self.assertIn("代码统计", text)
        self.assertIn("复杂度分析", text)
        self.assertIn("发现的问题", text)

    def test_critical_issues_highlighted(self):
        report = analyze_source(DANGEROUS_CODE, "test.py")
        critical = report.critical_count
        self.assertGreater(critical, 0)
        text = format_report(report)
        self.assertIn("🔴", text)

    def test_clean_report_no_critical(self):
        report = analyze_source(CLEAN_CODE, "clean.py")
        self.assertEqual(report.critical_count, 0)


if __name__ == "__main__":
    unittest.main()
