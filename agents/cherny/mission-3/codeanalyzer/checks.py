"""代码问题检查模块 - 检测各种代码异味和潜在问题。"""

import ast
import re
from dataclasses import dataclass
from enum import Enum
from typing import List


class Severity(Enum):
    CRITICAL = "🔴 严重"
    WARNING = "🟡 警告"
    SUGGESTION = "💡 建议"


@dataclass
class Issue:
    severity: Severity
    rule_id: str
    message: str
    line: int
    column: int = 0
    detail: str = ""


class IssueChecker(ast.NodeVisitor):
    """遍历 AST，检测代码问题。"""

    def __init__(self, source_lines: List[str], source: str):
        self.source_lines = source_lines
        self.source = source
        self.issues: List[Issue] = []

    def _add_issue(self, severity: Severity, rule_id: str, message: str,
                   line: int, column: int = 0, detail: str = ""):
        self.issues.append(Issue(severity, rule_id, message, line, column, detail))

    # ── 函数/方法检查 ──────────────────────────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node):
        line_count = (node.end_lineno or node.lineno) - node.lineno + 1

        # 超大函数（>50行）
        if line_count > 50:
            self._add_issue(
                Severity.WARNING, "F001", "超大函数",
                node.lineno, detail=f"函数 '{node.name}' 有 {line_count} 行，建议拆分为更小的函数（≤50行）"
            )
        elif line_count > 30:
            self._add_issue(
                Severity.SUGGESTION, "F002", "函数偏长",
                node.lineno, detail=f"函数 '{node.name}' 有 {line_count} 行，考虑是否可以简化（≤30行为佳）"
            )

        # 参数过多（>5个）
        args = node.args
        total_args = len(args.args) + len(args.kwonlyargs)
        if args.vararg:
            total_args += 1
        if args.kwarg:
            total_args += 1
        if total_args > 7:
            self._add_issue(
                Severity.WARNING, "F003", "参数过多",
                node.lineno, detail=f"函数 '{node.name}' 有 {total_args} 个参数，建议使用对象封装或 **kwargs"
            )
        elif total_args > 5:
            self._add_issue(
                Severity.SUGGESTION, "F004", "参数偏多",
                node.lineno, detail=f"函数 '{node.name}' 有 {total_args} 个参数，考虑是否可以精简"
            )

        # 嵌套深度检查
        self._check_nesting_depth(node)

    def _check_nesting_depth(self, node):
        """检查函数内的嵌套深度。"""
        max_depth = 0

        def walk(body, depth):
            nonlocal max_depth
            for stmt in body:
                # 当前语句本身如果就是控制结构，深度+1
                if isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    depth += 1
                    if depth > max_depth:
                        max_depth = depth
                    # 继续遍历子体
                    child_body = getattr(stmt, 'body', [])
                    walk(child_body, depth)
                    # orelse 分支
                    orelse = getattr(stmt, 'orelse', [])
                    if orelse:
                        walk(orelse, depth - 1)  # orelse 和同级
                else:
                    # 非控制结构，继续看子节点
                    for child in ast.iter_child_nodes(stmt):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                            child_body = getattr(child, 'body', [])
                            walk(child_body, depth + 1)

        walk(node.body, 0)

        if max_depth > 4:
            self._add_issue(
                Severity.WARNING, "N001", "嵌套过深",
                node.lineno, detail=f"函数 '{node.name}' 嵌套深度达 {max_depth} 层，建议重构降低复杂度"
            )

    # ── 异常处理检查 ──────────────────────────────────────────

    def visit_Try(self, node: ast.Try):
        self._check_try(node)
        self.generic_visit(node)

    def _check_try(self, node):
        for handler in node.handlers:
            # 裸 except / except Exception
            if handler.type is None:
                self._add_issue(
                    Severity.CRITICAL, "E001", "裸 except 捕获",
                    handler.lineno,
                    detail="使用了 bare except，会捕获所有异常包括 KeyboardInterrupt，应至少 except Exception"
                )
            elif isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                self._add_issue(
                    Severity.WARNING, "E002", "过宽的异常捕获",
                    handler.lineno,
                    detail="捕获 Exception 范围过宽，建议捕获具体异常类型"
                )

            # 空 except 体
            if not handler.body or (len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass)):
                self._add_issue(
                    Severity.CRITICAL, "E003", "空 except 体",
                    handler.lineno,
                    detail="except 块为空或只有 pass，异常被静默吞掉。至少应该记录日志"
                )

            # 只有一个 continue/break
            if len(handler.body) == 1 and isinstance(handler.body[0], (ast.Continue, ast.Break)):
                self._add_issue(
                    Severity.WARNING, "E004", "except 中仅含 continue/break",
                    handler.lineno,
                    detail="except 块中只有 continue/break，异常被静默忽略"
                )

    # ── 类检查 ──────────────────────────────────────────────

    def visit_ClassDef(self, node: ast.ClassDef):
        # 过大的类（>300行）
        line_count = (node.end_lineno or node.lineno) - node.lineno + 1
        if line_count > 300:
            self._add_issue(
                Severity.WARNING, "C001", "类过大",
                node.lineno,
                detail=f"类 '{node.name}' 有 {line_count} 行，建议拆分职责"
            )

        # 方法过多（>20）
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if len(methods) > 20:
            self._add_issue(
                Severity.WARNING, "C002", "方法过多",
                node.lineno,
                detail=f"类 '{node.name}' 有 {len(methods)} 个方法，可能违反单一职责原则"
            )

        self.generic_visit(node)

    # ── 导入检查 ──────────────────────────────────────────────

    def visit_Import(self, node: ast.Import):
        self._check_imports(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self._check_imports(node)
        self.generic_visit(node)

    def _check_imports(self, node):
        if isinstance(node, ast.ImportFrom) and node.module == '__future__':
            return  # future 导入不算

        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            # 通配符导入
            if name == '*':
                self._add_issue(
                    Severity.WARNING, "I001", "通配符导入",
                    node.lineno,
                    detail="使用了 'from X import *'，可能引入命名冲突，建议显式导入"
                )

    # ── 全局变量检查 ──────────────────────────────────────────

    # 通过外层模块级检查处理

    # ── 代码风格检查 ──────────────────────────────────────────

    def visit_Assign(self, node: ast.Assign):
        # 多重赋值链 a = b = c = value
        if len(node.targets) > 1:
            self._add_issue(
                Severity.SUGGESTION, "A001", "多重赋值",
                node.lineno,
                detail="多重赋值 a = b = c = val 可能导致混淆，建议分行赋值"
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        self._check_calls(node)
        self.generic_visit(node)

    def _check_calls(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # 危险函数
        dangerous = {
            'eval': "eval() 执行任意代码，存在严重安全风险，应使用 ast.literal_eval 或其他安全替代",
            'exec': "exec() 执行任意代码，存在严重安全风险，几乎总有更好的替代方案",
            'getattr': None,  # 仅在特定上下文危险，不报
            'setattr': None,
            'compile': "compile() 可用于构造恶意代码，确保输入可信",
        }
        if func_name in dangerous and dangerous[func_name]:
            self._add_issue(
                Severity.CRITICAL, "D001", f"危险函数: {func_name}()",
                node.lineno,
                detail=dangerous[func_name]
            )

        # 不安全的 input 处理（如果用在 eval 中）
        if func_name == 'input' and node.lineno < len(self.source_lines):
            # 检查后续是否用了 eval
            pass  # 太复杂，跳过这个检查

    # ── 模块级检查 ──────────────────────────────────────────

    def check_module_level(self, tree):
        """检查模块级别的问题。"""

        # 检查是否有 docstring
        if tree.body and not isinstance(tree.body[0], ast.Expr):
            self._add_issue(
                Severity.SUGGESTION, "M001", "缺少模块 docstring",
                1,
                detail="建议在文件开头添加模块级别的文档字符串"
            )
        elif tree.body and isinstance(tree.body[0], ast.Expr):
            expr_val = tree.body[0].value
            if not isinstance(expr_val, ast.Constant) or not isinstance(expr_val.value, str):
                self._add_issue(
                    Severity.SUGGESTION, "M001", "缺少模块 docstring",
                    1,
                    detail="建议在文件开头添加模块级别的文档字符串"
                )

        # 全局变量
        global_vars = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if not name.startswith('_') and name.upper() == name:
                            global_vars.append(name)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id.upper() == node.target.id and not node.target.id.startswith('_'):
                    global_vars.append(node.target.id)

        if len(global_vars) > 5:
            self._add_issue(
                Severity.WARNING, "M002", "全局变量过多",
                1,
                detail=f"发现 {len(global_vars)} 个全局变量（{', '.join(global_vars[:5])}...），建议封装到类或配置模块中"
            )

        # 文件长度检查
        total_lines = len(self.source_lines)
        if total_lines > 500:
            self._add_issue(
                Severity.WARNING, "M003", "文件过大",
                1,
                detail=f"文件有 {total_lines} 行，建议拆分为多个模块（≤500行为佳）"
            )
        elif total_lines > 300:
            self._add_issue(
                Severity.SUGGESTION, "M004", "文件偏长",
                1,
                detail=f"文件有 {total_lines} 行，考虑是否可以拆分（≤300行为佳）"
            )


def run_checks(source: str) -> List[Issue]:
    """对源代码执行所有检查，返回问题列表。"""
    lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [Issue(
            Severity.CRITICAL, "S001", "语法错误",
            e.lineno or 1, e.offset or 0,
            detail=str(e.msg)
        )]

    checker = IssueChecker(lines, source)
    checker.visit(tree)
    checker.check_module_level(tree)

    return checker.issues
