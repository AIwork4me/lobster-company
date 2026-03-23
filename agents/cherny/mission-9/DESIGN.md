# 技术设计：AI 日常事务助手 MVP

## 1. 技术选型（纯 Python 标准库）

| 模块 | 标准库 | 用途 |
|------|--------|------|
| 数据持久化 | `json` | 待办和收藏的存储 |
| 日期时间 | `datetime` | 截止时间解析、优先级计算、统计 |
| 自然语言解析 | `re` + `dataclasses` | 意图识别、实体提取 |
| CLI 交互 | 内置 `input()`/`print()` | 对话循环 |
| 文件路径 | `pathlib` | 数据文件管理 |
| 测试 | `unittest` | 全功能覆盖测试 |

## 2. 模块/文件结构

```
mission-9/
├── DESIGN.md
├── assistant/
│   ├── __init__.py          # 包入口
│   ├── config.py            # 常量与路径配置
│   ├── models.py            # Todo、Bookmark 数据模型
│   ├── storage.py           # JSON 持久化层
│   ├── nlp.py               # 自然语言解析器（意图+实体提取）
│   ├── todo_manager.py      # 待办 CRUD + 优先级计算
│   ├── bookmark_manager.py  # 收藏 CRUD + 自动归类
│   ├── reminder.py          # 每日待办摘要生成
│   ├── stats.py             # 数据统计（完成率、逾期率）
│   └── cli.py               # 交互式 REPL 主循环
├── tests/
│   ├── __init__.py
│   ├── test_nlp.py          # NLP 解析测试
│   ├── test_models.py       # 模型测试
│   ├── test_storage.py      # 持久化测试
│   ├── test_todo_manager.py # 待办管理测试
│   ├── test_bookmark_manager.py  # 收藏管理测试
│   ├── test_reminder.py     # 提醒测试
│   ├── test_stats.py        # 统计测试
│   └── test_integration.py  # 集成测试（完整对话流程）
└── data/                    # 运行时数据（JSON 文件）
```

## 3. 核心数据结构

### Todo（待办）
```python
@dataclass
class Todo:
    id: int
    content: str              # 待办内容
    deadline: Optional[datetime]  # 截止时间
    tags: List[str]           # 标签
    person: Optional[str]     # 关联人
    status: str               # pending / completed / deleted
    priority: int             # 1(最高) ~ 5(最低)，自动计算
    created_at: datetime
    completed_at: Optional[datetime]
```

### Bookmark（收藏）
```python
@dataclass
class Bookmark:
    id: int
    content: str              # 描述
    url: Optional[str]        # 链接
    category: str             # 自动归类：待阅读/学习资料/工具推荐/未分类
    created_at: datetime
    remind_at: datetime       # 建议回顾时间
    reviewed: bool
```

## 4. 功能实现方案（一句话描述）

| PRD 功能 | 实现方式 |
|----------|----------|
| P0 对话式待办管理 | nlp.py 解析用户输入→提取意图+实体→todo_manager 执行 CRUD |
| P0 每日智能提醒 | reminder.py 从待办列表中筛选今日/逾期任务→按优先级排序→格式化输出 |
| P1 优先级自动排序 | 根据 deadline 距离 + 是否逾期 + 创建时间自动计算 1-5 优先级 |
| P1 信息快速收藏 | nlp.py 识别 URL/收藏意图→bookmark_manager 创建→关键词匹配自动归类 |
| P2 简单数据统计 | stats.py 遍历已完成/逾期待办→计算完成率/逾期率→按标签汇总 |

## 5. 关键设计决策

1. **纯规则 NLP，不调 LLM API**：受限于标准库，用正则+关键词匹配做意图识别和时间提取。能覆盖 80% 常见表达。
2. **优先级自动计算，不存储**：优先级根据 deadline 和创建时间实时计算，保证排序始终最新。
3. **JSON 文件持久化**：简单可靠，单人使用足够。每次操作即时写入，不丢失数据。
4. **自动归类用关键词匹配**：收藏时根据 URL 和文本中的关键词匹配分类，无法匹配则归为"未分类"。
5. **对话式 REPL**：输入自然语言→解析→执行→输出结果，循环运行直到用户退出。
