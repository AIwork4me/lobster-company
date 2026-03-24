"""扫描所有 pr_queue 代码文件并输出质量报告。"""
import sys
import os
from pathlib import Path

# 使用相对路径定位 mission-3 的 codeanalyzer
_this_dir = Path(__file__).resolve().parent
_mission3_dir = _this_dir.parent / "mission-3"
sys.path.insert(0, str(_mission3_dir))
os.environ["PYTHONIOENCODING"] = "utf-8"

# 修复 stdout 编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from codeanalyzer.cli import main

files = [
    "pr_queue/models.py",
    "pr_queue/config.py",
    "pr_queue/store.py",
    "pr_queue/timeout_checker.py",
    "pr_queue/quality_checker.py",
    "pr_queue/reviewer_router.py",
    "pr_queue/notifier.py",
    "pr_queue/dashboard.py",
    "pr_queue/report.py",
    "pr_queue/webhook_handler.py",
]

os.chdir(str(_this_dir))

for f in files:
    print(f"\n{'='*60}")
    print(f"📄 {f}")
    print(f"{'='*60}")
    try:
        main([f])
    except SystemExit:
        pass
