"""Project Pulse - CLI 入口。

用法:
    python -m projectpulse <项目路径> [--compact] [--save] [--compare <旧快照>]
"""

import argparse
import sys

from .scanner import scan_project
from .report import format_report, format_compact
from .snapshot import save_snapshot, load_snapshot, compare_snapshots


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="projectpulse",
        description="Project Pulse - 项目健康诊断工具，一条命令了解项目代码质量",
    )
    parser.add_argument("path", help="项目根目录路径")
    parser.add_argument("--compact", action="store_true",
                        help="输出紧凑报告（适合 CI/CD）")
    parser.add_argument("--save", metavar="FILE",
                        help="保存快照到指定文件")
    parser.add_argument("--compare", metavar="OLD_SNAPSHOT",
                        help="与旧快照比较变化")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args(argv)

    result = _scan(args.path)

    _print_report(result, args.compact)
    _maybe_save_snapshot(result, args.save)
    _maybe_compare(result, args.compare)
    _set_exit_code(result)


def _scan(project_path):
    """执行项目扫描。"""
    try:
        return scan_project(project_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _print_report(result, compact):
    """输出报告。"""
    if compact:
        print(format_compact(result))
    else:
        print(format_report(result))


def _maybe_save_snapshot(result, save_path):
    """如果指定了 --save，保存快照。"""
    if not save_path:
        return
    save_snapshot(result, save_path)
    print(f"\nSnapshot saved to: {save_path}")


def _maybe_compare(result, old_snapshot_path):
    """如果指定了 --compare，比较快照。"""
    if not old_snapshot_path:
        return
    try:
        old = load_snapshot(old_snapshot_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    _print_comparison(compare_snapshots(old, result))


def _print_comparison(diff):
    """输出快照比较结果。"""
    print("\n--- Changes since last snapshot ---")
    print(f"Files added: {diff['files_added']}")
    print(f"Files removed: {diff['files_removed']}")
    print(f"Files modified: {diff['files_modified']}")
    print(f"Lines added: {diff['lines_added']}")
    if diff["file_changes"]:
        print("\nBiggest changes:")
        for c in diff["file_changes"][:5]:
            sign = "+" if c["lines_change"] > 0 else ""
            print(f"  {c['path']}: {sign}{c['lines_change']} lines")


def _set_exit_code(result):
    """根据问题严重程度设置退出码。"""
    critical = sum(1 for i in result["issues"] if i["type"] == "critical")
    warnings = sum(1 for i in result["issues"] if i["type"] == "warning")
    if critical > 0:
        sys.exit(2)
    elif warnings > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
