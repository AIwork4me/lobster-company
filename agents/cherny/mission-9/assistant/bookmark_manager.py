"""信息收藏管理器：CRUD 操作 + 自动归类。"""

from datetime import datetime
from typing import List, Optional

from .models import Bookmark
from .storage import load_bookmarks, save_bookmarks
from .nlp import classify_content, extract_review_time


class BookmarkManager:
    """信息收藏管理器。"""

    def __init__(self):
        self._bookmarks: List[Bookmark] = []
        self._load()

    def _load(self) -> None:
        """从文件加载收藏。"""
        data = load_bookmarks()
        self._bookmarks = [Bookmark.from_dict(d) for d in data]

    def _save(self) -> None:
        """保存收藏到文件。"""
        save_bookmarks([b.to_dict() for b in self._bookmarks])

    def _next_id(self) -> int:
        """获取下一个可用 ID。"""
        if not self._bookmarks:
            return 1
        return max(b.id for b in self._bookmarks) + 1

    def create(self, content: str, url: Optional[str] = None,
               category: Optional[str] = None,
               original_text: str = "") -> Bookmark:
        """创建新收藏。

        Args:
            content: 收藏内容描述
            url: 链接（可选）
            category: 分类（可选，不传则自动归类）
            original_text: 原始文本（用于提取回顾时间）
        """
        if category is None:
            category = classify_content(content, url)

        remind_at = extract_review_time(original_text) if original_text else (
            datetime.now().replace(hour=9, minute=0)
        )
        remind_at = remind_at.replace(microsecond=0)

        bookmark = Bookmark(
            id=self._next_id(),
            content=content,
            url=url,
            category=category,
            created_at=datetime.now().replace(microsecond=0),
            remind_at=remind_at,
            reviewed=False,
        )
        self._bookmarks.append(bookmark)
        self._save()
        return bookmark

    def list_all(self) -> List[Bookmark]:
        """获取所有收藏，按创建时间倒序。"""
        return sorted(self._bookmarks, key=lambda b: b.created_at, reverse=True)

    def list_by_category(self, category: str) -> List[Bookmark]:
        """按分类获取收藏。"""
        return [b for b in self._bookmarks if b.category == category]

    def list_unreviewed(self) -> List[Bookmark]:
        """获取未回顾的收藏。"""
        return [b for b in self._bookmarks if not b.reviewed]

    def list_due_review(self) -> List[Bookmark]:
        """获取已到回顾时间且未回顾的收藏。"""
        now = datetime.now()
        return [b for b in self._bookmarks
                if not b.reviewed and b.remind_at and b.remind_at <= now]

    def mark_reviewed(self, bookmark_id: int) -> Optional[Bookmark]:
        """标记收藏为已回顾。"""
        for bookmark in self._bookmarks:
            if bookmark.id == bookmark_id:
                bookmark.reviewed = True
                self._save()
                return bookmark
        return None

    def delete(self, bookmark_id: int) -> bool:
        """删除收藏。"""
        before = len(self._bookmarks)
        self._bookmarks = [b for b in self._bookmarks if b.id != bookmark_id]
        if len(self._bookmarks) < before:
            self._save()
            return True
        return False

    def get_by_id(self, bookmark_id: int) -> Optional[Bookmark]:
        """通过 ID 获取收藏。"""
        for bookmark in self._bookmarks:
            if bookmark.id == bookmark_id:
                return bookmark
        return None

    def get_categories(self) -> List[str]:
        """获取所有分类列表。"""
        cats = set(b.category for b in self._bookmarks)
        return sorted(cats)
