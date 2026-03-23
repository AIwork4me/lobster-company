"""圈复杂度分析模块 - 基于 McCabe 圈复杂度的计算。"""

import ast
from typing import Dict, List

from .stats import FunctionInfo


class ComplexityVisitor(ast.NodeVisitor):
    """遍历 AST 计算每个函数的圈复杂度。"""

    def __init__(self):
        self.function_complexity: Dict[str, int] = {}
        self._current_function = None
        self._complexity = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._analyze_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._analyze_function(node)

    def _analyze_function(self, node) -> None:
        # 保存/恢复状态以支持嵌套
        prev_func = self._current_function
        prev_complexity = self._complexity

        self._current_function = node.name
        self._complexity = 1  # 基础复杂度

        # 遍历函数体
        self.generic_visit(node)

        self.function_complexity[node.name] = self._complexity

        # 恢复
        self._current_function = prev_func
        self._complexity = prev_complexity

    def visit_If(self, node: ast.If) -> None:
        self._complexity += 1
        # elif 也算分支
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self._complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self._complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self._complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._complexity += 1
        self.generic_visit(node)

    def visit_boolop(self, node: ast.BoolOp) -> None:
        # and/or 每个操作数都是一个分支点
        self._complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        # 三元表达式
        self._complexity += 1
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        # 列表/字典/集合推导式中每个 if 子句
        self._complexity += len(node.ifs)
        self.generic_visit(node)


def analyze_complexity(source: str, functions: List[FunctionInfo]) -> List[FunctionInfo]:
    """计算所有函数的圈复杂度并更新 FunctionInfo。"""
    tree = ast.parse(source)
    visitor = ComplexityVisitor()
    visitor.visit(tree)

    # 对于同名函数（如不同类中），使用位置匹配
    func_name_count: Dict[str, int] = {}
    name_index: Dict[str, int] = {}

    for func in functions:
        name = f"{func.class_name}.{func.name}" if func.class_name else func.name
        func_name_count[name] = func_name_count.get(name, 0) + 1

    # 用行号进行精确匹配
    node_map: Dict[tuple, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node_map[(node.lineno, node.name)] = 0  # 占位

    # 重新遍历，按出现顺序分配
    class Context:
        def __init__(self):
            self.class_name = ""
            self.func_nodes = []

    ctx = Context()

    class Collector(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            ctx.class_name = node.name
            self.generic_visit(node)
            ctx.class_name = ""

        def visit_FunctionDef(self, node):
            ctx.func_nodes.append((node.lineno, node.name, ctx.class_name))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            ctx.func_nodes.append((node.lineno, node.name, ctx.class_name))
            self.generic_visit(node)

    Collector().visit(tree)

    # 将复杂度分配给函数
    for lineno, name, cls_name in ctx.func_nodes:
        key = f"{cls_name}.{name}" if cls_name else name
        if key in visitor.function_complexity:
            # 找到对应的 FunctionInfo
            for func in functions:
                full_name = f"{func.class_name}.{func.name}" if func.class_name else func.name
                if full_name == key and func.line_start == lineno:
                    func.complexity = visitor.function_complexity[key]
                    break
            else:
                # 按名称匹配（处理同名情况）
                remaining = [f for f in functions
                             if (f"{f.class_name}.{f.name}" if f.class_name else f.name) == key
                             and f.complexity == 0]
                if remaining:
                    remaining[0].complexity = visitor.function_complexity[key]

    return functions


def get_complexity_level(complexity: int) -> str:
    """返回复杂度等级描述。"""
    if complexity <= 5:
        return "低"
    elif complexity <= 10:
        return "中"
    elif complexity <= 20:
        return "高"
    else:
        return "极高"
