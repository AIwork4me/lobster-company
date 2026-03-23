"""Deep Agent 代码质量分析器

分析 Python 文件的代码质量，输出结构化报告，包含：
- 代码质量评分（0-100）
- 问题列表（严重/警告/建议）
- 函数复杂度分析
- 代码统计
- 重复代码检测
"""

from .analyzer import analyze_file, analyze_source
from .report import AnalysisReport, format_report, format_json

__all__ = ["analyze_file", "analyze_source", "AnalysisReport", "format_report", "format_json"]
__version__ = "1.0.0"
