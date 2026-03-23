"""代码统计分析模块 - 统计行数、函数数、类数等基础指标。"""

import ast
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class FunctionInfo:
    name: str
    line_start: int
    line_end: int
    line_count: int
    complexity: int
    is_method: bool = False
    class_name: str = ""


@dataclass
class ClassInfo:
    name: str
    line_start: int
    line_end: int
    method_count: int


@dataclass
class CodeStats:
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)

    @property
    def average_function_length(self) -> float:
        if not self.functions:
            return 0.0
        return sum(f.line_count for f in self.functions) / len(self.functions)

    @property
    def max_function_length(self) -> int:
        if not self.functions:
            return 0
        return max(f.line_count for f in self.functions)


def _count_line_types(source: str) -> Tuple[int, int, int]:
    """统计代码行、注释行、空行数。"""
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_multiline_string = False

    for line in source.splitlines():
        stripped = line.strip()

        if not stripped:
            blank_lines += 1
            continue

        # 检测多行字符串的边界
        triple_count = stripped.count('"""') + stripped.count("'''")
        if triple_count == 1:
            in_multiline_string = not in_multiline_string
            # 如果这行不是多行字符串的开头，算代码行
            if not in_multiline_string:
                comment_lines += 1
            continue
        elif triple_count >= 2:
            # 同一行开闭
            comment_lines += 1
            continue

        if in_multiline_string:
            comment_lines += 1
            continue

        if stripped.startswith('#'):
            comment_lines += 1
        else:
            code_lines += 1

    return code_lines, comment_lines, blank_lines


def _find_function_end(lines: List[str], start_line: int, indent_level: int) -> int:
    """找到函数体的结束行号（基于缩进）。"""
    for i in range(start_line, len(lines)):
        if i < len(lines) and lines[i].strip():
            current_indent = len(lines[i]) - len(lines[i].lstrip())
            if current_indent <= indent_level and lines[i].strip():
                return i
    return len(lines)


class StatsCollector(ast.NodeVisitor):
    """AST 遍历器，收集函数和类信息。"""

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self._current_class: str = ""

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._current_class = node.name
        # 收集类的方法
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        class_info = ClassInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            method_count=len(methods),
        )
        self.classes.append(class_info)
        self.generic_visit(node)
        self._current_class = ""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._add_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._add_function(node)
        self.generic_visit(node)

    def _add_function(self, node) -> None:
        line_count = (node.end_lineno or node.lineno) - node.lineno + 1
        is_method = self._current_class != ""
        func_info = FunctionInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            line_count=line_count,
            complexity=0,  # 后续由 ComplexityAnalyzer 填充
            is_method=is_method,
            class_name=self._current_class,
        )
        self.functions.append(func_info)


def collect_stats(source: str) -> CodeStats:
    """分析源码，收集基础统计信息。"""
    tree = ast.parse(source)
    lines = source.splitlines()

    stats = CodeStats(
        total_lines=len(lines),
    )

    # 行类型统计
    code, comment, blank = _count_line_types(source)
    stats.code_lines = code
    stats.comment_lines = comment
    stats.blank_lines = blank

    # AST 分析
    collector = StatsCollector(lines)
    collector.visit(tree)

    stats.functions = collector.functions
    stats.classes = collector.classes
    stats.function_count = len(stats.functions)
    stats.class_count = len(stats.classes)

    return stats
