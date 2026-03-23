"""logalyzer — 日志分析器 CLI

用法:
    python -m logalyzer <日志文件> [选项]

选项:
    --keyword, -k <关键词>    搜索包含指定关键词的日志行
    --no-color                禁用终端颜色
    --generate, -g <路径>     生成模拟日志文件
    --demo                    运行 demo（生成 + 分析模拟日志）

示例:
    python -m logalyzer server.log
    python -m logalyzer server.log -k timeout
    python -m logalyzer --generate demo.log
    python -m logalyzer --demo
"""

import argparse
import sys
import os

# 将当前包添加到 path（支持 -m 执行）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logalyzer.parser import parse_file
from logalyzer.analyzer import (
    compute_level_distribution,
    compute_hourly_trend,
    detect_anomalies,
    top_error_messages,
    search_keyword,
)
from logalyzer.report import format_report
from logalyzer.generator import generate_log


def main():
    parser = argparse.ArgumentParser(
        prog="logalyzer",
        description="🦞 Lobster Logalyzer — 快速日志分析工具",
        epilog="为运维同学设计的一键日志分析器",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="日志文件路径",
    )
    parser.add_argument(
        "--keyword", "-k",
        help="搜索指定关键词",
        default=None,
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="禁用终端颜色",
    )
    parser.add_argument(
        "--generate", "-g",
        metavar="PATH",
        help="生成模拟日志文件到指定路径",
        default=None,
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="运行完整 demo（生成 + 分析模拟日志）",
    )

    args = parser.parse_args()

    # Demo 模式
    if args.demo:
        demo_path = os.path.join(os.getcwd(), "demo_server.log")
        print(f"🔄 生成模拟日志 → {demo_path}")
        generate_log(demo_path, total_lines=5000)
        print(f"✅ 模拟日志生成完毕\n")
        args.file = demo_path
        args.keyword = "timeout"

    # 生成模式
    if args.generate:
        print(f"🔄 生成模拟日志 → {args.generate}")
        generate_log(args.generate, total_lines=5000)
        print(f"✅ 完成！用 logalyzer {args.generate} 分析")
        return

    # 分析模式
    if not args.file:
        parser.print_help()
        print("\n❌ 请指定日志文件路径，或使用 --demo 运行示例")
        sys.exit(1)

    file_path = args.file
    if not os.path.isfile(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    # 解析
    print(f"🔄 解析日志文件: {file_path}")
    entries = parse_file(file_path)

    if not entries:
        print("❌ 日志文件为空或无法解析")
        sys.exit(1)

    # 分析
    print("📊 分析中...")
    level_dist = compute_level_distribution(entries)
    hourly_trend = compute_hourly_trend(entries)
    anomaly_result = detect_anomalies(entries)
    top_errors = top_error_messages(entries)

    # 关键词搜索（可选）
    keyword_matches = None
    if args.keyword:
        keyword_matches = search_keyword(entries, args.keyword)

    # 生成报告
    from logalyzer.report import ReportInput

    report_data = ReportInput(
        file_path=file_path,
        level_dist=level_dist,
        hourly_trend=hourly_trend,
        anomaly_result=anomaly_result,
        top_errors=top_errors,
        keyword=args.keyword,
        keyword_matches=keyword_matches,
    )
    report = format_report(
        data=report_data,
        use_color=not args.no_color,
    )

    print(report)


if __name__ == "__main__":
    main()
