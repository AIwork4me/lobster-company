"""P0: 审查质量检测模块。

检测无实质内容的 Approval（"走过场式 Review"），
结合变更文件路径和代码行数评估风险等级。
"""

import re
from dataclasses import dataclass
from .models import PullRequest, Config, Review


@dataclass
class QualityResult:
    """审查质量检测结果。"""
    pr: PullRequest
    is_superficial: bool          # 是否存在走过场式 Review
    superficial_reviews: list     # 走过场的 Review 列表
    is_high_risk: bool            # 变更是否涉及高风险目录
    risk_dirs: list               # 匹配到的高风险目录
    is_large_change: bool         # 是否大变更
    needs_rereview: bool          # 是否需要二次审查
    reason: str                   # 判定理由


def is_superficial_review(review: Review, config: Config) -> bool:
    """判断单条 Review 是否为走过场式审查。

    条件：Review 状态为 approved 且内容匹配表面审查模式。
    """
    if review.state != "approved":
        return False

    body = review.body.strip()
    if not body:
        return True  # 空内容的 Approval 也是走过场

    body_lower = body.lower()
    for pattern in config.superficial_patterns:
        if pattern.lower() in body_lower:
            return True

    return False


def find_high_risk_dirs(pr: PullRequest, config: Config) -> list[str]:
    """找出变更文件中涉及的高风险目录。"""
    matched = set()
    for filepath in pr.changed_files:
        parts = filepath.replace("\\", "/").split("/")
        for part in parts:
            if part.lower() in [d.lower() for d in config.high_risk_dirs]:
                matched.add(part.lower())
    return sorted(matched)


def is_large_change(pr: PullRequest, config: Config) -> bool:
    """判断变更规模是否过大。"""
    return pr.total_changed_lines > config.large_change_threshold


def check_review_quality(pr: PullRequest, config: Config) -> QualityResult:
    """对单个 PR 进行审查质量检测。

    判定需要二次审查的条件（满足任一即标记）：
    1. 存在走过场式 Review 且涉及高风险目录
    2. 存在走过场式 Review 且变更超过阈值行数
    3. 涉及高风险目录且无任何 Review
    """
    superficial_reviews = [
        r for r in pr.reviews if is_superficial_review(r, config)
    ]
    has_approved = any(r.state == "approved" for r in pr.reviews)

    is_superficial = len(superficial_reviews) > 0
    risk_dirs = find_high_risk_dirs(pr, config)
    is_high_risk = len(risk_dirs) > 0
    large = is_large_change(pr, config)

    reasons = []
    needs_rereview = False

    if is_superficial and is_high_risk:
        needs_rereview = True
        reasons.append("走过场式 Approval + 高风险目录")
    elif is_superficial and large:
        needs_rereview = True
        reasons.append("走过场式 Approval + 大规模变更")
    elif is_high_risk and not has_approved and pr.is_open:
        needs_rereview = True
        reasons.append("高风险目录变更无 Review")

    return QualityResult(
        pr=pr,
        is_superficial=is_superficial,
        superficial_reviews=superficial_reviews,
        is_high_risk=is_high_risk,
        risk_dirs=risk_dirs,
        is_large_change=large,
        needs_rereview=needs_rereview,
        reason="; ".join(reasons) if reasons else "审查正常",
    )


def check_all_reviews(
    prs: list[PullRequest], config: Config
) -> list[QualityResult]:
    """批量检测所有 PR 的审查质量。"""
    return [check_review_quality(pr, config) for pr in prs]


def format_quality_alert(result: QualityResult) -> str:
    """格式化审查质量警告消息。"""
    pr = result.pr
    return (
        f"🔴 审查质量警告\n"
        f"PR #{pr.number}: {pr.title}\n"
        f"作者: {pr.author}\n"
        f"仓库: {pr.repo}\n"
        f"变更行数: +{pr.added_lines} -{pr.deleted_lines}\n"
        f"高风险目录: {', '.join(result.risk_dirs) or '无'}\n"
        f"判定: {result.reason}\n"
        f"建议: 需要 Tech Lead 进行二次审查"
    )
