"""Project Pulse - 快照管理。

支持保存、加载和比较项目健康快照，追踪代码质量趋势。
"""

import json
import os
from datetime import datetime, timezone


def save_snapshot(data, file_path):
    """保存项目快照到 JSON 文件。

    Args:
        data: 快照数据字典
        file_path: 保存路径
    """
    # Add timestamp if not present
    if "timestamp" not in data:
        data["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    # Ensure directory exists
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_snapshot(file_path):
    """从 JSON 文件加载项目快照。

    Args:
        file_path: 快照文件路径

    Returns:
        dict: 快照数据

    Raises:
        FileNotFoundError: 文件不存在
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Snapshot not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_snapshots(old_snapshot, new_snapshot):
    """比较两个快照，返回变化摘要。

    Args:
        old_snapshot: 旧快照数据
        new_snapshot: 新快照数据

    Returns:
        dict: 变化摘要，包含文件增减、行数变化等
    """
    old_files = {f["path"]: f for f in old_snapshot.get("files", [])}
    new_files = {f["path"]: f for f in new_snapshot.get("files", [])}

    old_paths = set(old_files.keys())
    new_paths = set(new_files.keys())

    files_added = len(new_paths - old_paths)
    files_removed = len(old_paths - new_paths)
    files_modified = 0

    file_changes = []
    for path in sorted(new_paths & old_paths):
        old_lines = old_files[path].get("total_lines", 0)
        new_lines = new_files[path].get("total_lines", 0)
        change = new_lines - old_lines
        if change != 0:
            files_modified += 1
            file_changes.append({
                "path": path,
                "old_lines": old_lines,
                "new_lines": new_lines,
                "lines_change": change,
            })

    # Sort by absolute change descending
    file_changes.sort(key=lambda x: abs(x["lines_change"]), reverse=True)

    lines_added = new_snapshot.get("total_lines", 0) - old_snapshot.get("total_lines", 0)

    return {
        "old_timestamp": old_snapshot.get("timestamp", "unknown"),
        "new_timestamp": new_snapshot.get("timestamp", "unknown"),
        "files_added": files_added,
        "files_removed": files_removed,
        "files_modified": files_modified,
        "lines_added": lines_added,
        "file_changes": file_changes,
    }
