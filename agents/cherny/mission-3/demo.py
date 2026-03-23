"""Deep Agent 代码质量分析器 - Demo
用分析器分析自身的源码，展示工具能力。

用法: python demo.py
"""

import os
import sys
import io
from pathlib import Path

# Windows 环境强制 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 确保可以导入 codeanalyzer
sys.path.insert(0, str(Path(__file__).parent))

from codeanalyzer.analyzer import analyze_file
from codeanalyzer.report import format_report


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Deep Agent 代码质量分析器 - Demo                      ║")
    print("║  用分析器分析自身的源码                                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    analyzer_dir = Path(__file__).parent / "codeanalyzer"

    if not analyzer_dir.exists():
        print("错误: 找不到 codeanalyzer 目录")
        sys.exit(1)

    py_files = sorted(analyzer_dir.glob("*.py"))
    py_files = [f for f in py_files if f.name != "__pycache__"]

    if not py_files:
        print("错误: 没有找到 Python 文件")
        sys.exit(1)

    total_score = 0
    total_issues = 0
    analyzed_count = 0

    for filepath in py_files:
        try:
            report = analyze_file(str(filepath))
            print(format_report(report))
            print()

            total_score += report.score
            total_issues += len(report.issues)
            analyzed_count += 1
        except Exception as e:
            print(f"分析 {filepath.name} 时出错: {e}")
            print()

    # 总结
    if analyzed_count > 0:
        avg_score = round(total_score / analyzed_count)
        print("╔══════════════════════════════════════════════════════════╗")
        print(f"║  汇总: 分析了 {analyzed_count} 个文件                          ║")
        print(f"║  平均评分: {avg_score}/100                                      ║")
        print(f"║  总问题数: {total_issues}                                          ║")
        print("╚══════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
