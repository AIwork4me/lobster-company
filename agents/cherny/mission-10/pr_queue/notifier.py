"""Webhook 通知发送模块。

通过 HTTP POST 将通知消息发送到 Slack/飞书 Webhook。
"""

import json
import urllib.request
import urllib.error
from typing import Optional


def send_webhook(url: str, message: str, dry_run: bool = False) -> bool:
    """发送消息到 Webhook URL。

    Args:
        url: Webhook URL（Slack 或飞书格式）。
        message: 纯文本消息内容。
        dry_run: 为 True 时只打印不实际发送。

    Returns:
        是否发送成功。
    """
    payload = json.dumps({"text": message}).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    if dry_run:
        return True

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except urllib.error.URLError:
        return False
    except Exception:
        return False


def send_slack_notification(url: str, message: str, dry_run: bool = False) -> bool:
    """发送 Slack 通知（兼容 Slack Webhook 格式）。"""
    return send_webhook(url, message, dry_run)


def send_feishu_notification(url: str, message: str, dry_run: bool = False) -> bool:
    """发送飞书通知（兼容飞书 Webhook 格式）。"""
    return send_webhook(url, message, dry_run)
