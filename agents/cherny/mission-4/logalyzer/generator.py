"""模拟日志生成器 —— 用于 demo 和测试

生成逼真的模拟服务日志，包含多种级别、时间分布、
ERROR 峰值、时间间隔异常等场景。
"""

import os
import random
from datetime import datetime, timedelta


# 模拟的日志消息模板
_TEMPLATES = {
    "INFO": [
        "Request processed successfully in {ms}ms",
        "User {user} logged in from {ip}",
        "Cache hit for key {key}",
        "Database query completed in {ms}ms",
        "Health check passed",
        "Scheduled task {task} started",
        "Message published to topic {topic}",
        "Connection pool status: {n}/{max} active",
        "API response: {status} for /api/{endpoint}",
        "Background job {job} completed in {ms}ms",
    ],
    "DEBUG": [
        "SQL query: SELECT * FROM {table} WHERE id = {n}",
        "Request headers: Content-Type={ctype}",
        "Cache miss for key {key}, fetching from DB",
        "WebSocket connection established from {ip}",
        "Retry attempt {n} for operation {op}",
        "Parsing config file {path}",
    ],
    "WARN": [
        "Slow query detected: {ms}ms for {table}",
        "Connection pool near capacity: {n}/{max}",
        "Rate limit approaching for client {ip}",
        "Deprecated API endpoint /api/{endpoint} called",
        "Memory usage at {pct}%",
        "Certificate expiring in {n} days",
    ],
    "ERROR": [
        "Connection refused to database at {ip}:{port}",
        "Failed to process request: timeout after {ms}ms",
        "NullPointerException in UserService.{method}",
        "Authentication failed for user {user} from {ip}",
        "Disk space critical: {pct}% used on /data",
        "API call to {service} returned status {status}",
        "File not found: {path}",
        "OutOfMemoryError: Java heap space",
        "HTTP 503 from upstream server at {ip}",
        "SSL handshake failed with {ip}",
    ],
    "FATAL": [
        "Cannot connect to primary database, shutting down",
        "Unrecoverable error in message broker, halting",
    ],
}

_USERS = ["admin", "alice", "bob", "charlie", "dave", "eve", "frank"]
_IPS = ["192.168.1.10", "192.168.1.20", "10.0.0.1", "10.0.0.5",
        "172.16.0.1", "172.16.0.100"]
_TABLES = ["users", "orders", "products", "sessions", "logs", "payments"]
_SERVICES = ["auth-service", "payment-gateway", "notification-svc", "cache-svc"]
_ENDPOINTS = ["users", "orders", "products", "auth", "health", "metrics"]
_TASKS = ["cleanup", "backup", "sync", "report", "index"]


def _fill_template(template: str) -> str:
    """填充模板中的占位符"""
    result = template
    result = result.replace("{ms}", str(random.randint(1, 5000)))
    result = result.replace("{user}", random.choice(_USERS))
    result = result.replace("{ip}", random.choice(_IPS))
    result = result.replace("{key}", f"cache:{random.choice(_TABLES)}:{random.randint(1, 9999)}")
    result = result.replace("{table}", random.choice(_TABLES))
    result = result.replace("{n}", str(random.randint(1, 1000)))
    result = result.replace("{max}", "100")
    result = result.replace("{topic}", random.choice(["events", "alerts", "metrics"]))
    result = result.replace("{endpoint}", random.choice(_ENDPOINTS))
    result = result.replace("{task}", random.choice(_TASKS))
    result = result.replace("{job}", random.choice(_TASKS))
    result = result.replace("{status}", str(random.choice([200, 201, 404, 500, 503])))
    result = result.replace("{method}", random.choice(["login", "createOrder", "getProfile"]))
    result = result.replace("{pct}", str(random.randint(70, 98)))
    result = result.replace("{port}", str(random.choice([5432, 3306, 6379, 9200])))
    result = result.replace("{service}", random.choice(_SERVICES))
    result = result.replace("{path}", f"/var/log/{random.choice(_TASKS)}.log")
    result = result.replace("{ctype}", "application/json")
    result = result.replace("{op}", random.choice(["write", "read", "delete"]))
    return result


def generate_log(
    output_path: str,
    total_lines: int = 5000,
    hours: int = 24,
    error_spike_hour: int = 14,
    gap_start_hour: int = 3,
    gap_duration: float = 0.5,
    seed: int = 42,
) -> str:
    """生成模拟日志文件

    模拟场景：
    - 正常流量波动（白天高、夜间低）
    - 下午2点 ERROR 峰值（数据库故障模拟）
    - 凌晨3点日志空窗期（服务重启）
    - 各级别日志按真实比例分布

    Args:
        output_path: 输出文件路径
        total_lines: 总日志行数
        hours: 模拟时长（小时）
        error_spike_hour: ERROR 峰值所在小时
        gap_start_hour: 空窗期开始小时
        gap_duration: 空窗期时长（小时）
        seed: 随机种子

    Returns:
        输出文件路径
    """
    random.seed(seed)

    base_time = datetime(2026, 3, 22, 0, 0, 0)
    lines = []
    current_time = base_time

    # 第一步：计算每小时权重
    weights = []
    for h in range(hours):
        hour_of_day = h % 24
        if 8 <= hour_of_day <= 22:
            weight = 1.0
        else:
            weight = 0.3
        if hour_of_day == error_spike_hour:
            weight *= 1.5
        if gap_start_hour <= hour_of_day < gap_start_hour + gap_duration:
            weight *= 0.05
        weights.append(weight)

    # 第二步：按权重分配行数
    total_weight = sum(weights)
    quotas = []
    allocated = 0
    for i in range(hours - 1):
        q = max(1, round(total_lines * weights[i] / total_weight))
        quotas.append(q)
        allocated += q
    quotas.append(max(1, total_lines - allocated))

    # 第三步：生成日志
    hour_start = base_time
    for h in range(hours):
        hour_of_day = h % 24
        count = quotas[h]
        current_time = hour_start
        is_gap = gap_start_hour <= hour_of_day < gap_start_hour + gap_duration

        if is_gap:
            for _ in range(count):
                current_time += timedelta(seconds=random.randint(30, 120))
                lines.append(_make_line(current_time, "INFO", "System idle"))
            hour_start += timedelta(hours=1)
            continue

        for _ in range(count):
            interval = max(1, 3600 // max(1, count))
            current_time += timedelta(seconds=random.randint(1, max(2, interval)))

            # 确定日志级别
            if hour_of_day == error_spike_hour and random.random() < 0.4:
                level = "ERROR"
            else:
                r = random.random()
                if r < 0.10:
                    level = "DEBUG"
                elif r < 0.70:
                    level = "INFO"
                elif r < 0.90:
                    level = "WARN"
                elif r < 0.99:
                    level = "ERROR"
                else:
                    level = "FATAL"

            template = random.choice(_TEMPLATES[level])
            message = _fill_template(template)
            lines.append(_make_line(current_time, level, message))

        hour_start += timedelta(hours=1)

    # 写入文件
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

    return output_path


def _make_line(timestamp: datetime, level: str, message: str) -> str:
    """格式化单行日志"""
    ts = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{ts}] [{level}] {message}"
