"""报告生成器 —— 将分析结果格式化为可读报告

职责：接收统计数据，输出格式化的文本报告。
支持终端彩色输出和纯文本输出。
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional, List

from logalyzer.analyzer import _level_sort_key, LevelDistribution, HourlyTrend, AnomalyResult

# 终端颜色（仅 Windows 10+ 和现代终端支持）
_COLORS = {
    "reset": "\033[0m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}

_LEVEL_COLORS = {
    "ERROR": "red",
    "FATAL": "red",
    "CRITICAL": "red",
    "WARN": "yellow",
    "WARNING": "yellow",
    "INFO": "green",
    "DEBUG": "cyan",
    "TRACE": "dim",
    "UNKNOWN": "dim",
}

_SEVERITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢"}


@dataclass
class ReportInput:
    """报告输入数据封装——将 format_report 的多个参数收敛为一个对象"""
    file_path: str
    level_dist: LevelDistribution
    hourly_trend: HourlyTrend
    anomaly_result: AnomalyResult
    top_errors: list
    keyword: Optional[str] = None
    keyword_matches: Optional[list] = None


def _enabled() -> bool:
    """检测终端是否支持颜色"""
    return (
        hasattr(sys.stdout, "isatty")
        and sys.stdout.isatty()
        and os.environ.get("NO_COLOR") is None
    )


def _bar(count: int, max_count: int, width: int = 30) -> str:
    """生成水平条形图"""
    if max_count <= 0:
        return ""
    filled = round(count / max_count * width)
    return "█" * filled + "░" * (width - filled)


def _colorize(text: str, color_name: str, use_color: bool) -> str:
    """条件着色：use_color 为 True 时才添加颜色"""
    if not use_color:
        return text
    code = _COLORS.get(color_name, "")
    if not code:
        return text
    return f"{code}{text}{_COLORS['reset']}"


def _section_header(title: str, use_color: bool) -> str:
    """生成章节标题"""
    line = "=" * 60
    bold_line = _colorize(line, "bold", use_color)
    return f"\n{bold_line}\n  {title}\n{bold_line}"


def _severity_text(severity: str) -> str:
    """将严重程度转为带图标的文字"""
    icon = _SEVERITY_ICONS.get(severity, "⚪")
    label = {"high": "严重", "medium": "中等", "low": "轻微"}.get(severity, severity)
    return f"{icon} {label}"


def _format_level_distribution(dist: LevelDistribution, use_color: bool) -> str:
    """格式化日志级别分布章节"""
    lines = [_section_header("📊 日志级别分布", use_color)]
    if not dist.counts:
        lines.append("  (无数据)")
        return "\n".join(lines)

    max_count = max(dist.counts.values())
    sorted_levels = sorted(
        dist.counts.items(),
        key=lambda x: _level_sort_key(x[0]),
        reverse=True,
    )
    for level, count in sorted_levels:
        pct = dist.percentages.get(level, 0)
        color = _LEVEL_COLORS.get(level, "reset")
        bar_str = _colorize(_bar(count, max_count), color, use_color)
        count_str = _colorize(f"{count:>6}", color, use_color)
        lines.append(
            f"  {level:<10} {count_str:>8} 条  {pct:>5.1f}%  {bar_str}"
        )
    return "\n".join(lines)


def _format_hourly_trend(trend: HourlyTrend, use_color: bool) -> str:
    """格式化每小时日志量趋势章节"""
    lines = [_section_header("📈 每小时日志量趋势", use_color)]
    if not trend.hourly_counts:
        lines.append("  (无时间戳数据)")
        return "\n".join(lines)

    max_count = max(trend.hourly_counts.values())
    for hour_key in sorted(trend.hourly_counts.keys()):
        count = trend.hourly_counts[hour_key]
        bar_str = _bar(count, max_count)
        short_hour = hour_key.split(" ")[-1] if " " in hour_key else hour_key
        lines.append(f"  {short_hour}  {count:>5} 条  {bar_str}")

    lines.append("")
    lines.append(
        f"  🔥 高峰: {_colorize(trend.peak_hour, 'red', use_color)} "
        f"({_colorize(str(trend.peak_count), 'red', use_color)} 条)"
    )
    lines.append(
        f"  💤 低谷: {_colorize(trend.quiet_hour, 'cyan', use_color)} "
        f"({_colorize(str(trend.quiet_count), 'cyan', use_color)} 条)"
    )
    return "\n".join(lines)


def _format_anomalies(result: AnomalyResult, use_color: bool) -> str:
    """格式化异常检测章节"""
    lines = [_section_header("⚠️  异常检测", use_color)]
    if not result.anomalies:
        lines.append(_colorize("  ✅ 未检测到异常，系统运行平稳", "green", use_color))
        return "\n".join(lines)

    lines.append(f"  检测到 {_colorize(str(len(result.anomalies)), 'yellow', use_color)} 个异常")
    lines.append("")
    for anomaly in result.anomalies:
        sev = _severity_text(anomaly.severity)
        color = {"high": "red", "medium": "yellow", "low": "green"}.get(
            anomaly.severity, "reset"
        )
        lines.append(f"  {_colorize(sev, color, use_color)}  {anomaly.description}")
    return "\n".join(lines)


def _format_top_errors(top_errors: list, use_color: bool) -> str:
    """格式化 Top N 高频错误章节"""
    lines = [_section_header("🔥 Top 10 高频错误", use_color)]
    if not top_errors:
        lines.append("  (无 ERROR 级别日志)")
        return "\n".join(lines)

    for i, (msg, count, line_no) in enumerate(top_errors, 1):
        display_msg = msg[:70] + "..." if len(msg) > 70 else msg
        num_str = _colorize(f"#{i}", "yellow", use_color)
        count_str = _colorize(f"{count}次", "red", use_color)
        lines.append(f"  {num_str}  {count_str:>6}  L{line_no:<5}  {display_msg}")
    return "\n".join(lines)


def _format_keyword_search(keyword: Optional[str], matches: Optional[list], use_color: bool) -> str:
    """格式化关键词搜索章节（无关键词时返回空字符串）"""
    if not keyword:
        return ""

    lines = [_section_header(f'🔍 关键词搜索: "{keyword}"', use_color)]

    if matches is None:
        lines.append("  (搜索结果为空)")
        return "\n".join(lines)

    lines.append(f"  匹配到 {_colorize(str(len(matches)), 'bold', use_color)} 条日志")
    display = matches[:20]
    for match in display:
        color = _LEVEL_COLORS.get(match.level, "reset")
        line_num = _colorize(f"L{match.line_number}", "dim", use_color)
        level_tag = _colorize(f"[{match.level}]", color, use_color)
        lines.append(f"  {line_num}  {level_tag}  {match.line[:100]}")
    if len(matches) > 20:
        lines.append(f"  ... 还有 {len(matches) - 20} 条未显示")

    return "\n".join(lines)


def format_report(
    data: ReportInput,
    use_color: bool = None,
) -> str:
    """生成完整的分析报告

    Args:
        data: ReportInput 包含所有分析数据
        use_color: 是否使用颜色（None=自动检测）

    Returns:
        格式化报告字符串
    """
    if use_color is None:
        use_color = _enabled()

    lines = []

    # 标题
    lines.append(_colorize("🦞 Lobster Logalyzer — 日志分析报告", "bold", use_color))
    lines.append(f"文件: {_colorize(data.file_path, 'blue', use_color)}")
    lines.append(f"总日志量: {_colorize(str(data.level_dist.total), 'bold', use_color)} 条")

    # 各章节
    lines.append(_format_level_distribution(data.level_dist, use_color))
    lines.append(_format_hourly_trend(data.hourly_trend, use_color))
    lines.append(_format_anomalies(data.anomaly_result, use_color))
    lines.append(_format_top_errors(data.top_errors, use_color))

    keyword_section = _format_keyword_search(data.keyword, data.keyword_matches, use_color)
    if keyword_section:
        lines.append(keyword_section)

    # 页脚
    lines.append("")
    lines.append(_colorize("=" * 60, "bold", use_color))
    lines.append(_colorize("报告生成完毕 — Lobster Logalyzer 🦞", "dim", use_color))
    lines.append("")

    return "\n".join(lines)
