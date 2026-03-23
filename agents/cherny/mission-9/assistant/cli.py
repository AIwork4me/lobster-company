"""交互式 REPL 主循环。"""

from typing import Optional

from .todo_manager import TodoManager
from .bookmark_manager import BookmarkManager
from .reminder import generate_daily_summary
from .stats import WeeklyStats
from .nlp import parse_command, Command


class Assistant:
    """AI 日常事务助手 CLI。"""

    def __init__(self):
        self.todo_mgr = TodoManager()
        self.bookmark_mgr = BookmarkManager()

    def start(self) -> None:
        """启动交互循环。"""
        self._print_welcome()
        while True:
            try:
                user_input = input("\n你> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 再见！")
                break

            if not user_input:
                continue
            if user_input in ("退出", "quit", "exit", "bye"):
                print("👋 再见！")
                break

            response = self._handle_input(user_input)
            print(f"\n{response}")

    def _print_welcome(self) -> None:
        """显示欢迎信息。"""
        welcome = (
            "🦞 AI 日常事务助手\n"
            "━" * 40 + "\n"
            "输入自然语言即可管理待办和收藏信息\n"
            '输入「帮助」查看所有命令，「退出」结束'
        )
        print(welcome)

    def _handle_input(self, text: str) -> str:
        """处理用户输入，返回响应文本。"""
        cmd = parse_command(text)
        handlers = {
            "help": self._cmd_help,
            "create_todo": self._cmd_create_todo,
            "list_todos": self._cmd_list_todos,
            "daily_summary": self._cmd_daily_summary,
            "complete": self._cmd_complete,
            "delete": self._cmd_delete,
            "add_bookmark": self._cmd_add_bookmark,
            "list_bookmarks": self._cmd_list_bookmarks,
            "stats": self._cmd_stats,
        }
        handler = handlers.get(cmd.intent)
        if handler:
            return handler(cmd)
        return '🤔 抱歉，没有理解你的意思。输入「帮助」查看可用命令。'

    def _cmd_help(self, cmd: Command) -> str:
        """显示帮助信息。"""
        return (
            "📖 使用说明\n"
            "━" * 40 + "\n"
            "📋 待办管理：\n"
            '  「明天下午三点前把报价单发给张总」  → 创建待办\n'
            '  「今天有什么事」                     → 查看待办\n'
            '  「完成了 #3」或「做完了报价单」      → 完成待办\n'
            '  「删除 #3」或「删掉报价单」          → 删除待办\n'
            "\n📌 信息收藏：\n"
            '  「收藏这个 https://... 行业报告」     → 保存收藏\n'
            '  「待阅读」                           → 查看收藏\n'
            "\n📊 其他：\n"
            '  「统计」                             → 本周数据\n'
            '  「帮助」                             → 本说明\n'
            '  「退出」                             → 退出助手'
        )

    def _cmd_create_todo(self, cmd: Command) -> str:
        """创建待办。"""
        if not cmd.content:
            return "❌ 请告诉我你想创建什么待办。"

        todo = self.todo_mgr.create(
            content=cmd.content,
            deadline=cmd.deadline,
            tags=cmd.tags,
            person=cmd.person,
        )
        lines = [f"✅ 已创建待办：{todo.content}"]
        if todo.deadline:
            lines.append(f"   截止：{todo.deadline.strftime('%Y/%m/%d %H:%M')}")
        if todo.tags:
            lines.append(f"   标签：{'、'.join(todo.tags)}")
        if todo.person:
            lines.append(f"   关联人：{todo.person}")
        lines.append(f"   优先级：{self._priority_text(todo.priority)}")
        return "\n".join(lines)

    def _cmd_list_todos(self, cmd: Command) -> str:
        """列出待办。"""
        pending = self.todo_mgr.list_pending()
        if not pending:
            return "📋 暂无待办事项。"

        lines = [f"📋 待办列表（{len(pending)} 项）", "━" * 40]
        for i, todo in enumerate(pending, 1):
            priority = self._priority_text(todo.priority)
            line = f"  {i}. [#{todo.id}] {todo.content} ({priority})"
            if todo.deadline:
                line += f" 截止：{todo.deadline.strftime('%m/%d %H:%M')}"
            lines.append(line)
        return "\n".join(lines)

    def _cmd_daily_summary(self, cmd: Command) -> str:
        """每日摘要。"""
        pending = self.todo_mgr.list_pending()
        return generate_daily_summary(pending)

    def _cmd_complete(self, cmd: Command) -> str:
        """完成待办。"""
        todo = self.todo_mgr.complete(todo_id=cmd.todo_id, content_match=cmd.content)
        if todo:
            return f"✅ 已完成：{todo.content}"
        if cmd.content:
            return f"❌ 未找到匹配的待办：{cmd.content}"
        return '❌ 请指定要完成的待办（如「完成了 #3」或「做完了报价单」）。'

    def _cmd_delete(self, cmd: Command) -> str:
        """删除待办。"""
        ok = self.todo_mgr.delete(todo_id=cmd.todo_id, content_match=cmd.content)
        if ok:
            return "🗑️ 已删除。"
        if cmd.content:
            return f"❌ 未找到匹配的待办：{cmd.content}"
        return '❌ 请指定要删除的待办（如「删除 #3」或「删掉报价单」）。'

    def _cmd_add_bookmark(self, cmd: Command) -> str:
        """添加收藏。"""
        if not cmd.content and not cmd.url:
            return "❌ 请提供要收藏的内容或链接。"

        bookmark = self.bookmark_mgr.create(
            content=cmd.content or cmd.url or "",
            url=cmd.url,
            original_text=cmd.content,
        )
        lines = [f"📌 已收藏：{bookmark.content}"]
        if bookmark.url:
            lines.append(f"   链接：{bookmark.url}")
        lines.append(f"   分类：{bookmark.category}")
        lines.append(f"   建议回顾：{bookmark.remind_at.strftime('%Y/%m/%d %H:%M')}")
        return "\n".join(lines)

    def _cmd_list_bookmarks(self, cmd: Command) -> str:
        """列出收藏。"""
        bookmarks = self.bookmark_mgr.list_unreviewed()
        if not bookmarks:
            return "📭 暂无未回顾的收藏。"

        lines = [f"📌 待回顾收藏（{len(bookmarks)} 项）", "━" * 40]
        for i, bm in enumerate(bookmarks, 1):
            line = f"  {i}. [#{bm.id}] {bm.content}"
            if bm.url:
                truncated = bm.url[:40] + "..." if len(bm.url) > 40 else bm.url
                line += f" ({truncated})"
            line += f" [{bm.category}]"
            lines.append(line)
            lines.append(f"     回顾时间：{bm.remind_at.strftime('%m/%d %H:%M')}")
        return "\n".join(lines)

    def _cmd_stats(self, cmd: Command) -> str:
        """显示统计信息。"""
        all_todos = self.todo_mgr.list_all()
        stats = WeeklyStats(all_todos)
        return stats.summary()

    @staticmethod
    def _priority_text(priority: int) -> str:
        """优先级数字转中文。"""
        mapping = {1: "🔴 紧急", 2: "🟠 高", 3: "🟡 中", 4: "🟢 低", 5: "⚪ 待定"}
        return mapping.get(priority, "⚪ 待定")


def main():
    """CLI 入口。"""
    assistant = Assistant()
    assistant.start()


if __name__ == "__main__":
    main()
