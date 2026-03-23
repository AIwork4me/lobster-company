"""Webhook 事件接收与分发模块。

解析 GitHub/GitLab 风格的 PR 事件 payload，更新本地存储并触发检查。
"""

from .models import PullRequest, Review, Config
from .store import PRStore
from .timeout_checker import is_timeout, format_timeout_message, get_wait_hours
from .quality_checker import check_review_quality, format_quality_alert
from .reviewer_router import suggest_reviewers, format_reviewer_suggestion
from .notifier import send_webhook


def parse_github_pr_payload(payload: dict) -> PullRequest:
    """解析 GitHub PR 事件 payload 为 PullRequest 对象。"""
    pr_data = payload.get("pull_request", {})
    reviews = []
    for r in pr_data.get("reviews", []):
        reviews.append(Review(
            reviewer=r.get("user", {}).get("login", ""),
            state=r.get("state", "commented").lower(),
            body=r.get("body", ""),
            submitted_at=r.get("submitted_at", ""),
        ))

    return PullRequest(
        number=pr_data.get("number", 0),
        title=pr_data.get("title", ""),
        author=pr_data.get("user", {}).get("login", ""),
        repo=payload.get("repository", {}).get("full_name", ""),
        state=pr_data.get("state", "open").lower(),
        created_at=pr_data.get("created_at", ""),
        updated_at=pr_data.get("updated_at", ""),
        reviewers=[r.get("login", "") for r in pr_data.get("requested_reviewers", [])],
        labels=[l.get("name", "") for l in pr_data.get("labels", [])],
        changed_files=pr_data.get("changed_files", []),
        added_lines=pr_data.get("additions", 0),
        deleted_lines=pr_data.get("deletions", 0),
        reviews=reviews,
    )


def handle_pr_event(
    payload: dict,
    store: PRStore,
    config: Config,
    dry_run: bool = False,
) -> list[str]:
    """处理 PR 事件，返回触发的通知消息列表。

    流程:
    1. 解析 payload 为 PullRequest
    2. 保存到 store
    3. 检查超时 → 发送催办通知
    4. 检查审查质量 → 发送质量警告
    5. 建议审查人（仅新 PR）
    """
    pr = parse_github_pr_payload(payload)
    store.add(pr)

    messages = []
    action = payload.get("action", "opened")

    # 超时检查
    if is_timeout(pr, config) and config.webhook_url:
        msg = format_timeout_message(pr, get_wait_hours(pr))
        send_webhook(config.webhook_url, msg, dry_run=dry_run)
        messages.append(msg)

    # 审查质量检查（当有新 Review 提交时）
    if action in ("submitted", "review_requested"):
        result = check_review_quality(pr, config)
        if result.needs_rereview and config.webhook_url:
            msg = format_quality_alert(result)
            send_webhook(config.webhook_url, msg, dry_run=dry_run)
            messages.append(msg)

    # 审查人建议（仅新 PR）
    if action == "opened" and config.reviewer_rules:
        suggested = suggest_reviewers(pr, config)
        if suggested:
            msg = format_reviewer_suggestion(pr, suggested)
            if config.webhook_url:
                send_webhook(config.webhook_url, msg, dry_run=dry_run)
            messages.append(msg)

    return messages
