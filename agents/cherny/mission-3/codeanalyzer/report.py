"""报告生成模块 - 将分析结果格式化为可读报告。"""

from dataclasses import dataclass, field
from typing import List

from .stats import CodeStats
from .checks import Issue, Severity
from .duplicates import DuplicateBlock
from .complexity import get_complexity_level


@dataclass
class AnalysisReport:
    """完整的分析报告。"""
    filename: str
    score: int
    stats: CodeStats
    issues: List[Issue] = field(default_factory=list)
    duplicates: List[DuplicateBlock] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def suggestion_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.SUGGESTION)


def calculate_score(stats: CodeStats, issues: List[Issue],
                    duplicates: List[DuplicateBlock]) -> int:
    """计算代码质量评分（0-100）。

    评分规则：
    - 基础分 100
    - 严重问题每个扣 15 分
    - 警告每个扣 5 分
    - 建议每个扣 2 分
    - 重复代码每组扣 3 分
    - 复杂度高的函数额外扣分
    - 加分：注释比例好、函数长度合理
    """
    score = 100.0

    # 问题扣分
    for issue in issues:
        if issue.severity == Severity.CRITICAL:
            score -= 15
        elif issue.severity == Severity.WARNING:
            score -= 5
        else:
            score -= 2

    # 重复代码扣分
    for dup in duplicates:
        score -= 3 * dup.similarity

    # 复杂度扣分
    for func in stats.functions:
        if func.complexity > 20:
            score -= 5
        elif func.complexity > 10:
            score -= 2

    # 超大函数扣分
    for func in stats.functions:
        if func.line_count > 80:
            score -= 5
        elif func.line_count > 50:
            score -= 2

    # 加分项
    if stats.total_lines > 0:
        comment_ratio = stats.comment_lines / stats.total_lines
        if 0.1 <= comment_ratio <= 0.3:
            score += 5  # 注释比例健康
        elif comment_ratio > 0.5:
            score -= 3  # 注释过多可能意味着代码不清晰

    return max(0, min(100, round(score)))


def format_report(report: AnalysisReport) -> str:
    """将分析报告格式化为可读的文本。"""
    lines = []
    sep = "=" * 60

    lines.append(sep)
    lines.append(f"  Deep Agent 代码质量分析报告")
    lines.append(f"  文件: {report.filename}")
    lines.append(sep)
    lines.append("")

    # ── 评分 ──
    score_display = _score_display(report.score)
    lines.append(f"  整体评分: {report.score}/100 {score_display}")
    lines.append("")

    # ── 代码统计 ──
    lines.append("─" * 40)
    lines.append("  📊 代码统计")
    lines.append("─" * 40)
    lines.append(f"  总行数:       {report.stats.total_lines}")
    lines.append(f"  代码行:       {report.stats.code_lines}")
    lines.append(f"  注释行:       {report.stats.comment_lines}")
    lines.append(f"  空行:         {report.stats.blank_lines}")
    lines.append(f"  函数数量:     {report.stats.function_count}")
    lines.append(f"  类数量:       {report.stats.class_count}")

    if report.stats.total_lines > 0:
        comment_pct = report.stats.comment_lines / report.stats.total_lines * 100
        lines.append(f"  注释比例:     {comment_pct:.1f}%")

    if report.stats.functions:
        lines.append(f"  平均函数长度: {report.stats.average_function_length:.1f} 行")
        lines.append(f"  最大函数长度: {report.stats.max_function_length} 行")
    lines.append("")

    # ── 问题列表 ──
    lines.append("─" * 40)
    lines.append(f"  ⚠️  发现的问题 (共 {len(report.issues)} 个)")
    lines.append("─" * 40)

    if not report.issues:
        lines.append("  ✅ 没有发现问题，代码质量良好！")
    else:
        # 按严重程度分组
        grouped = {
            Severity.CRITICAL: [],
            Severity.WARNING: [],
            Severity.SUGGESTION: [],
        }
        for issue in report.issues:
            grouped[issue.severity].append(issue)

        for severity in [Severity.CRITICAL, Severity.WARNING, Severity.SUGGESTION]:
            items = grouped[severity]
            if not items:
                continue
            lines.append("")
            lines.append(f"  {severity.value} ({len(items)} 个)")
            lines.append("  " + "-" * 36)
            for i, issue in enumerate(items, 1):
                lines.append(f"    {i}. [{issue.rule_id}] 行 {issue.line}: {issue.message}")
                if issue.detail:
                    lines.append(f"       → {issue.detail}")

    lines.append("")

    # ── 复杂度分析 ──
    lines.append("─" * 40)
    lines.append("  🔄 复杂度分析（Top 10）")
    lines.append("─" * 40)

    sorted_funcs = sorted(report.stats.functions, key=lambda f: f.complexity, reverse=True)
    top_funcs = sorted_funcs[:10]

    if not top_funcs:
        lines.append("  未检测到函数定义")
    else:
        # 表头
        lines.append(f"  {'函数名':<30} {'复杂度':>6} {'行数':>6} {'等级':>6}")
        lines.append("  " + "-" * 52)

        for func in top_funcs:
            name = func.name
            if func.class_name:
                name = f"{func.class_name}.{name}"
            name_display = name[:28] + ".." if len(name) > 30 else name
            level = get_complexity_level(func.complexity)

            # 复杂度高的标记
            marker = ""
            if func.complexity > 20:
                marker = " ⚠️"
            elif func.complexity > 10:
                marker = " ⚡"

            lines.append(f"  {name_display:<30} {func.complexity:>6} {func.line_count:>6} {level:>4}{marker}")

    lines.append("")

    # ── 重复代码 ──
    if report.duplicates:
        lines.append("─" * 40)
        lines.append(f"  🔁 重复代码 ({len(report.duplicates)} 组)")
        lines.append("─" * 40)
        for i, dup in enumerate(report.duplicates, 1):
            lines.append(f"  {i}. 行 {dup.line_start_1}-{dup.line_end_1} ≈ 行 {dup.line_start_2}-{dup.line_end_2}  相似度 {dup.similarity:.0%}")
        lines.append("")

    # ── 总结 ──
    lines.append(sep)
    summary = _generate_summary(report)
    lines.append(f"  {summary}")
    lines.append(sep)

    return "\n".join(lines)


def _score_display(score: int) -> str:
    if score >= 90:
        return "🌟 优秀"
    elif score >= 75:
        return "✅ 良好"
    elif score >= 60:
        return "👌 一般"
    elif score >= 40:
        return "⚠️ 需改进"
    else:
        return "🔴 较差"


def _generate_summary(report: AnalysisReport) -> str:
    parts = []
    parts.append(f"评分 {report.score}/100")

    if report.critical_count:
        parts.append(f"严重问题 {report.critical_count} 个")
    if report.warning_count:
        parts.append(f"警告 {report.warning_count} 个")
    if report.suggestion_count:
        parts.append(f"建议 {report.suggestion_count} 个")
    if report.duplicates:
        parts.append(f"重复代码 {len(report.duplicates)} 组")

    high_complexity = [f for f in report.stats.functions if f.complexity > 10]
    if high_complexity:
        parts.append(f"高复杂度函数 {len(high_complexity)} 个")

    return " | ".join(parts)


def format_json(report: AnalysisReport) -> dict:
    """返回 JSON 友好的字典格式。"""
    import json

    return {
        "filename": report.filename,
        "score": report.score,
        "stats": {
            "total_lines": report.stats.total_lines,
            "code_lines": report.stats.code_lines,
            "comment_lines": report.stats.comment_lines,
            "blank_lines": report.stats.blank_lines,
            "function_count": report.stats.function_count,
            "class_count": report.stats.class_count,
        },
        "issues": [
            {
                "severity": issue.severity.value,
                "rule_id": issue.rule_id,
                "message": issue.message,
                "line": issue.line,
                "detail": issue.detail,
            }
            for issue in report.issues
        ],
        "top_complexity": [
            {
                "name": f"{f.class_name}.{f.name}" if f.class_name else f.name,
                "complexity": f.complexity,
                "lines": f.line_count,
            }
            for f in sorted(report.stats.functions, key=lambda f: f.complexity, reverse=True)[:10]
        ],
        "duplicates": [
            {
                "lines_1": f"{d.line_start_1}-{d.line_end_1}",
                "lines_2": f"{d.line_start_2}-{d.line_end_2}",
                "similarity": round(d.similarity, 2),
            }
            for d in report.duplicates
        ],
    }
