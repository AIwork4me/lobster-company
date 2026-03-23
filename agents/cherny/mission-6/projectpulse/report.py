"""Project Pulse - 报告格式化。

将扫描结果格式化为人类可读的报告。
"""

from .priority import prioritize_issues


def format_report(result):
    """生成完整的文本报告。

    Args:
        result: scan_project 的返回值

    Returns:
        str: 格式化的报告文本
    """
    sections = []
    sections.append(_format_header(result))
    sections.append(_format_issue_summary(result.get("issues", [])))
    sections.append(_format_top_files(result.get("top_files", [])))
    sections.append(_format_action_plan(result.get("issues", [])))
    return "\n".join(sections)


def format_compact(result):
    """生成紧凑版报告（适合 CI/CD 输出）。

    Args:
        result: scan_project 的返回值

    Returns:
        str: 紧凑的报告文本
    """
    issues = result.get("issues", [])
    sorted_issues = prioritize_issues(issues)

    counts = _count_by_type(sorted_issues)
    parts = [
        f"Project Pulse | Files: {result.get('total_files', 0)} | "
        f"Lines: {result.get('total_lines', 0)} | "
        f"Critical: {counts['critical']} | Warning: {counts['warning']} | "
        f"Info: {counts['info']}",
    ]

    if counts["critical"] > 0:
        parts.append(f"  TOP PRIORITY: Fix {counts['critical']} critical issue(s)")

    for issue in sorted_issues[:5]:
        parts.append(f"  [{issue['type'].upper()}] {issue['file']}: {issue['message']}")

    return "\n".join(parts)


def _count_by_type(issues):
    """按类型统计问题数量。"""
    counts = {"critical": 0, "warning": 0, "info": 0}
    for issue in issues:
        t = issue.get("type", "info")
        if t in counts:
            counts[t] += 1
    return counts


def _format_header(result):
    """格式化报告头部（项目概览）。"""
    lines = [
        "=" * 60,
        "  PROJECT PULSE - 项目健康诊断报告",
        "=" * 60,
        "",
        f"项目路径: {result.get('project_path', 'N/A')}",
        f"文件数量: {result.get('total_files', 0)}",
        f"总行数:   {result.get('total_lines', 0)}",
        f"代码行数: {result.get('total_code_lines', 0)}",
        f"平均文件行数: {result.get('avg_lines_per_file', 0)}",
        "",
    ]
    return "\n".join(lines)


def _format_issue_summary(issues):
    """格式化问题摘要。"""
    sorted_issues = prioritize_issues(issues)
    counts = _count_by_type(sorted_issues)

    critical = [i for i in sorted_issues if i["type"] == "critical"]
    warnings = [i for i in sorted_issues if i["type"] == "warning"]
    infos = [i for i in sorted_issues if i["type"] == "info"]

    lines = [
        "-" * 60,
        f"  问题统计: {counts['critical']} 严重 | {counts['warning']} 警告 | {counts['info']} 建议",
        "-" * 60,
        "",
    ]

    lines.extend(_format_issue_group("!!", "严重问题 (必须修复)", critical))
    lines.extend(_format_issue_group("!", "警告 (建议修复)", warnings))
    lines.extend(_format_info_group(infos))

    return "\n".join(lines)


def _format_issue_group(icon, title, issues):
    """格式化一个问题组。"""
    lines = []
    if not issues:
        return lines
    lines.append(f"[{icon}] {title}")
    for issue in issues:
        lines.append(f"  * {issue['file']}: {issue['message']}")
    lines.append("")
    return lines


def _format_info_group(infos):
    """格式化 info 级别的问题。"""
    if not infos:
        return []
    lines = ["[i]  建议 (可选改进)"]
    for issue in infos[:10]:
        lines.append(f"  * {issue['file']}: {issue['message']}")
    if len(infos) > 10:
        lines.append(f"  ... 还有 {len(infos) - 10} 条建议")
    lines.append("")
    return lines


def _format_top_files(top_files):
    """格式化最大文件列表。"""
    if not top_files:
        return ""
    lines = [
        "-" * 60,
        "  最大的 5 个文件",
        "-" * 60,
    ]
    for i, f in enumerate(top_files, 1):
        lines.append(
            f"  {i}. {f.get('path', '?')} ({f.get('total_lines', 0)} 行, "
            f"{f.get('function_count', 0)} 函数, {f.get('class_count', 0)} 类)"
        )
    lines.append("")
    return "\n".join(lines)


def _format_action_plan(issues):
    """格式化行动计划。"""
    counts = _count_by_type(issues)
    lines = [
        "=" * 60,
        "  建议行动计划",
        "=" * 60,
    ]

    steps = []
    if counts["critical"] > 0:
        steps.append("1. 优先修复严重问题（嵌套过深、函数过长）")
    if counts["warning"] > 0:
        num = len(steps) + 1
        steps.append(f"{num}. 审查警告问题，规划到下一个迭代")
    if counts["info"] > 0:
        num = len(steps) + 1
        steps.append(f"{num}. 逐步添加缺失的模块文档")

    if not steps:
        steps.append("项目状态良好，继续保持！")

    lines.extend(steps)
    lines.append("")
    return "\n".join(lines)
