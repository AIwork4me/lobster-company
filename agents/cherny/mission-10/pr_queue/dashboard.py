"""P1: Review 积压看板。

提供只读 Web 页面和 JSON API，展示当前 Open PR 列表。
"""

import json
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from .models import PullRequest, Config
from .timeout_checker import get_wait_hours
from .quality_checker import check_review_quality


def _render_summary_row(open_prs: list[PullRequest], config: Config) -> str:
    """生成看板摘要统计行。"""
    from .quality_checker import check_review_quality
    timeout_count = sum(
        1 for p in open_prs if get_wait_hours(p) >= config.timeout_hours
    )
    rereview_count = sum(
        1 for p in open_prs if check_review_quality(p, config).needs_rereview
    )
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"<h1>🦞 PR Queue - Review 积压看板</h1>\n"
        f"<p class=\"info\">最后更新: {now_str} | 超时阈值: {config.timeout_hours}h</p>\n"
        f"<div class=\"summary\">\n"
        f"    <div class=\"stat\"><div class=\"stat-num\">{len(open_prs)}</div>"
        f"<div class=\"stat-label\">Open PR</div></div>\n"
        f"    <div class=\"stat\"><div class=\"stat-num\">{timeout_count}</div>"
        f"<div class=\"stat-label\">超时 PR</div></div>\n"
        f"    <div class=\"stat\"><div class=\"stat-num\">{rereview_count}</div>"
        f"<div class=\"stat-label\">需二次审查</div></div>\n"
        f"</div>"
    )


def _render_pr_row(pr: PullRequest, config: Config) -> str:
    """生成单个 PR 的表格行 HTML。"""
    from .quality_checker import check_review_quality
    hours = get_wait_hours(pr)
    result = check_review_quality(pr, config)
    risk_badge = ""
    if result.is_high_risk:
        risk_badge += '<span class="badge badge-risk">高风险</span> '
    if result.needs_rereview:
        risk_badge += '<span class="badge badge-warn">需二次审查</span> '
    if hours >= config.timeout_hours:
        risk_badge += '<span class="badge badge-timeout">超时</span>'

    reviewers_str = ", ".join(pr.reviewers) if pr.reviewers else "未指定"
    return (
        f"<tr><td>#{pr.number}</td><td>{pr.title}</td><td>{pr.author}</td>"
        f"<td>{pr.repo}</td><td>{hours:.1f}h</td><td>{reviewers_str}</td>"
        f"<td>{len(pr.changed_files)} 文件</td>"
        f"<td>+{pr.added_lines} -{pr.deleted_lines}</td>"
        f"<td>{risk_badge}</td></tr>"
    )


def _render_html(prs: list[PullRequest], config: Config) -> str:
    """生成看板 HTML 页面。"""
    open_prs = [pr for pr in prs if pr.is_open]
    open_prs.sort(key=lambda p: get_wait_hours(p), reverse=True)

    rows = "".join(_render_pr_row(pr, config) for pr in open_prs)
    summary = _render_summary_row(open_prs, config)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>PR Queue - Review 积压看板</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; background: #f5f5f5; }}
    h1 {{ color: #1a1a2e; }}
    .info {{ color: #666; margin-bottom: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #eee; }}
    th {{ background: #1a1a2e; color: white; font-weight: 600; }}
    tr:hover {{ background: #f9f9f9; }}
    .badge {{ padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
    .badge-risk {{ background: #fee2e2; color: #dc2626; }}
    .badge-warn {{ background: #fef3c7; color: #d97706; }}
    .badge-timeout {{ background: #dbeafe; color: #2563eb; }}
    .summary {{ margin-bottom: 1.5rem; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .stat {{ display: inline-block; margin-right: 2rem; }}
    .stat-num {{ font-size: 24px; font-weight: 700; color: #1a1a2e; }}
    .stat-label {{ font-size: 13px; color: #666; }}
</style>
</head>
<body>
{summary}
<table>
<tr><th>PR</th><th>标题</th><th>作者</th><th>仓库</th><th>等待</th><th>审查人</th><th>文件</th><th>变更</th><th>标签</th></tr>
{rows}
</table>
</body>
</html>"""


def _render_api(prs: list[PullRequest], config: Config) -> str:
    """生成 JSON API 响应。"""
    open_prs = [pr for pr in prs if pr.is_open]
    open_prs.sort(key=lambda p: get_wait_hours(p), reverse=True)

    result = []
    for pr in open_prs:
        hours = get_wait_hours(pr)
        quality = check_review_quality(pr, config)
        result.append({
            "number": pr.number,
            "title": pr.title,
            "author": pr.author,
            "repo": pr.repo,
            "wait_hours": round(hours, 1),
            "reviewers": pr.reviewers,
            "changed_file_count": len(pr.changed_files),
            "added_lines": pr.added_lines,
            "deleted_lines": pr.deleted_lines,
            "is_high_risk": quality.is_high_risk,
            "needs_rereview": quality.needs_rereview,
            "risk_dirs": quality.risk_dirs,
        })

    return json.dumps(result, ensure_ascii=False, indent=2)


def make_handler(prs: list[PullRequest], config: Config):
    """创建 HTTP 请求处理器工厂函数。"""

    class Handler(BaseHTTPRequestHandler):
        """看板 HTTP 请求处理器。"""

        def do_GET(self):
            if self.path == "/" or self.path == "/dashboard":
                content = _render_html(prs, config).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            elif self.path == "/api/prs":
                content = _render_api(prs, config).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Not Found")

        def log_message(self, format, *args):
            """静默 HTTP 日志。"""
            pass

    return Handler


def start_dashboard(
    prs: list[PullRequest],
    config: Config,
    host: str = "127.0.0.1",
    port: int = 8080,
) -> HTTPServer:
    """启动看板 HTTP 服务器。"""
    handler = make_handler(prs, config)
    server = HTTPServer((host, port), handler)
    return server
