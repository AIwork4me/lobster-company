"""主分析模块 - 整合所有分析组件。"""

from pathlib import Path
from typing import Optional

from .stats import CodeStats, collect_stats
from .checks import Issue, run_checks
from .complexity import analyze_complexity
from .duplicates import DuplicateBlock, detect_duplicates
from .report import AnalysisReport, calculate_score, format_report, format_json


def analyze_file(file_path: str) -> AnalysisReport:
    """分析指定的 Python 文件，返回完整的分析报告。

    Args:
        file_path: Python 文件路径

    Returns:
        AnalysisReport: 包含评分、问题、复杂度等信息的分析报告

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件不是 Python 文件
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if path.suffix != '.py':
        raise ValueError(f"不是 Python 文件: {file_path}")

    source = path.read_text(encoding='utf-8')

    return analyze_source(source, path.name)


def analyze_source(source: str, filename: str = "<source>") -> AnalysisReport:
    """直接分析 Python 源代码字符串。

    Args:
        source: Python 源代码
        filename: 文件名（仅用于报告显示）

    Returns:
        AnalysisReport: 完整的分析报告
    """
    # 1. 基础统计
    stats = collect_stats(source)

    # 2. 问题检查
    issues = run_checks(source)

    # 3. 复杂度分析
    stats.functions = analyze_complexity(source, stats.functions)

    # 4. 重复代码检测
    duplicates = detect_duplicates(source)

    # 5. 计算评分
    score = calculate_score(stats, issues, duplicates)

    # 6. 生成报告
    report = AnalysisReport(
        filename=filename,
        score=score,
        stats=stats,
        issues=issues,
        duplicates=duplicates,
    )

    return report
