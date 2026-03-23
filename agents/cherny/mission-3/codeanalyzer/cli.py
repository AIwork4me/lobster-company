"""Deep Agent 代码质量分析器 - CLI 入口。

用法:
    python -m codeanalyzer <文件路径> [--json]
    python codeanalyzer/cli.py <文件路径> [--json]

示例:
    python -m codeanalyzer my_module.py
    python -m codeanalyzer my_module.py --json
"""

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze_file
from .report import format_report, format_json


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="codeanalyzer",
        description="Deep Agent 代码质量分析器 - 分析 Python 代码质量并输出结构化报告",
    )
    parser.add_argument("file", help="要分析的 Python 文件路径")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="以 JSON 格式输出报告")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args(argv)

    file_path = args.file

    # 如果没有 .py 后缀，尝试添加
    if not file_path.endswith('.py'):
        file_path = file_path + '.py'

    try:
        report = analyze_file(file_path)
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except SyntaxError as e:
        print(f"错误: 无法解析文件 - {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps(format_json(report), ensure_ascii=False, indent=2))
    else:
        print(format_report(report))

    # 如果有严重问题，返回非零退出码
    if report.critical_count > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
