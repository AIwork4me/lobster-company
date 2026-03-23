"""待办管理器：CRUD 操作 + 优先级自动计算。"""

from datetime import datetime
from typing import List, Optional

from .models import Todo
from .storage import load_todos, save_todos
from .config import (
    PRIORITY_OVERDUE, PRIORITY_TODAY, PRIORITY_WITHIN_3_DAYS,
    PRIORITY_THIS_WEEK, PRIORITY_NO_DEADLINE,
)


class TodoManager:
    """待办事项管理器。"""

    def __init__(self):
        self._todos: List[Todo] = []
        self._load()

    def _load(self) -> None:
        """从文件加载待办。"""
        data = load_todos()
        self._todos = [Todo.from_dict(d) for d in data]
        self._recalc_priorities()

    def _save(self) -> None:
        """保存待办到文件。"""
        save_todos([t.to_dict() for t in self._todos])

    def _next_id(self) -> int:
        """获取下一个可用 ID。"""
        if not self._todos:
            return 1
        return max(t.id for t in self._todos) + 1

    def _recalc_priorities(self) -> None:
        """重新计算所有待办的优先级。"""
        now = datetime.now()
        today = now.date()

        for todo in self._todos:
            if todo.status != "pending":
                continue
            todo.priority = self._calc_priority(todo, now, today)

    @staticmethod
    def _calc_priority(todo: Todo, now: datetime, today: datetime) -> int:
        """根据截止时间计算单个待办的优先级。"""
        if todo.deadline is None:
            return PRIORITY_NO_DEADLINE

        if todo.deadline < now:
            return PRIORITY_OVERDUE

        days_left = (todo.deadline.date() - today).days

        if days_left == 0:
            return PRIORITY_TODAY
        if days_left <= 3:
            return PRIORITY_WITHIN_3_DAYS
        if days_left <= 7:
            return PRIORITY_THIS_WEEK
        return PRIORITY_NO_DEADLINE

    def create(self, content: str, deadline: Optional[datetime] = None,
               tags: Optional[List[str]] = None,
               person: Optional[str] = None) -> Todo:
        """创建新待办。"""
        todo = Todo(
            id=self._next_id(),
            content=content,
            deadline=deadline,
            tags=tags or [],
            person=person,
            created_at=datetime.now(),
        )
        now = datetime.now()
        today = now.date()
        todo.priority = self._calc_priority(todo, now, today)
        self._todos.append(todo)
        self._save()
        return todo

    def list_pending(self) -> List[Todo]:
        """获取所有待处理的待办，按优先级排序。"""
        pending = [t for t in self._todos if t.status == "pending"]
        pending.sort(key=lambda t: (t.priority, t.created_at))
        return pending

    def list_all(self) -> List[Todo]:
        """获取所有待办（含已完成）。"""
        return sorted(self._todos, key=lambda t: (t.status != "completed", t.priority, t.created_at))

    def list_completed(self) -> List[Todo]:
        """获取已完成的待办。"""
        return [t for t in self._todos if t.status == "completed"]

    def complete(self, todo_id: Optional[int] = None,
                 content_match: Optional[str] = None) -> Optional[Todo]:
        """完成待办（通过 ID 或内容匹配）。"""
        todo = self._find(todo_id, content_match)
        if todo and todo.status == "pending":
            todo.status = "completed"
            todo.completed_at = datetime.now()
            self._save()
            return todo
        return None

    def delete(self, todo_id: Optional[int] = None,
               content_match: Optional[str] = None) -> bool:
        """删除待办（通过 ID 或内容匹配）。"""
        todo = self._find(todo_id, content_match)
        if todo:
            todo.status = "deleted"
            self._save()
            return True
        return False

    def get_by_id(self, todo_id: int) -> Optional[Todo]:
        """通过 ID 获取待办。"""
        for todo in self._todos:
            if todo.id == todo_id and todo.status != "deleted":
                return todo
        return None

    def search(self, keyword: str) -> List[Todo]:
        """搜索待办（内容模糊匹配）。"""
        return [t for t in self._todos
                if keyword in t.content and t.status != "deleted"]

    def get_due_today(self) -> List[Todo]:
        """获取今天到期的待办。"""
        now = datetime.now()
        today = now.date()
        return [t for t in self._todos
                if t.status == "pending"
                and t.deadline is not None
                and t.deadline.date() <= today]

    def get_overdue(self) -> List[Todo]:
        """获取已逾期的待办。"""
        now = datetime.now()
        return [t for t in self._todos
                if t.status == "pending"
                and t.deadline is not None
                and t.deadline < now]

    def count_by_status(self) -> dict:
        """按状态统计待办数量。"""
        counts = {"pending": 0, "completed": 0, "deleted": 0}
        for todo in self._todos:
            status = todo.status if todo.status in counts else "pending"
            counts[status] += 1
        return counts

    def _find(self, todo_id: Optional[int],
              content_match: Optional[str]) -> Optional[Todo]:
        """内部查找方法。"""
        if todo_id is not None:
            return self.get_by_id(todo_id)
        if content_match:
            for todo in self._todos:
                if (content_match in todo.content
                        and todo.status not in ("completed", "deleted")):
                    return todo
        return None
