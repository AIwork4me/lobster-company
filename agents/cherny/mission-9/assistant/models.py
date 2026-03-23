"""数据模型：Todo 和 Bookmark。"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List


@dataclass
class Todo:
    """待办事项模型。"""

    id: int
    content: str
    deadline: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    person: Optional[str] = None
    status: str = "pending"
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """序列化为字典（datetime 转字符串）。"""
        d = asdict(self)
        if self.deadline is not None:
            d["deadline"] = self.deadline.isoformat()
        d["created_at"] = self.created_at.isoformat()
        if self.completed_at is not None:
            d["completed_at"] = self.completed_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Todo":
        """从字典反序列化。"""
        if d.get("deadline") is not None:
            d["deadline"] = datetime.fromisoformat(d["deadline"])
        if d.get("created_at") is not None:
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        if d.get("completed_at") is not None:
            d["completed_at"] = datetime.fromisoformat(d["completed_at"])
        return cls(**d)


@dataclass
class Bookmark:
    """信息收藏模型。"""

    id: int
    content: str
    url: Optional[str] = None
    category: str = "未分类"
    created_at: datetime = field(default_factory=datetime.now)
    remind_at: Optional[datetime] = None
    reviewed: bool = False

    def to_dict(self) -> dict:
        """序列化为字典（datetime 转字符串）。"""
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        if self.remind_at is not None:
            d["remind_at"] = self.remind_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Bookmark":
        """从字典反序列化。"""
        if d.get("created_at") is not None:
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        if d.get("remind_at") is not None:
            d["remind_at"] = datetime.fromisoformat(d["remind_at"])
        return cls(**d)
