"""Project Pulse - 项目扫描器。

扫描指定目录下的所有 Python 文件，收集指标并生成问题清单。
"""

import os
from pathlib import Path

from .metrics import compute_file_metrics


def scan_project(project_path):
    """扫描项目目录，收集所有 Python 文件的健康指标。

    Args:
        project_path: 项目根目录路径

    Returns:
        dict: 包含项目级统计和文件级详情的字典

    Raises:
        FileNotFoundError: 目录不存在
    """
    root = Path(project_path)
    if not root.is_dir():
        raise FileNotFoundError(f"Directory not found: {project_path}")

    py_files = sorted(root.rglob("*.py"))
    py_files = [f for f in py_files if "__pycache__" not in f.parts]

    file_results, total_lines, total_code_lines, issues = _scan_files(py_files, root)

    top_files = sorted(
        file_results, key=lambda x: x["total_lines"], reverse=True
    )[:5]

    num_files = len(file_results)
    avg_lines = total_lines / num_files if num_files > 0 else 0
    avg_code = total_code_lines / num_files if num_files > 0 else 0

    return {
        "project_path": str(root),
        "total_files": num_files,
        "total_lines": total_lines,
        "total_code_lines": total_code_lines,
        "avg_lines_per_file": round(avg_lines, 1),
        "avg_code_lines_per_file": round(avg_code, 1),
        "files": file_results,
        "top_files": top_files,
        "issues": issues,
    }


def _scan_files(py_files, root):
    """遍历所有 Python 文件，收集指标和问题。

    Returns:
        tuple: (file_results, total_lines, total_code_lines, issues)
    """
    file_results = []
    total_lines = 0
    total_code_lines = 0
    issues = []

    for fpath in py_files:
        metrics = compute_file_metrics(str(fpath))
        total_lines += metrics["total_lines"]
        total_code_lines += metrics["code_lines"]

        file_entry = _build_file_entry(fpath, root, metrics)
        file_results.append(file_entry)

        file_issues = _generate_issues(file_entry["path"], metrics)
        issues.extend(file_issues)

    return file_results, total_lines, total_code_lines, issues


def _build_file_entry(fpath, root, metrics):
    """从扫描结果构建文件条目字典。"""
    return {
        "path": str(fpath.relative_to(root)),
        "total_lines": metrics["total_lines"],
        "code_lines": metrics["code_lines"],
        "function_count": metrics["function_count"],
        "class_count": metrics["class_count"],
        "max_function_length": metrics["max_function_length"],
        "max_nesting_depth": metrics["max_nesting_depth"],
    }


def _add_issue(issues, file_path, issue_type, message):
    """添加一个问题到问题列表。"""
    issues.append({
        "file": file_path,
        "type": issue_type,
        "message": message,
    })


def _generate_issues(rel_path, metrics):
    """根据文件指标生成问题列表。

    Args:
        rel_path: 文件相对路径
        metrics: compute_file_metrics 的返回值

    Returns:
        list[dict]: 问题列表
    """
    issues = []

    depth = metrics["max_nesting_depth"]
    func_len = metrics["max_function_length"]
    total = metrics["total_lines"]

    # Critical: Deep nesting or very long functions
    if depth > 4:
        _add_issue(issues, rel_path, "critical",
                   f"Deep nesting (depth={depth}). "
                   "Refactor using early returns or extract sub-functions.")
    if func_len > 100:
        _add_issue(issues, rel_path, "critical",
                   f"Very long function ({func_len} lines). "
                   "Break into smaller, focused functions.")
    elif metrics["has_long_functions"]:
        _add_issue(issues, rel_path, "warning",
                   f"Long function ({func_len} lines). Consider splitting.")

    # Warning: Large file
    if total > 300:
        _add_issue(issues, rel_path, "warning",
                   f"Large file ({total} lines). Consider splitting into modules.")

    # Info: Missing docstring
    if not metrics["has_module_docstring"] and total > 0:
        _add_issue(issues, rel_path, "info", "Missing module docstring.")

    return issues
