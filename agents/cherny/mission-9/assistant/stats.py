"""数据统计：完成率、逾期率、标签分布。"""

from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

from .models import Todo


class WeeklyStats:
    """每周统计数据生成器。"""

    def __init__(self, todos: List[Todo]):
        self._todos = todos
        self._week_start = self._calc_week_start()

    @staticmethod
    def _calc_week_start() -> datetime:
        """计算本周一 00:00。"""
        now = datetime.now()
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)

    def _this_week_todos(self) -> List[Todo]:
        """获取本周创建的待办。"""
        return [t for t in self._todos if t.created_at >= self._week_start]

    def completion_rate(self) -> float:
        """本周待办完成率。"""
        week_todos = self._this_week_todos()
        if not week_todos:
            return 0.0
        completed = sum(1 for t in week_todos if t.status == "completed")
        return completed / len(week_todos) * 100

    def overdue_rate(self) -> float:
        """本周待办逾期率。"""
        week_todos = self._this_week_todos()
        pending = [t for t in week_todos if t.status == "pending"]
        if not pending:
            return 0.0
        now = datetime.now()
        overdue = sum(1 for t in pending if t.deadline and t.deadline < now)
        return overdue / len(pending) * 100

    def tag_distribution(self) -> Dict[str, int]:
        """标签分布统计。"""
        counter = Counter()
        for todo in self._todos:
            for tag in todo.tags:
                counter[tag] += 1
        return dict(counter.most_common())

    def daily_completion(self) -> Dict[str, int]:
        """每日完成数量（本周）。"""
        counter = Counter()
        week_todos = self._this_week_todos()
        for todo in week_todos:
            if todo.status == "completed" and todo.completed_at:
                day_str = todo.completed_at.strftime("%m-%d")
                counter[day_str] += 1
        return dict(counter)

    def summary(self) -> str:
        """生成统计报告文本。"""
        rate = self.completion_rate()
        overdue = self.overdue_rate()
        week_todos = self._this_week_todos()
        completed = sum(1 for t in week_todos if t.status == "completed")
        pending = sum(1 for t in week_todos if t.status == "pending")

        lines = [
            "📊 本周统计报告",
            "━" * 40,
            f"本周创建：{len(week_todos)} 项",
            f"已完成：{completed} 项",
            f"待处理：{pending} 项",
            f"完成率：{rate:.1f}%",
            f"逾期率：{overdue:.1f}%",
        ]

        # 标签分布
        tag_dist = self.tag_distribution()
        if tag_dist:
            lines.append("\n🏷️  标签分布：")
            for tag, count in tag_dist.items():
                lines.append(f"  {tag}：{count} 项")

        # 每日完成
        daily = self.daily_completion()
        if daily:
            lines.append("\n📅 每日完成：")
            for day, count in sorted(daily.items()):
                lines.append(f"  {day}：{count} 项")

        # 建议
        if rate < 60:
            lines.append("\n💡 建议：完成率偏低，试试减少每日待办数量，聚焦 3-5 件事")
        elif rate >= 80:
            lines.append("\n✨ 完成率很高，继续保持！")

        return "\n".join(lines)
