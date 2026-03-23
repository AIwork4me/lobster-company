"""PR Queue 核心数据模型。

定义 PullRequest、Review、Comment、Config 等数据结构。
"""

from dataclasses import dataclass, field


@dataclass
class Review:
    """单条 Review 记录。"""
    reviewer: str
    state: str              # approved / changes_requested / commented
    body: str
    submitted_at: str       # ISO 8601 时间字符串


@dataclass
class PullRequest:
    """单个 Pull Request 数据。"""
    number: int
    title: str
    author: str
    repo: str
    state: str              # open / closed / merged
    created_at: str         # ISO 8601
    updated_at: str
    reviewers: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    changed_files: list = field(default_factory=list)
    added_lines: int = 0
    deleted_lines: int = 0
    reviews: list = field(default_factory=list)

    @property
    def total_changed_lines(self) -> int:
        """变更总行数。"""
        return self.added_lines + self.deleted_lines

    @property
    def is_open(self) -> bool:
        return self.state == "open"

    def to_dict(self) -> dict:
        """序列化为字典。"""
        return {
            "number": self.number,
            "title": self.title,
            "author": self.author,
            "repo": self.repo,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "reviewers": self.reviewers,
            "labels": self.labels,
            "changed_files": self.changed_files,
            "added_lines": self.added_lines,
            "deleted_lines": self.deleted_lines,
            "reviews": [
                {
                    "reviewer": r.reviewer,
                    "state": r.state,
                    "body": r.body,
                    "submitted_at": r.submitted_at,
                }
                for r in self.reviews
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PullRequest":
        """从字典反序列化。"""
        reviews = [
            Review(**r) for r in data.get("reviews", [])
        ]
        return cls(
            number=data["number"],
            title=data["title"],
            author=data["author"],
            repo=data["repo"],
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            reviewers=data.get("reviewers", []),
            labels=data.get("labels", []),
            changed_files=data.get("changed_files", []),
            added_lines=data.get("added_lines", 0),
            deleted_lines=data.get("deleted_lines", 0),
            reviews=reviews,
        )


@dataclass
class Config:
    """PR Queue 全局配置。"""
    timeout_hours: int = 24
    high_risk_dirs: list = field(default_factory=lambda: [
        "migration", "schema", "payment", "auth", "security",
    ])
    superficial_patterns: list = field(default_factory=lambda: [
        "LGTM", "看起来没问题", "👍", "+1", "looks good",
        "Looks good to me", "lgtm", "ok", "👍🏻",
    ])
    reviewer_rules: dict = field(default_factory=dict)
    webhook_url: str = ""
    tech_lead: str = ""
    repos: list = field(default_factory=list)
    large_change_threshold: int = 200

    def to_dict(self) -> dict:
        """序列化为字典。"""
        return {
            "timeout_hours": self.timeout_hours,
            "high_risk_dirs": self.high_risk_dirs,
            "superficial_patterns": self.superficial_patterns,
            "reviewer_rules": self.reviewer_rules,
            "webhook_url": self.webhook_url,
            "tech_lead": self.tech_lead,
            "repos": self.repos,
            "large_change_threshold": self.large_change_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """从字典反序列化，缺失字段使用默认值。"""
        defaults = cls()
        return cls(
            timeout_hours=data.get("timeout_hours", defaults.timeout_hours),
            high_risk_dirs=data.get("high_risk_dirs", defaults.high_risk_dirs),
            superficial_patterns=data.get(
                "superficial_patterns", defaults.superficial_patterns
            ),
            reviewer_rules=data.get("reviewer_rules", defaults.reviewer_rules),
            webhook_url=data.get("webhook_url", defaults.webhook_url),
            tech_lead=data.get("tech_lead", defaults.tech_lead),
            repos=data.get("repos", defaults.repos),
            large_change_threshold=data.get(
                "large_change_threshold", defaults.large_change_threshold
            ),
        )
