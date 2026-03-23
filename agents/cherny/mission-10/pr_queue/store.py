"""PR 数据持久化模块。

使用 JSON 文件存储所有 PR 数据，支持增删改查。
"""

import json
from pathlib import Path
from typing import Optional
from .models import PullRequest


DEFAULT_STORE_FILENAME = "pr_queue_data.json"


class PRStore:
    """PR 数据存储。"""

    def __init__(self, path: str = ""):
        if not path:
            path = DEFAULT_STORE_FILENAME
        self._path = Path(path)

    def _load_all(self) -> dict[str, dict]:
        """加载全部数据，key 为 'repo:number'。"""
        if not self._path.exists():
            return {}
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_all(self, data: dict[str, dict]) -> None:
        """保存全部数据。"""
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _make_key(self, repo: str, number: int) -> str:
        return f"{repo}:{number}"

    def add(self, pr: PullRequest) -> None:
        """添加或更新一个 PR。"""
        data = self._load_all()
        key = self._make_key(pr.repo, pr.number)
        data[key] = pr.to_dict()
        self._save_all(data)

    def get(self, repo: str, number: int) -> Optional[PullRequest]:
        """获取单个 PR，不存在返回 None。"""
        data = self._load_all()
        key = self._make_key(repo, number)
        if key not in data:
            return None
        return PullRequest.from_dict(data[key])

    def get_all(self) -> list[PullRequest]:
        """获取所有 PR。"""
        data = self._load_all()
        prs = []
        for pr_data in data.values():
            prs.append(PullRequest.from_dict(pr_data))
        return prs

    def get_open_prs(self) -> list[PullRequest]:
        """获取所有 Open 状态的 PR。"""
        return [pr for pr in self.get_all() if pr.is_open]

    def get_by_repo(self, repo: str) -> list[PullRequest]:
        """获取指定仓库的所有 PR。"""
        return [pr for pr in self.get_all() if pr.repo == repo]

    def delete(self, repo: str, number: int) -> bool:
        """删除一个 PR，返回是否成功。"""
        data = self._load_all()
        key = self._make_key(repo, number)
        if key not in data:
            return False
        del data[key]
        self._save_all(data)
        return True

    def update_labels(self, repo: str, number: int, labels: list[str]) -> bool:
        """更新 PR 的标签列表。"""
        pr = self.get(repo, number)
        if pr is None:
            return False
        pr.labels = labels
        self.add(pr)
        return True
