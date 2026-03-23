"""日志解析器 —— 从原始日志行中提取结构化信息

职责单一：只负责把一行日志文本变成一个 LogEntry 数据结构。
不关心统计、不关心报告，只管解析。
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# 日志时间模式：每项为 (正则表达式, 对应的时间格式列表)
# 将匹配模式和解析格式统一管理，消除两组列表的重复感
_TIMESTAMP_RULES = [
    # ISO 8601: 2026-03-22T09:00:00.123+08:00
    (
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?)",
        ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"],
    ),
    # 标准格式: 2026-03-22 09:00:00(.123)?
    (
        r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"],
    ),
    # 斜杠日期: 2026/03/22 09:00:00
    (
        r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})",
        ["%Y/%m/%d %H:%M:%S"],
    ),
    # nginx: 22/Mar/2026:09:00:00 +0800
    (
        r"(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s*[+-]\d{2}:?\d{2})",
        ["%d/%b/%Y:%H:%M:%S %z", "%d/%b/%Y:%H:%M:%S"],
    ),
    # syslog: Mar 22 09:00:00
    (
        r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
        ["%b %d %H:%M:%S"],
    ),
]

# 预编译正则+格式对
_COMPILED_TIMESTAMP_RULES = [
    (re.compile(pattern), formats)
    for pattern, formats in _TIMESTAMP_RULES
]

# 日志级别
LOG_LEVELS = ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "CRITICAL", "TRACE"]

# 预编译正则：提取日志级别
_LEVEL_PATTERN = re.compile(
    r"\b(" + "|".join(LOG_LEVELS) + r")\b", re.IGNORECASE
)


@dataclass
class LogEntry:
    """一条日志的结构化表示"""
    raw: str
    timestamp: Optional[datetime]
    level: str
    message: str
    line_number: int


def _extract_timestamp(line: str) -> Optional[datetime]:
    """从日志行中提取时间戳"""
    for pattern, formats in _COMPILED_TIMESTAMP_RULES:
        match = pattern.search(line)
        if not match:
            continue
        ts_str = match.group(1)
        # 依次尝试匹配的时间格式，ValueError 表示格式不兼容（预期行为）
        parsed = _try_parse_timestamp(ts_str, formats)
        if parsed is not None:
            return parsed
    return None


def _try_parse_timestamp(ts_str: str, formats: list) -> Optional[datetime]:
    """尝试用多种格式解析时间戳字符串，成功则返回 datetime"""
    for fmt in formats:
        parsed = _safe_strptime(ts_str, fmt)
        if parsed is not None:
            return parsed
    return None


def _safe_strptime(ts_str: str, fmt: str) -> Optional[datetime]:
    """安全的 strptime，格式不匹配时返回 None 而非抛出异常"""
    try:
        return datetime.strptime(ts_str, fmt)
    except ValueError:
        return None


def _extract_level(line: str) -> str:
    """从日志行中提取日志级别"""
    match = _LEVEL_PATTERN.search(line)
    if match:
        return match.group(1).upper()
    return "UNKNOWN"


def _extract_message(line: str) -> str:
    """提取日志消息部分（去掉时间戳和级别前缀）"""
    cleaned = line
    for pattern, _ in _COMPILED_TIMESTAMP_RULES:
        cleaned = pattern.sub("", cleaned, count=1)
    cleaned = _LEVEL_PATTERN.sub("", cleaned, count=1)
    cleaned = re.sub(r"^[\s\[\]|\\:\-]+", "", cleaned).strip()
    return cleaned or line.strip()


def parse_line(line: str, line_number: int = 0) -> LogEntry:
    """解析单行日志为结构化 LogEntry

    Args:
        line: 原始日志行
        line_number: 行号（从1开始）

    Returns:
        LogEntry 数据对象
    """
    line = line.rstrip("\n\r")
    timestamp = _extract_timestamp(line)
    level = _extract_level(line)
    message = _extract_message(line)
    return LogEntry(
        raw=line,
        timestamp=timestamp,
        level=level,
        message=message,
        line_number=line_number,
    )


def parse_file(file_path: str) -> list:
    """解析日志文件，返回 LogEntry 列表

    Args:
        file_path: 日志文件路径

    Returns:
        LogEntry 列表

    Raises:
        FileNotFoundError: 文件不存在
    """
    entries = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            if not line.strip():
                continue
            entries.append(parse_line(line, i))
    return entries
