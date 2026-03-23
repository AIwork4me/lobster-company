"""Project Pulse - 文件级指标计算。

使用 AST 解析 Python 文件，提取代码质量指标：
- 行数统计（总行数、代码行数、空行、注释行）
- 函数数量和最长函数
- 类数量
- 最大嵌套深度
- 模块 docstring 检测
"""

import ast
from pathlib import Path


def compute_file_metrics(file_path):
    """分析单个 Python 文件的代码质量指标。

    Args:
        file_path: Python 文件路径

    Returns:
        dict: 包含各项指标的字典

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件不是 .py 文件
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix != ".py":
        raise ValueError(f"Not a Python file: {file_path}")

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    line_counts = _count_line_types(lines)
    has_docstring = _check_module_docstring(source)

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return _empty_metrics(line_counts, has_docstring)

    class_count = _count_nodes(tree, ast.ClassDef)
    func_count = _count_nodes(tree, (ast.FunctionDef, ast.AsyncFunctionDef))
    func_analysis = _analyze_functions(tree)
    max_nesting = _compute_max_nesting(tree)

    return {
        "total_lines": len(lines),
        "code_lines": line_counts["code"],
        "comment_lines": line_counts["comment"],
        "blank_lines": line_counts["blank"],
        "function_count": func_count,
        "class_count": class_count,
        "max_function_length": func_analysis["max_length"],
        "max_nesting_depth": max_nesting,
        "has_module_docstring": has_docstring,
        "has_long_functions": func_analysis["long_count"] > 0,
        "has_deep_nesting": max_nesting > 4,
    }


def _empty_metrics(line_counts, has_docstring):
    """返回语法错误文件的空指标。"""
    return {
        "total_lines": 0,
        "code_lines": line_counts.get("code", 0),
        "comment_lines": line_counts.get("comment", 0),
        "blank_lines": line_counts.get("blank", 0),
        "function_count": 0,
        "class_count": 0,
        "max_function_length": 0,
        "max_nesting_depth": 0,
        "has_module_docstring": has_docstring,
        "has_long_functions": False,
        "has_deep_nesting": False,
    }


def _count_line_types(lines):
    """统计代码行、注释行、空行。"""
    counts = {"code": 0, "comment": 0, "blank": 0}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            counts["blank"] += 1
        elif stripped.startswith("#"):
            counts["comment"] += 1
        else:
            counts["code"] += 1
    return counts


def _check_module_docstring(source):
    """检查模块是否有 docstring。"""
    stripped = source.strip()
    if not stripped:
        return False
    return stripped.startswith('"""') or stripped.startswith("'''")


def _count_nodes(tree, node_types):
    """统计 AST 中特定类型节点的数量。"""
    if isinstance(node_types, type):
        node_types = (node_types,)
    return sum(1 for node in ast.walk(tree) if isinstance(node, node_types))


def _analyze_functions(tree):
    """分析所有函数的长度。

    Returns:
        dict: {"max_length": int, "long_count": int}
    """
    max_length = 0
    long_count = 0

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        func_lines = node.end_lineno - node.lineno + 1
        max_length = max(max_length, func_lines)
        if func_lines > 50:
            long_count += 1

    return {"max_length": max_length, "long_count": long_count}


def _compute_max_nesting(tree):
    """计算 AST 中的最大嵌套深度。"""
    max_depth = [0]

    def _walk(node, depth):
        nesting_types = (
            ast.If, ast.For, ast.While, ast.With, ast.Try,
            ast.ExceptHandler, ast.AsyncFor, ast.AsyncWith,
        )
        definition_types = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

        if isinstance(node, nesting_types) or isinstance(node, definition_types):
            depth += 1

        if depth > max_depth[0]:
            max_depth[0] = depth

        for child in ast.iter_child_nodes(node):
            _walk(child, depth)

    _walk(tree, 0)
    return max_depth[0]
