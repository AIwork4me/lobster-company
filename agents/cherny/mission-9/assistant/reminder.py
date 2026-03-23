"""每日待办摘要生成。"""

from datetime import datetime
from typing import List

from .models import Todo


def _format_deadline(todo: Todo) -> str:
    """格式化截止时间为友好文本。"""
    if todo.deadline is None:
        return "无截止时间"
    now = datetime.now()
    today = now.date()
    todo_date = todo.deadline.date()
    days_diff = (todo_date - today).days

    if days_diff < 0:
        return f"逾期 {abs(days_diff)} 天（{todo.deadline.strftime('%m/%d %H:%M')}）"
    if days_diff == 0:
        return f"今天 {todo.deadline.strftime('%H:%M')}"
    if days_diff == 1:
        return f"明天 {todo.deadline.strftime('%H:%M')}"
    if days_diff <= 7:
        return todo.deadline.strftime("%m/%d %H:%M")
    return todo.deadline.strftime("%Y/%m/%d %H:%M")


def _priority_label(priority: int) -> str:
    """将优先级数字转为标签。"""
    labels = {1: "🔴 紧急", 2: "🟠 高", 3: "🟡 中", 4: "🟢 低", 5: "⚪ 待定"}
    return labels.get(priority, "⚪ 待定")


def _format_todo_line(todo: Todo) -> str:
    """格式化单条待办。"""
    priority_tag = _priority_label(todo.priority)
    deadline_str = _format_deadline(todo)
    parts = [f"  {priority_tag} [#{todo.id}] {todo.content}"]
    parts.append(f"  截止：{deadline_str}")
    if todo.tags:
        parts.append(f"  标签：{'、'.join(todo.tags)}")
    if todo.person:
        parts.append(f"  关联人：{todo.person}")
    return "\n".join(parts)


def generate_daily_summary(todos: List[Todo]) -> str:
    """生成每日待办摘要。

    Args:
        todos: 待处理（pending）的待办列表

    Returns:
        格式化的摘要文本
    """
    if not todos:
        return "📋 今日无待办，享受轻松时光吧！"

    overdue = [t for t in todos if t.deadline and t.deadline < datetime.now()]
    today_due = [t for t in todos if t.deadline
                 and t.deadline.date() == datetime.now().date()]
    upcoming = [t for t in todos if t not in overdue and t not in today_due]

    lines = ["📋 今日待办摘要", "━" * 40]

    if overdue:
        lines.append(f"\n⚠️  已逾期（{len(overdue)}）：")
        for todo in overdue:
            lines.append(_format_todo_line(todo))

    if today_due:
        lines.append(f"\n🔴 今日截止（{len(today_due)}）：")
        for todo in today_due:
            lines.append(_format_todo_line(todo))

    if upcoming:
        lines.append(f"\n🟡 近期待办（{len(upcoming)}）：")
        for todo in upcoming:
            lines.append(_format_todo_line(todo))

    lines.append(f"\n💡 共 {len(todos)} 项待办，优先处理逾期和今日截止任务")

    return "\n".join(lines)
