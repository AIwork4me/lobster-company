"""重复代码检测模块 - 检测结构相似的代码块。"""

import ast
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class DuplicateBlock:
    """检测到的重复代码块。"""
    line_start_1: int
    line_end_1: int
    line_start_2: int
    line_end_2: int
    similarity: float  # 0.0 - 1.0
    description: str


def _normalize_ast(node: ast.AST) -> Tuple:
    """将 AST 节点归一化为可比较的元组，忽略变量名等细节。"""
    if isinstance(node, ast.Module):
        return tuple(_normalize_ast(n) for n in node.body)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ("func", node.name, tuple(_normalize_ast(n) for n in node.body))
    elif isinstance(node, ast.ClassDef):
        return ("class", node.name, tuple(_normalize_ast(n) for n in node.body))
    elif isinstance(node, ast.If):
        return ("if", tuple(_normalize_ast(n) for n in node.body))
    elif isinstance(node, ast.For):
        return ("for", tuple(_normalize_ast(n) for n in node.body))
    elif isinstance(node, ast.While):
        return ("while", tuple(_normalize_ast(n) for n in node.body))
    elif isinstance(node, ast.With):
        return ("with", tuple(_normalize_ast(n) for n in node.body))
    elif isinstance(node, ast.Try):
        parts = []
        for handler in node.handlers:
            parts.append(("except", tuple(_normalize_ast(n) for n in handler.body)))
        if node.orelse:
            parts.append(("else", tuple(_normalize_ast(n) for n in node.orelse)))
        if node.finalbody:
            parts.append(("finally", tuple(_normalize_ast(n) for n in node.finalbody)))
        return ("try", tuple(parts))
    elif isinstance(node, ast.Return):
        return ("return",)
    elif isinstance(node, ast.Assign):
        return ("assign", len(node.targets))
    elif isinstance(node, ast.Expr):
        return ("expr",)
    elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return ("comprehension",)
    elif isinstance(node, ast.Lambda):
        return ("lambda",)
    else:
        return (type(node).__name__,)


def _extract_statement_blocks(source: str, min_lines: int = 4) -> List[Tuple[int, int, str, Tuple]]:
    """提取代码中的语句块用于比较。"""
    lines = source.splitlines()
    blocks = []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return blocks

    def _visit_body(body, start_line=1):
        for node in body:
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                line_count = node.end_lineno - node.lineno + 1
                if line_count >= min_lines:
                    block_source = "\n".join(lines[node.lineno - 1:node.end_lineno])
                    normalized = _normalize_ast(node)
                    blocks.append((node.lineno, node.end_lineno, block_source, normalized))

            # 递归进入子节点
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.AST):
                    if hasattr(child, 'body') and isinstance(child.body, list):
                        _visit_body(child.body, getattr(child, 'lineno', start_line))
                    if hasattr(child, 'orelse') and isinstance(child.orelse, list):
                        _visit_body(child.orelse, getattr(child, 'lineno', start_line))
                    if hasattr(child, 'handlers') and isinstance(child.handlers, list):
                        for handler in child.handlers:
                            if hasattr(handler, 'body'):
                                _visit_body(handler.body, getattr(handler, 'lineno', start_line))

    _visit_body(tree.body)
    return blocks


def _string_similarity(s1: str, s2: str) -> float:
    """计算两个字符串的相似度（基于序列匹配）。"""
    if not s1 or not s2:
        return 0.0

    lines1 = [l.strip() for l in s1.splitlines() if l.strip()]
    lines2 = [l.strip() for l in s2.splitlines() if l.strip()]

    if not lines1 or not lines2:
        return 0.0

    # 归一化变量名：将单词标识符替换为占位符
    import re
    def normalize(s):
        return re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', 'X', s)

    norm1 = [normalize(l) for l in lines1]
    norm2 = [normalize(l) for l in lines2]

    # 计算最长公共子序列比例
    m, n = len(norm1), len(norm2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if norm1[i - 1] == norm2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_length = dp[m][n]
    return lcs_length / max(m, n)


def detect_duplicates(source: str, min_lines: int = 6, threshold: float = 0.85) -> List[DuplicateBlock]:
    """检测重复代码块。"""
    blocks = _extract_statement_blocks(source, min_lines)
    duplicates = []

    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            start1, end1, src1, norm1 = blocks[i]
            start2, end2, src2, norm2 = blocks[j]

            # 结构完全相同
            if norm1 == norm2:
                sim = 1.0
            else:
                sim = _string_similarity(src1, src2)

            if sim >= threshold:
                duplicates.append(DuplicateBlock(
                    line_start_1=start1,
                    line_end_1=end1,
                    line_start_2=start2,
                    line_end_2=end2,
                    similarity=sim,
                    description=f"行 {start1}-{end1} 与 行 {start2}-{end2} 相似度 {sim:.0%}",
                ))

    # 去重和过滤：如果 A~B 且 B~C 且 A~C，只保留 A~B
    # 同时过滤掉重叠区间（子集关系）
    seen_lines = set()
    unique = []
    for dup in sorted(duplicates, key=lambda d: d.similarity, reverse=True):
        key = (dup.line_start_1, dup.line_start_2)
        if key not in seen_lines:
            # 过滤子集：如果两个区间完全包含在已有重复中，跳过
            is_subset = False
            for existing in unique:
                if (existing.line_start_1 <= dup.line_start_1 and
                    existing.line_end_1 >= dup.line_end_1 and
                    existing.line_start_2 <= dup.line_start_2 and
                    existing.line_end_2 >= dup.line_end_2 and
                    existing.similarity >= dup.similarity):
                    is_subset = True
                    break
                if (existing.line_start_2 <= dup.line_start_1 and
                    existing.line_end_2 >= dup.line_end_1 and
                    existing.line_start_1 <= dup.line_start_2 and
                    existing.line_end_1 >= dup.line_end_2 and
                    existing.similarity >= dup.similarity):
                    is_subset = True
                    break
            if not is_subset:
                unique.append(dup)
            seen_lines.add(key)

    # 最多返回 10 组最重要的重复
    return sorted(unique, key=lambda d: d.similarity, reverse=True)[:10]
