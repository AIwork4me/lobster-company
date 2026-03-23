# DESIGN.md - PR Queue 技术设计

## 一、产品理解

PR Queue 是一个 Code Review 流程管理工具，核心功能：
1. PR 等待超时自动催办（通过 Webhook 发通知）
2. 检测"走过场式"审查（LGTM 等无实质内容的 Approval）
3. Review 积压看板（只读 Web 页面）
4. 审查人轮值分配（按代码目录自动建议 Reviewer）
5. 每周审查报告（数据摘要）

目标用户：5-30 人技术团队的 Tech Lead。

## 二、技术选型

- **语言**：Python 3.13（标准库）
- **HTTP 服务**：`http.server`（Webhook 接收 + Dashboard）
- **数据存储**：JSON 文件（`json` 模块）
- **定时任务**：内部计时器 + `time.sleep` 轮询
- **通知发送**：`urllib.request` 调用 Slack/飞书 Webhook
- **HTML 生成**：字符串拼接（简单模板）
- **测试**：`unittest`

零外部依赖。

## 三、文件结构

```
mission-10/
├── DESIGN.md
├── pr_queue/
│   ├── __init__.py          # 包入口，导出版本号
│   ├── models.py            # 数据模型：PR, Review, Comment, Config
│   ├── config.py            # 配置加载/保存（JSON 格式）
│   ├── store.py             # PR 数据持久化（JSON 文件存储）
│   ├── timeout_checker.py   # P0: PR 超时检测
│   ├── quality_checker.py   # P0: 审查质量分析
│   ├── reviewer_router.py   # P1: 审查人轮值分配
│   ├── notifier.py          # Webhook 通知发送
│   ├── dashboard.py         # P1: Web 看板（HTTP Server）
│   ├── report.py            # P2: 每周报告生成
│   └── webhook_handler.py   # Webhook 事件接收与分发
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_config.py
│   ├── test_store.py
│   ├── test_timeout_checker.py
│   ├── test_quality_checker.py
│   ├── test_reviewer_router.py
│   ├── test_notifier.py
│   ├── test_report.py
│   └── test_dashboard.py
└── run_demo.py              # 演示脚本（模拟数据）
```

## 四、核心数据结构

### Config（配置）
```python
@dataclass
class Config:
    timeout_hours: int           # 超时阈值，默认 24
    high_risk_dirs: list[str]   # 高风险目录关键词
    superficial_patterns: list[str]  # 表面审查模式
    reviewer_rules: dict        # 目录→审查人映射
    webhook_url: str            # 通知 Webhook URL
    tech_lead: str              # Tech Lead 用户名
    repos: list[str]            # 监听的仓库列表
```

### PullRequest（PR 数据）
```python
@dataclass
class PullRequest:
    number: int
    title: str
    author: str
    repo: str
    state: str                 # open / closed / merged
    created_at: str            # ISO 8601
    updated_at: str
    reviewers: list[str]
    labels: list[str]
    changed_files: list[str]
    added_lines: int
    deleted_lines: int
    reviews: list[Review]
```

### Review（审查记录）
```python
@dataclass
class Review:
    reviewer: str
    state: str                 # approved / changes_requested / commented
    body: str
    submitted_at: str
```

## 五、功能实现方案

| 功能 | 优先级 | 实现方案 |
|------|--------|---------|
| PR 超时催办 | P0 | 比较当前时间与 PR 创建时间，超过阈值则构建通知消息并调用 Webhook |
| 审查质量标记 | P0 | 匹配评论内容与表面审查模式，结合变更文件路径检测高风险，标记 needs-rereview |
| Review 积压看板 | P1 | http.server 提供 HTML 页面，从 JSON 存储读取 PR 列表，按等待时长排序 |
| 审查人轮值分配 | P1 | 根据变更文件路径匹配 reviewer_rules，返回建议审查人列表 |
| 每周审查报告 | P2 | 聚合指定时间范围内的 PR 数据，计算统计指标，生成摘要文本 |

## 六、接口设计

### Webhook 接收端
- `POST /webhook` — 接收 GitHub/GitLab 风格的 PR 事件 payload
- 解析后更新本地 PR 存储，触发超时检查和质量检查

### Dashboard
- `GET /dashboard` — 返回 HTML 看板页面
- `GET /api/prs` — 返回 JSON 格式的 PR 列表（供前端查询）

### 通知
- `POST` 到配置的 Webhook URL，payload 为 JSON 格式的通知消息
