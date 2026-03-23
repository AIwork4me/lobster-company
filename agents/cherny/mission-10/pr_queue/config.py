"""配置管理模块。

负责加载和保存 Config（JSON 格式）。
"""

import json
from pathlib import Path
from .models import Config


DEFAULT_CONFIG_FILENAME = "pr_queue_config.json"


def load_config(path: str = "") -> Config:
    """从 JSON 文件加载配置，文件不存在则返回默认配置。"""
    if not path:
        path = DEFAULT_CONFIG_FILENAME

    config_path = Path(path)
    if not config_path.exists():
        return Config()

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Config.from_dict(data)


def save_config(config: Config, path: str = "") -> None:
    """将配置保存到 JSON 文件。"""
    if not path:
        path = DEFAULT_CONFIG_FILENAME

    with open(path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
