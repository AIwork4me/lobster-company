"""Agent Memory Manager - 轻量级记忆管理器 CLI 工具"""

import argparse
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows 终端 UTF-8 输出支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DEFAULT_FILE = Path(__file__).parent / "memory.json"

TZ = timezone(timedelta(hours=8))


def _load(filepath: Path) -> tuple[list, dict]:
    """从 JSON 文件加载数据，返回 (memories, meta)。
    meta 中保存 next_id 计数器，确保删除后 ID 不复用。"""
    if not filepath.exists():
        return [], {"next_id": 1}
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("memories", []), {"next_id": data.get("next_id", 1)}
    # 兼容旧版纯列表格式
    memories = data
    nid = (max(m["id"] for m in memories) + 1) if memories else 1
    return memories, {"next_id": nid}


def _save(filepath: Path, memories: list, meta: dict) -> None:
    """将记忆列表和元数据保存到 JSON 文件。"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"memories": memories, "next_id": meta["next_id"]}, f, ensure_ascii=False, indent=2)


def _next_id(meta: dict) -> int:
    """获取下一条记忆的自增 ID 并更新计数器。"""
    nid = meta["next_id"]
    meta["next_id"] = nid + 1
    return nid


def _now() -> str:
    """返回当前时间的 ISO 格式字符串。"""
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")


def add_memory(filepath: Path, content: str, tags: list[str]) -> dict:
    """添加一条新记忆，返回新记忆条目。"""
    memories, meta = _load(filepath)
    entry = {
        "id": _next_id(meta),
        "content": content,
        "tags": tags,
        "created_at": _now(),
        "updated_at": _now(),
    }
    memories.append(entry)
    _save(filepath, memories, meta)
    return entry


def list_memories(filepath: Path, tag: str = None, limit: int = None) -> list[dict]:
    """列出记忆条目，支持按标签过滤和数量限制。"""
    memories, _ = _load(filepath)
    if tag:
        memories = [m for m in memories if tag in m.get("tags", [])]
    # 按 id 倒序（最新的在前）
    memories.sort(key=lambda m: m["id"], reverse=True)
    if limit and limit > 0:
        memories = memories[:limit]
    return memories


def search_memories(filepath: Path, keyword: str) -> list[dict]:
    """搜索记忆条目，在 content 中匹配关键词。"""
    memories, _ = _load(filepath)
    kw_lower = keyword.lower()
    return [m for m in memories if kw_lower in m["content"].lower()]


def delete_memory(filepath: Path, memory_id: int) -> bool:
    """删除指定 ID 的记忆条目，成功返回 True。"""
    memories, meta = _load(filepath)
    new_memories = [m for m in memories if m["id"] != memory_id]
    if len(new_memories) == len(memories):
        return False
    _save(filepath, new_memories, meta)
    return True


def get_stats(filepath: Path) -> dict:
    """返回统计信息：总条数、标签分布、最近7天新增。"""
    memories, _ = _load(filepath)
    total = len(memories)
    # 标签分布
    tag_dist: dict[str, int] = {}
    for m in memories:
        for t in m.get("tags", []):
            tag_dist[t] = tag_dist.get(t, 0) + 1
    # 最近7天新增
    seven_days_ago = datetime.now(TZ) - timedelta(days=7)
    recent = 0
    for m in memories:
        created = datetime.strptime(m["created_at"], "%Y-%m-%d %H:%M:%S")
        created = created.replace(tzinfo=TZ)
        if created >= seven_days_ago:
            recent += 1
    return {"total": total, "tag_distribution": tag_dist, "recent_7_days": recent}


def _format_entry(m: dict) -> str:
    """格式化单条记忆用于终端输出。"""
    tags = ", ".join(m.get("tags", []))
    return f"  [{m['id']}] {m['content']}\n      tags: {tags} | created: {m['created_at']}"


def main():
    parser = argparse.ArgumentParser(description="Agent Memory Manager")
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="添加一条新记忆")
    p_add.add_argument("--content", "-c", required=True, help="记忆内容")
    p_add.add_argument("--tags", "-t", default="", help="标签，逗号分隔")

    # list
    p_list = sub.add_parser("list", help="列出记忆条目")
    p_list.add_argument("--tag", default=None, help="按标签过滤")
    p_list.add_argument("--limit", "-n", type=int, default=None, help="返回条数上限")

    # search
    p_search = sub.add_parser("search", help="搜索记忆")
    p_search.add_argument("keyword", help="搜索关键词")

    # delete
    p_del = sub.add_parser("delete", help="删除记忆")
    p_del.add_argument("id", type=int, help="要删除的记忆 ID")

    # stats
    sub.add_parser("stats", help="显示统计信息")

    args = parser.parse_args()

    if args.command == "add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        entry = add_memory(DEFAULT_FILE, args.content, tags)
        print(f"✅ 已添加记忆 [ID: {entry['id']}]")

    elif args.command == "list":
        results = list_memories(DEFAULT_FILE, args.tag, args.limit)
        if not results:
            print("📭 没有找到记忆条目")
        else:
            print(f"📋 找到 {len(results)} 条记忆：\n")
            for m in results:
                print(_format_entry(m))

    elif args.command == "search":
        results = search_memories(DEFAULT_FILE, args.keyword)
        if not results:
            print(f"🔍 未找到包含「{args.keyword}」的记忆")
        else:
            print(f"🔍 找到 {len(results)} 条匹配记忆：\n")
            for m in results:
                print(_format_entry(m))

    elif args.command == "delete":
        if delete_memory(DEFAULT_FILE, args.id):
            print(f"🗑️ 已删除记忆 [ID: {args.id}]")
        else:
            print(f"❌ 未找到 ID 为 {args.id} 的记忆")

    elif args.command == "stats":
        stats = get_stats(DEFAULT_FILE)
        print("📊 记忆统计信息")
        print(f"  总条数: {stats['total']}")
        print(f"  最近7天新增: {stats['recent_7_days']}")
        if stats["tag_distribution"]:
            print("  标签分布:")
            for tag, count in sorted(stats["tag_distribution"].items(), key=lambda x: -x[1]):
                print(f"    {tag}: {count}")
        else:
            print("  标签分布: (无)")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
