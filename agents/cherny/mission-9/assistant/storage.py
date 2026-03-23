"""JSON 文件持久化层。"""

import json
from pathlib import Path
from typing import List, Any

from . import config


def _todos_file() -> Path:
    return config.TODOS_FILE


def _bookmarks_file() -> Path:
    return config.BOOKMARKS_FILE


def load_json(filepath: Path) -> List[dict]:
    """加载 JSON 文件，返回列表。文件不存在返回空列表。"""
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return [data] if data else []
    except (json.JSONDecodeError, OSError):
        return []


def save_json(filepath: Path, data: List[Any]) -> None:
    """保存数据到 JSON 文件。自动创建父目录。"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_todos() -> List[dict]:
    """加载待办数据。"""
    return load_json(_todos_file())


def save_todos(data: List[dict]) -> None:
    """保存待办数据。"""
    save_json(_todos_file(), data)


def load_bookmarks() -> List[dict]:
    """加载收藏数据。"""
    return load_json(_bookmarks_file())


def save_bookmarks(data: List[dict]) -> None:
    """保存收藏数据。"""
    save_json(_bookmarks_file(), data)
