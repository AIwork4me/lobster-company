"""P0: PR 超时检测模块。

检测 PR 等待时间是否超过配置的阈值。
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from .models import PullRequest, Config


def parse_iso_time(time_str: str) -> datetime:
    """解析 ISO 8601 时间字符串。"""
    # 支持 2026-03-22T10:00:00Z 和 2026-03-22T10:00:00+08:00
    time_str = time_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(time_str)
    except ValueError:
        # 回退：去掉时区部分再试
        if "+" in time_str:
            time_str = time_str[:time_str.rindex("+")]
        return datetime.fromisoformat(time_str).replace(tzinfo=timezone.utc)


def get_wait_hours(pr: PullRequest, now: Optional[datetime] = None) -> float:
    """计算 PR 已等待的小时数。"""
    created = parse_iso_time(pr.created_at)
    if now is None:
        now = datetime.now(timezone.utc)
    delta = now - created
    return delta.total_seconds() / 3600


def is_timeout(pr: PullRequest, config: Config, now: Optional[datetime] = None) -> bool:
    """判断 PR 是否超时。"""
    if not pr.is_open:
        return False
    return get_wait_hours(pr, now) >= config.timeout_hours


def get_timeout_prs(
    prs: list[PullRequest],
    config: Config,
    now: Optional[datetime] = None,
) -> list[tuple[PullRequest, float]]:
    """返回所有超时 PR 及其等待小时数，按等待时长降序。"""
    result = []
    for pr in prs:
        if is_timeout(pr, config, now):
            hours = get_wait_hours(pr, now)
            result.append((pr, hours))
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def format_timeout_message(pr: PullRequest, wait_hours: float) -> str:
    """格式化超时通知消息。"""
    file_list = ", ".join(pr.changed_files[:5])
    if len(pr.changed_files) > 5:
        file_list += f" 等 {len(pr.changed_files)} 个文件"

    return (
        f"⚠️ PR 超时提醒\n"
        f"PR #{pr.number} 等待 Review 已超过 {wait_hours:.1f}h\n"
        f"标题: {pr.title}\n"
        f"作者: {pr.author}\n"
        f"仓库: {pr.repo}\n"
        f"变更文件: {file_list}\n"
        f"请尽快处理！"
    )
