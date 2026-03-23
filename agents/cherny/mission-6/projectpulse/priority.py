"""Project Pulse - 问题优先级排序。

将扫描发现的问题按严重程度排序，帮助团队确定修复顺序。
"""

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def prioritize_issues(issues):
    """按严重程度对问题排序。

    Args:
        issues: 问题列表，每个问题包含 "type" 字段

    Returns:
        list[dict]: 按严重程度降序排列的问题列表
    """
    return sorted(issues, key=lambda x: SEVERITY_ORDER.get(x["type"], 99))
