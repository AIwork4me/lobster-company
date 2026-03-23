"""Pipeline 框架 - 上下文模块。

提供 Stage 间数据传递的载体。Context 使用 key-value 字典存储，
保持最大灵活性，适应不同数据处理场景。
"""

from typing import Any
from copy import deepcopy


class Context:
    """Stage 间数据传递的载体。

    使用 key-value 字典存储数据，支持 get/set/has/remove 操作。
    提供 snapshot() 方法创建当前状态的深拷贝，用于调试和报告。
    """

    def __init__(self, data: dict | None = None) -> None:
        """初始化上下文。

        Args:
            data: 初始数据字典，默认为空。
        """
        self._data: dict[str, Any] = dict(data) if data else {}
        self.status = "active"

    def get(self, key: str, default: Any = None) -> Any:
        """获取值，不存在返回默认值。

        Args:
            key: 键名。
            default: 默认值，默认为 None。

        Returns:
            对应的值或默认值。
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置键值对。

        Args:
            key: 键名。
            value: 值。
        """
        self._data[key] = value

    def has(self, key: str) -> bool:
        """检查键是否存在。

        Args:
            key: 键名。

        Returns:
            键是否存在。
        """
        return key in self._data

    def remove(self, key: str) -> None:
        """移除键。不存在时静默。

        Args:
            key: 键名。
        """
        self._data.pop(key, None)

    def to_dict(self) -> dict:
        """导出为普通字典。

        Returns:
            数据的浅拷贝字典。
        """
        return dict(self._data)

    def snapshot(self) -> dict:
        """创建当前状态的深拷贝快照。

        Returns:
            数据的深拷贝字典，用于调试和报告。
        """
        return deepcopy(self._data)

    def __repr__(self) -> str:
        return f"Context(keys={list(self._data.keys())})"
