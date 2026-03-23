"""P1: 审查人轮值分配模块。

根据代码目录与 Reviewer 的映射规则，为新 PR 建议审查人。
"""

from .models import PullRequest, Config


def match_reviewer_rules(
    changed_files: list[str], rules: dict[str, list[str]]
) -> list[str]:
    """根据变更文件路径匹配审查规则，返回建议的审查人列表。

    rules 格式: {"src/payment/**": ["alice", "bob"], "src/auth/": ["charlie"]}
    匹配逻辑: 规则中的目录路径是变更文件路径的前缀。
    """
    suggested = []
    matched_rules = set()

    for filepath in changed_files:
        normalized = filepath.replace("\\", "/")
        for rule_path, reviewers in rules.items():
            if rule_path in matched_rules:
                continue
            rule_dir = rule_path.rstrip("*").rstrip("/")
            if normalized.startswith(rule_dir + "/"):
                matched_rules.add(rule_dir)
                for r in reviewers:
                    if r not in suggested:
                        suggested.append(r)

    return suggested


def suggest_reviewers(pr: PullRequest, config: Config) -> list[str]:
    """为 PR 建议审查人。"""
    return match_reviewer_rules(pr.changed_files, config.reviewer_rules)


def format_reviewer_suggestion(pr: PullRequest, reviewers: list[str]) -> str:
    """格式化审查人建议消息。"""
    if not reviewers:
        return (
            f"ℹ️ PR #{pr.number} 未匹配到审查规则，请手动指定 Reviewer。"
        )

    mentions = " ".join(f"@{r}" for r in reviewers)
    return (
        f"📋 审查人分配建议\n"
        f"PR #{pr.number}: {pr.title}\n"
        f"变更目录涉及以下规则:\n"
        f"  建议审查人: {mentions}\n"
        f"请确认或调整。"
    )
