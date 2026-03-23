"""P2: 每周审查报告生成模块。

聚合指定时间范围内的 PR 数据，生成 Review 统计摘要。
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from .models import PullRequest, Config
from .timeout_checker import get_wait_hours, parse_iso_time
from .quality_checker import check_review_quality, is_superficial_review


@dataclass
class WeeklyStats:
    """每周审查统计数据。"""
    total_prs: int
    reviewed_prs: int
    avg_review_hours: float
    timeout_count: int
    superficial_count: int
    high_risk_count: int
    needs_rereview_count: int
    total_added_lines: int
    total_deleted_lines: int
    most_active_reviewer: str
    start_date: str
    end_date: str


def _get_week_range(now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """获取上周的时间范围（周一 00:00 到周日 23:59）。"""
    if now is None:
        now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    last_monday = now - timedelta(days=days_since_monday + 7)
    last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    last_sunday = last_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return last_monday, last_sunday


def _filter_prs_by_range(
    prs: list[PullRequest],
    start: datetime,
    end: datetime,
) -> list[PullRequest]:
    """筛选在指定时间范围内创建的 PR。"""
    result = []
    for pr in prs:
        try:
            created = parse_iso_time(pr.created_at)
            if start <= created <= end:
                result.append(pr)
        except (ValueError, IndexError):
            continue  # 无效时间格式，跳过此 PR
    return result


def _calc_avg_review_hours(prs: list[PullRequest]) -> float:
    """计算从 PR 创建到第一条 Review 的平均时长（小时）。"""
    review_hours = []
    for pr in prs:
        if not pr.reviews:
            continue
        created = parse_iso_time(pr.created_at)
        first_review = _get_first_review_time(pr.reviews)
        if first_review:
            hours = (first_review - created).total_seconds() / 3600
            review_hours.append(hours)
    return round(sum(review_hours) / len(review_hours), 1) if review_hours else 0


def _get_first_review_time(reviews: list) -> Optional[datetime]:
    """获取最早一条 Review 的时间。"""
    earliest = None
    for r in reviews:
        try:
            t = parse_iso_time(r.submitted_at)
            if earliest is None or t < earliest:
                earliest = t
        except (ValueError, IndexError):
            continue  # 无效时间格式，跳过此 Review
    return earliest


def _count_superficial_reviews(prs: list[PullRequest], config: Config) -> int:
    """统计走过场式 Review 次数。"""
    count = 0
    for pr in prs:
        for r in pr.reviews:
            if is_superficial_review(r, config):
                count += 1
    return count


def _find_most_active_reviewer(prs: list[PullRequest]) -> str:
    """找出 Review 次数最多的审查人。"""
    reviewer_counts = {}
    for pr in prs:
        for r in pr.reviews:
            reviewer_counts[r.reviewer] = reviewer_counts.get(r.reviewer, 0) + 1
    if not reviewer_counts:
        return "无"
    return max(reviewer_counts, key=reviewer_counts.get)


def generate_weekly_report(
    prs: list[PullRequest],
    config: Config,
    week_start: Optional[datetime] = None,
    week_end: Optional[datetime] = None,
) -> WeeklyStats:
    """生成每周审查统计数据。"""
    if week_start is None or week_end is None:
        week_start, week_end = _get_week_range()

    week_prs = _filter_prs_by_range(prs, week_start, week_end)

    quality_results = [check_review_quality(pr, config) for pr in week_prs]

    return WeeklyStats(
        total_prs=len(week_prs),
        reviewed_prs=sum(1 for p in week_prs if p.reviews),
        avg_review_hours=_calc_avg_review_hours(week_prs),
        timeout_count=sum(
            1 for p in week_prs if get_wait_hours(p) >= config.timeout_hours
        ),
        superficial_count=_count_superficial_reviews(week_prs, config),
        high_risk_count=sum(1 for q in quality_results if q.is_high_risk),
        needs_rereview_count=sum(1 for q in quality_results if q.needs_rereview),
        total_added_lines=sum(p.added_lines for p in week_prs),
        total_deleted_lines=sum(p.deleted_lines for p in week_prs),
        most_active_reviewer=_find_most_active_reviewer(week_prs),
        start_date=week_start.strftime("%Y-%m-%d"),
        end_date=week_end.strftime("%Y-%m-%d"),
    )


def format_weekly_report(stats: WeeklyStats) -> str:
    """将每周统计格式化为文本报告。"""
    return (
        f"📊 每周审查报告 ({stats.start_date} ~ {stats.end_date})\n"
        f"{'─' * 40}\n"
        f"📦 PR 总数: {stats.total_prs}\n"
        f"✅ 已审查: {stats.reviewed_prs}\n"
        f"⏱️ 平均 Review 时长: {stats.avg_review_hours}h\n"
        f"⚠️ 超时 PR: {stats.timeout_count}\n"
        f"🔴 走过场式 Review: {stats.superficial_count} 次\n"
        f"🟡 高风险 PR: {stats.high_risk_count}\n"
        f"🔁 需二次审查: {stats.needs_rereview_count}\n"
        f"📝 代码变更: +{stats.total_added_lines} -{stats.total_deleted_lines}\n"
        f"🏆 最活跃 Reviewer: {stats.most_active_reviewer}\n"
        f"{'─' * 40}"
    )
