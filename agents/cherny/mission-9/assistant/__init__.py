"""AI 日常事务助手 - 对话式待办管理与信息收藏工具。

面向 1-3 人小团队的创始人/自由职业者，
用自然语言管理待办、收藏信息、查看统计。
"""

from .todo_manager import TodoManager
from .bookmark_manager import BookmarkManager
from .reminder import generate_daily_summary
from .stats import WeeklyStats
from .nlp import parse_command, Command

__all__ = [
    "TodoManager",
    "BookmarkManager",
    "generate_daily_summary",
    "WeeklyStats",
    "parse_command",
    "Command",
]
