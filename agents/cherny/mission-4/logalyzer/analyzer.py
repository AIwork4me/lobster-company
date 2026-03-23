"""日志统计与分析 —— 核心分析引擎

职责：接收 LogEntry 列表，产出各类统计数据。
不关心数据从哪来（文件/流），不关心结果怎么展示。
"""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class LevelDistribution:
    """日志级别分布"""
    counts: dict = field(default_factory=dict)
    total: int = 0
    percentages: dict = field(default_factory=dict)


@dataclass
class HourlyTrend:
    """每小时日志量趋势"""
    hourly_counts: dict = field(default_factory=dict)  # hour_str -> count
    peak_hour: str = ""
    peak_count: int = 0
    quiet_hour: str = ""
    quiet_count: int = 0


@dataclass
class Anomaly:
    """检测到的异常"""
    anomaly_type: str  # "error_spike" | "gap" | "burst"
    description: str
    timestamp: Optional[str] = None
    severity: str = "medium"  # low | medium | high


@dataclass
class AnomalyResult:
    """异常检测结果"""
    anomalies: list = field(default_factory=list)
    error_spike_count: int = 0
    gap_count: int = 0
    burst_count: int = 0


@dataclass
class KeywordMatch:
    """关键词匹配结果"""
    line_number: int
    line: str
    level: str


def _level_sort_key(level: str) -> int:
    """日志级别排序权重（越高越严重）"""
    weights = {
        "DEBUG": 0, "TRACE": 0,
        "INFO": 1,
        "WARN": 2, "WARNING": 2,
        "ERROR": 3,
        "FATAL": 4, "CRITICAL": 4,
        "UNKNOWN": -1,
    }
    return weights.get(level.upper(), -1)


def _build_hourly_stats(entries: list) -> tuple:
    """按小时统计 ERROR 数量和总数量

    Args:
        entries: LogEntry 列表

    Returns:
        (hourly_errors, hourly_totals, timed_entries)
    """
    hourly_errors = defaultdict(int)
    hourly_totals = defaultdict(int)
    timed_entries = [e for e in entries if e.timestamp is not None]

    for entry in timed_entries:
        hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00")
        hourly_totals[hour_key] += 1
        if _level_sort_key(entry.level) >= 3:
            hourly_errors[hour_key] += 1

    return hourly_errors, hourly_totals, timed_entries


def _make_anomaly(anomaly_type: str, description: str,
                  timestamp: str, severity: str) -> Anomaly:
    """构造 Anomaly 对象的工厂方法，统一异常构造模式"""
    return Anomaly(
        anomaly_type=anomaly_type,
        description=description,
        timestamp=timestamp,
        severity=severity,
    )


def _calc_severity(metric, threshold, high_multiplier: float = 1.5) -> str:
    """根据指标是否超过阈值的倍数判断严重程度

    Args:
        metric: 当前值（如 count 或 z_score）
        threshold: 阈值
        high_multiplier: 超过阈值多少倍算 high

    Returns:
        "high" 或 "medium"
    """
    return "high" if metric >= threshold * high_multiplier else "medium"


def _detect_error_spikes(hourly_errors, spike_threshold) -> tuple:
    """检测 ERROR 峰值异常

    Args:
        hourly_errors: 每小时 ERROR 计数字典
        spike_threshold: ERROR 峰值倍数阈值

    Returns:
        (anomalies, spike_count)
    """
    anomalies = []
    spike_count = 0

    if not hourly_errors:
        return anomalies, spike_count

    avg_errors = sum(hourly_errors.values()) / len(hourly_errors)
    for hour_key, count in sorted(hourly_errors.items()):
        if avg_errors <= 0 or count < avg_errors * spike_threshold:
            continue
        sev = _calc_severity(count / avg_errors, spike_threshold)
        anomalies.append(_make_anomaly(
            "error_spike",
            f"ERROR 峰值: {hour_key} 出现 {count} 条错误 "
            f"(平均值 {avg_errors:.1f}, {count/avg_errors:.1f}x)",
            hour_key, sev,
        ))
        spike_count += 1

    return anomalies, spike_count


def _detect_time_gaps(timed_entries, gap_threshold_minutes) -> tuple:
    """检测时间间隔异常

    Args:
        timed_entries: 有时间戳的 LogEntry 列表（已预过滤）
        gap_threshold_minutes: 空窗期阈值（分钟）

    Returns:
        (anomalies, gap_count)
    """
    anomalies = []
    gap_count = 0

    sorted_entries = sorted(timed_entries, key=lambda e: e.timestamp)
    for i in range(1, len(sorted_entries)):
        gap = sorted_entries[i].timestamp - sorted_entries[i - 1].timestamp
        gap_minutes = gap.total_seconds() / 60
        if gap_minutes < gap_threshold_minutes:
            continue
        sev = _calc_severity(gap_minutes, gap_threshold_minutes, 2.0)
        ts_start = sorted_entries[i - 1].timestamp.strftime("%H:%M:%S")
        ts_end = sorted_entries[i].timestamp.strftime("%H:%M:%S")
        anomalies.append(_make_anomaly(
            "gap",
            f"日志空窗期: {ts_start} → {ts_end} "
            f"(间隔 {gap_minutes:.0f} 分钟)",
            ts_start, sev,
        ))
        gap_count += 1

    return anomalies, gap_count


def _detect_traffic_bursts(hourly_totals, burst_threshold) -> tuple:
    """检测突发流量异常（基于 Z-score）

    Args:
        hourly_totals: 每小时总日志量字典
        burst_threshold: Z-score 阈值

    Returns:
        (anomalies, burst_count)
    """
    anomalies = []
    burst_count = 0

    if not hourly_totals or len(hourly_totals) <= 1:
        return anomalies, burst_count

    avg_total = sum(hourly_totals.values()) / len(hourly_totals)
    std = math.sqrt(
        sum((c - avg_total) ** 2 for c in hourly_totals.values())
        / len(hourly_totals)
    )
    if std <= 0:
        return anomalies, burst_count

    for hour_key, count in sorted(hourly_totals.items()):
        z_score = (count - avg_total) / std
        if z_score < burst_threshold:
            continue
        sev = _calc_severity(z_score, burst_threshold)
        anomalies.append(_make_anomaly(
            "burst",
            f"突发流量: {hour_key} 日志量 {count} 条 "
            f"(均值 {avg_total:.1f}, Z-score {z_score:.1f})",
            hour_key, sev,
        ))
        burst_count += 1

    return anomalies, burst_count


def compute_level_distribution(entries: list) -> LevelDistribution:
    """统计日志级别分布

    Args:
        entries: LogEntry 列表

    Returns:
        LevelDistribution
    """
    counter = Counter(e.level for e in entries)
    total = sum(counter.values())
    percentages = {}
    if total > 0:
        for level, count in counter.items():
            percentages[level] = count / total * 100

    return LevelDistribution(
        counts=dict(counter),
        total=total,
        percentages=percentages,
    )


def compute_hourly_trend(entries: list) -> HourlyTrend:
    """计算每小时日志量趋势

    Args:
        entries: LogEntry 列表

    Returns:
        HourlyTrend
    """
    hourly = defaultdict(int)
    for entry in entries:
        if entry.timestamp is None:
            continue
        hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00")
        hourly[hour_key] += 1

    if not hourly:
        return HourlyTrend()

    peak_hour = max(hourly, key=hourly.get)
    quiet_hour = min(hourly, key=hourly.get)

    return HourlyTrend(
        hourly_counts=dict(hourly),
        peak_hour=peak_hour,
        peak_count=hourly[peak_hour],
        quiet_hour=quiet_hour,
        quiet_count=hourly[quiet_hour],
    )


def detect_anomalies(
    entries: list,
    spike_threshold: float = 3.0,
    gap_threshold_minutes: float = 30.0,
    burst_threshold: float = 5.0,
) -> AnomalyResult:
    """异常检测

    检测三类异常：
    1. ERROR 峰值：某小时的 ERROR 数量显著高于平均水平
    2. 时间间隔异常：日志中出现超过阈值的空窗期
    3. 突发流量：某小时的总日志量显著高于平均水平

    Args:
        entries: LogEntry 列表
        spike_threshold: ERROR 峰值倍数（默认3倍于平均）
        gap_threshold_minutes: 空窗期阈值（分钟）
        burst_threshold: 突发流量倍数（默认5倍于平均）

    Returns:
        AnomalyResult
    """
    hourly_errors, hourly_totals, timed_entries = _build_hourly_stats(entries)

    spike_anomalies, spike_count = _detect_error_spikes(hourly_errors, spike_threshold)
    gap_anomalies, gap_count = _detect_time_gaps(timed_entries, gap_threshold_minutes)
    burst_anomalies, burst_count = _detect_traffic_bursts(hourly_totals, burst_threshold)

    return AnomalyResult(
        anomalies=spike_anomalies + gap_anomalies + burst_anomalies,
        error_spike_count=spike_count,
        gap_count=gap_count,
        burst_count=burst_count,
    )


def _template_message(msg: str) -> str:
    """将日志消息模板化，替换动态内容为占位符"""
    t = re.sub(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "<IP>", msg)
    t = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[\.\d]*", "<TS>", t)
    t = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", t)
    t = re.sub(r"\b\d{4,}\b", "<N>", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def top_error_messages(entries: list, top_n: int = 10) -> list:
    """统计 Top N 高频错误消息

    对 ERROR 及以上级别的日志消息进行去重统计。
    去重策略：去除消息中的动态部分（数字、IP、路径参数等）。

    Args:
        entries: LogEntry 列表
        top_n: 返回前 N 条

    Returns:
        [(消息模板, 出现次数, 首次出现行号), ...]
    """
    error_entries = [
        e for e in entries if _level_sort_key(e.level) >= 3
    ]

    template_counter = Counter()
    template_first_line = {}

    for entry in error_entries:
        tpl = _template_message(entry.message)
        template_counter[tpl] += 1
        if tpl not in template_first_line:
            template_first_line[tpl] = entry.line_number

    return [
        (msg, count, template_first_line[msg])
        for msg, count in template_counter.most_common(top_n)
    ]


def search_keyword(entries: list, keyword: str, case_sensitive: bool = False) -> list:
    """关键词搜索

    Args:
        entries: LogEntry 列表
        keyword: 搜索关键词
        case_sensitive: 是否区分大小写

    Returns:
        KeywordMatch 列表
    """
    results = []
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(keyword), flags)

    for entry in entries:
        if pattern.search(entry.raw):
            results.append(KeywordMatch(
                line_number=entry.line_number,
                line=entry.raw[:200],
                level=entry.level,
            ))
    return results
