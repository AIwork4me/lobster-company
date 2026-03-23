# Deep Agent 框架架构设计

> 架构师：Steinberger | 日期：2026-03-22 | 版本：1.0

---

## 一、背景与目标

澳龙公司正在构建 Deep Agent —— 一款通用 AI Agent 系统（对标 OpenClaw / Cursor Agent）。本文档定义其核心框架的模块化架构。

**核心需求**：
1. 支持多种任务类型（代码生成、数据分析、网页操作、文档处理等）
2. 工具（Tools）的动态注册和发现
3. 多轮对话的上下文管理
4. Agent 的自我反思和纠错能力
5. 任务拆解和子任务编排

**设计原则**：
- 架构为业务服务，不为炫技
- 简单方案优于复杂方案
- 先够用再扩展，每个设计决策必须回答"解决了什么问题"

---

## 二、L1 概念架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Deep Agent Framework                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │   Agent Core  │    │  Orchestrator │    │  Tool Registry    │  │
│  │              │    │              │    │                   │  │
│  │ · LLM 调用   │◄──►│ · 任务拆解   │◄──►│ · 工具注册/发现   │  │
│  │ · 推理循环   │    │ · 子任务编排 │    │ · Schema 验证    │  │
│  │ · Token 管理 │    │ · DAG 执行   │    │ · 权限控制       │  │
│  └──────┬───────┘    └──────┬───────┘    └─────────┬─────────┘  │
│         │                   │                      │            │
│  ┌──────┴───────────────────┴──────────────────────┴─────────┐  │
│  │                     Session Manager                        │  │
│  │                     · 多轮对话上下文                        │  │
│  │                     · 记忆（短期 / 长期）                   │  │
│  │                     · 消息历史压缩                         │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                      Reflection Engine                    │  │
│  │                      · 结果评估                            │  │
│  │                      · 错误诊断                            │  │
│  │                      · 策略调整                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                      Adapters (可插拔)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ LLM      │  │ 代码生成 │  │ 数据分析 │  │ 文档处理 │ ...   │
│  │ Provider │  │ Adapter  │  │ Adapter  │  │ Adapter  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                      I/O Layer                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ CLI      │  │ HTTP API │  │ IDE 插件  │ ...                │
│  └──────────┘  └──────────┘  └──────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

**一句话总结**：Agent Core 负责思考和调用 LLM，Orchestrator 负责编排任务，Tool Registry 管理工具，Session Manager 管理上下文，Reflection Engine 提供自我纠错能力。Adapters 层实现具体任务类型，I/O Layer 负责用户交互。

---

## 三、核心模块划分

| # | 模块 | 职责（一句话） |
|---|------|--------------|
| 1 | **Agent Core** | 管理 LLM 调用循环，将推理转化为行动（工具调用 / 文本输出） |
| 2 | **Orchestrator** | 将用户任务拆解为子任务，按 DAG 依赖关系编排执行 |
| 3 | **Tool Registry** | 工具的注册、发现、Schema 验证和权限控制 |
| 4 | **Session Manager** | 管理多轮对话的上下文、记忆和消息历史 |
| 5 | **Reflection Engine** | 评估 Agent 行动结果，诊断错误，触发重试或策略调整 |
| 6 | **Adapters** | 可插拔的任务类型适配器（代码生成、数据分析等） |
| 7 | **I/O Layer** | 用户交互入口（CLI、API、IDE 插件等） |

---

## 四、模块间接口定义

### 4.1 Agent Core ↔ LLM Provider

```python
class LLMProvider(Protocol):
    """LLM 服务提供者接口。"""
    
    def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """调用 LLM，返回结构化响应。"""
        ...
    
    def stream_complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        **kwargs,
    ) -> Iterator[LLMResponseChunk]:
        """流式调用 LLM。"""
        ...

@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: list[ToolCall] | None = None  # assistant 角色发起的工具调用
    tool_call_id: str | None = None           # tool 角色的响应对应 ID

@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] | None
    usage: TokenUsage
    finish_reason: str

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict  # JSON parsed

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

### 4.2 Tool Registry

```python
class ToolRegistry:
    """工具注册中心。"""
    
    def register(self, tool: Tool) -> None:
        """注册一个工具。同名工具会覆盖已有注册。"""
        ...
    
    def unregister(self, name: str) -> None:
        """注销工具。"""
        ...
    
    def get(self, name: str) -> Tool:
        """按名称查找工具，不存在抛出 ToolNotFoundError。"""
        ...
    
    def list_tools(self) -> list[ToolSchema]:
        """返回所有已注册工具的 Schema（用于传给 LLM）。"""
        ...
    
    def list_by_capability(self, tag: str) -> list[Tool]:
        """按能力标签筛选工具（如 'code', 'web', 'file'）。"""
        ...

@dataclass
class ToolSchema:
    """工具的描述性 Schema（传给 LLM 用）。"""
    name: str
    description: str
    parameters: dict  # JSON Schema format
    tags: list[str] = field(default_factory=list)

class Tool(Protocol):
    """工具执行接口。"""
    
    @property
    def schema(self) -> ToolSchema:
        """返回工具 Schema。"""
        ...
    
    def execute(self, arguments: dict, context: ExecutionContext) -> ToolResult:
        """执行工具，返回结果。"""
        ...
    
    def validate_arguments(self, arguments: dict) -> ValidationResult:
        """验证参数是否符合 Schema。"""
        ...

@dataclass
class ToolResult:
    success: bool
    output: Any
    error: str | None = None

@dataclass
class ExecutionContext:
    """工具执行时的上下文引用（不复制数据，仅提供访问）。"""
    session_id: str
    working_directory: str
    permissions: set[str]
```

### 4.3 Session Manager

```python
class SessionManager:
    """会话管理器。"""
    
    def create_session(self, session_id: str | None = None) -> Session:
        """创建新会话。"""
        ...
    
    def get_session(self, session_id: str) -> Session:
        """获取已有会话。"""
        ...
    
    def list_sessions(self) -> list[SessionInfo]:
        """列出所有会话（元信息，不包含消息内容）。"""
        ...

class Session:
    """单次对话会话。"""
    
    def add_message(self, message: Message) -> None:
        """添加消息到历史。"""
        ...
    
    def get_messages(self, limit: int | None = None) -> list[Message]:
        """获取消息历史。limit=None 返回全部。"""
        ...
    
    def get_context_window(self, max_tokens: int) -> list[Message]:
        """获取适配 Token 预算的消息子集（自动截断历史）。"""
        ...
    
    def set_variable(self, key: str, value: Any) -> None:
        """设置会话级变量。"""
        ...
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取会话级变量。"""
        ...
    
    def to_summary(self) -> str:
        """生成会话摘要（用于上下文压缩）。"""
        ...
```

### 4.4 Orchestrator

```python
class Orchestrator:
    """任务编排器。"""
    
    def plan(self, task: str, session: Session) -> ExecutionPlan:
        """分析任务，生成执行计划。"""
        ...
    
    def execute(self, plan: ExecutionPlan, session: Session) -> TaskResult:
        """按计划执行子任务。"""
        ...
    
    def replan(self, plan: ExecutionPlan, feedback: ReflectionFeedback) -> ExecutionPlan:
        """根据反思反馈调整执行计划。"""
        ...

@dataclass
class ExecutionPlan:
    """执行计划：子任务 DAG。"""
    goal: str
    subtasks: list[SubTask]
    dependencies: dict[str, list[str]]  # subtask_id -> 依赖的 subtask_id 列表
    
    def get_ready_tasks(self, completed: set[str]) -> list[SubTask]:
        """获取当前可执行的子任务（依赖已满足）。"""
        ...

@dataclass
class SubTask:
    id: str
    description: str
    tool_requirements: list[str]  # 需要的工具名称
    expected_output: str
    status: Literal["pending", "running", "done", "failed"] = "pending"
    result: Any = None

@dataclass
class TaskResult:
    success: bool
    output: Any
    subtask_results: dict[str, SubTaskResult]
```

### 4.5 Reflection Engine

```python
class ReflectionEngine:
    """反思引擎：评估 Agent 行动结果，触发纠错。"""
    
    def evaluate(
        self,
        action: AgentAction,
        result: ToolResult | LLMResponse,
        original_task: str,
    ) -> ReflectionFeedback:
        """评估单次行动的结果。"""
        ...
    
    def diagnose_failure(
        self,
        error: Exception,
        context: list[Message],
        attempts: int,
    ) -> Diagnosis:
        """诊断失败原因，给出修复建议。"""
        ...

@dataclass
class ReflectionFeedback:
    quality_score: float          # 0.0 ~ 1.0
    should_retry: bool
    retry_strategy: Literal["same_tool", "different_tool", "rephrase", "escalate"]
    reasoning: str                # 评估推理过程
    suggested_fix: str | None     # 可选的修复建议

@dataclass
class Diagnosis:
    root_cause: str               # 错误根因
    category: Literal["tool_error", "reasoning_error", "context_gap", "unknown"]
    recommended_action: str       # 建议的下一步
    max_attempts_reached: bool    # 是否已达最大重试次数
```

### 4.6 Adapter 接口

```python
class TaskAdapter(Protocol):
    """任务类型适配器。每种任务类型（代码生成、数据分析等）实现此接口。"""
    
    @property
    def task_type(self) -> str:
        """任务类型标识（如 'code_gen', 'data_analysis'）。"""
        ...
    
    def can_handle(self, task: str) -> float:
        """评估本适配器处理该任务的能力（0.0 ~ 1.0）。"""
        ...
    
    def prepare_context(self, task: str, session: Session) -> list[Message]:
        """为特定任务类型准备系统提示和上下文。"""
        ...
    
    def format_output(self, result: TaskResult) -> str:
        """格式化任务结果为用户可读输出。"""
        ...
```

---

## 五、数据流图

### 一个任务从接收到完成的完整流程

```
用户输入 "帮我分析这个 CSV 文件的数据趋势"
    │
    ▼
┌─────────────┐
│  I/O Layer   │  接收输入，路由到 Agent Core
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Session Mgr   │  创建/恢复 Session，添加用户消息
│              │  Session.get_context_window(max_tokens) → 消息列表
└──────┬──────┘
       │ messages
       ▼
┌─────────────┐
│ Adapter      │  can_handle() 评估 → 选择 "data_analysis" 适配器
│              │  prepare_context() 注入数据分析专用系统提示
└──────┬──────┘
       │ enriched_messages
       ▼
┌─────────────┐
│ Orchestrator │  plan() 分析任务，生成执行计划：
│              │    SubTask 1: 读取 CSV (tool: file_read)
│              │    SubTask 2: 数据清洗 (tool: data_transform)
│              │    SubTask 3: 趋势分析 (tool: data_analyze)
│              │    SubTask 4: 生成报告 (tool: none, LLM 生成)
│              │  依赖: 1→2→3→4（线性）
└──────┬──────┘
       │ plan
       ▼
┌──────────────────────────────────────────┐
│           执行循环 (per SubTask)          │
│                                          │
│  ┌──────────────┐    tools_schemas       │
│  │ Tool Registry │◄──────────────────┐   │
│  └──────┬───────┘                     │   │
│         │ tools + messages             │   │
│         ▼                              │   │
│  ┌──────────────┐                      │   │
│  │  Agent Core   │                      │   │
│  │              │                      │   │
│  │ LLM.complete │──► ToolCall          │   │
│  │     │        │     │                │   │
│  │     │        │     ▼                │   │
│  │     │        │  Tool Registry.get() │   │
│  │     │        │     │                │   │
│  │     │        │     ▼                │   │
│  │     │        │  Tool.execute()      │   │
│  │     │        │     │                │   │
│  │     │  ◄─────┤  ToolResult         │   │
│  │     │        │                      │   │
│  │     ▼        │                      │   │
│  │ 添加工具     │                      │   │
│  │ 结果到消息   │                      │   │
│  │ 继续推理     │                      │   │
│  └──────┬───────┘                      │   │
│         │ subtask_result                │   │
│         ▼                              │   │
│  ┌──────────────┐                      │   │
│  │ Reflection   │                      │   │
│  │ Engine       │                      │   │
│  │              │                      │   │
│  │ evaluate()   │──► quality_score     │   │
│  │     │        │                      │   │
│  │     ├── 高分  │──► 标记完成          │   │
│  │     │        │                      │   │
│  │     └── 低分  │──► should_retry     │   │
│  │              │    │                 │   │
│  │              │    ├── retry_strategy│   │
│  │              │    └── 反馈给        │   │
│  │              │        Agent Core    │   │
│  └──────────────┘                      │   │
│                                          │   │
└──────────────────────────────────────────┘   │
       │                                          │
       │ 全部 SubTask 完成                         │
       ▼                                          │
┌─────────────┐                                  │
│ Orchestrator │  汇总所有子任务结果 → TaskResult  │
└──────┬──────┘                                  │
       │                                          │
       ▼                                          │
┌─────────────┐                                  │
│ Adapter      │  format_output() → 用户可读格式   │
└──────┬──────┘                                  │
       │                                          │
       ▼                                          │
┌─────────────┐                                  │
│  I/O Layer   │  输出结果给用户                   │
└─────────────┘                                  │
```

### 反思重试流程（Detail）

```
SubTask 执行完成
    │
    ▼
ReflectionEngine.evaluate(action, result, task)
    │
    ├── quality_score >= 0.8 → 标记 done，继续下一个 SubTask
    │
    ├── quality_score 0.4~0.8 且 attempts < max → should_retry=True
    │       │
    │       ├── retry_strategy="same_tool"
    │       │   → 调整参数，重新调用同一工具
    │       │
    │       ├── retry_strategy="different_tool"
    │       │   → 选择不同工具完成同一子任务
    │       │
    │       └── retry_strategy="rephrase"
    │           → 重新组织 LLM 提示，让 Agent 换个思路
    │
    ├── quality_score < 0.4 且 attempts >= max → escalate
    │   → 返回错误，Orchestrator 决定是否 replan
    │
    └── category="context_gap"
        → Orchestrator.replan() 重新拆解任务
```

---

## 六、ADR（架构决策记录）

### ADR-001: Agent Core 采用 ReAct 循环而非纯 Planning

- **背景**：Agent 需要在"思考"和"行动"之间交替，直至任务完成。有两种主流范式：Plan-and-Execute（先规划全部步骤再执行）和 ReAct（Reasoning + Acting，逐步推理逐步行动）。
- **选项**：
  1. **Plan-and-Execute**：Orchestrator 先生成完整计划，Agent 按计划执行，不偏离
  2. **ReAct**：Agent 每一步都推理下一步做什么，动态决策
  3. **混合**：Orchestrator 做粗粒度规划，Agent Core 在每个子任务内用 ReAct 循环
- **决定**：选择**混合模式（选项 3）**。Orchestrator 负责任务级规划（子任务 DAG），Agent Core 在子任务内用 ReAct 循环处理具体操作。
- **后果**：
  - 优点：兼顾全局规划能力和局部灵活性，复杂任务不失控
  - 代价：两层循环增加实现复杂度，需要清晰的职责边界避免混乱
  - 与纯 ReAct 的区别：子任务边界由 Orchestrator 控制，避免 Agent 在无关方向上"漫游"

### ADR-002: Tool 接口基于 JSON Schema 而非 Python 类型签名

- **背景**：工具的参数定义需要让 LLM 理解。两种思路：Python 函数签名（带 type hints）vs JSON Schema。
- **选项**：
  1. **Python 类型签名**：从函数定义自动提取参数类型，生成文档
  2. **JSON Schema**：显式定义参数格式，与 OpenAI Function Calling 等标准兼容
  3. **自定义 DSL**：自建一套参数描述语言
- **决定**：选择**JSON Schema（选项 2）**。
- **理由**：
  - 行业标准：OpenAI、Anthropic、Google 均采用 JSON Schema 描述工具
  - 生态兼容：不绑定特定 LLM provider，换模型时 Schema 不用改
  - LLM 友好：JSON Schema 能精确描述嵌套结构、枚举、必填/可选等约束
- **后果**：
  - Python 端需做 JSON Schema ↔ Python 对象的转换（但这是一个已成熟的问题）
  - 工具注册时需要同时提供 Python 函数和 JSON Schema（可从 docstring 自动生成）

### ADR-003: 上下文管理采用滑动窗口 + 摘要，而非无限历史

- **背景**：多轮对话的上下文会不断增长，但 LLM 的上下文窗口有限。需要一种策略来管理消息历史。
- **选项**：
  1. **保留全部历史**：简单但会超出 Token 预算
  2. **滑动窗口**：只保留最近 N 条消息
  3. **滑动窗口 + 摘要**：最近的详细保留，更早的压缩为摘要
  4. **向量检索 RAG**：将历史存入向量库，按相关性检索
- **决定**：V1 选择**滑动窗口 + 摘要（选项 3）**，V2 预留 RAG 扩展点。
- **理由**：
  - 滑动窗口保证 Token 不超预算，摘要保留关键信息不丢失
  - V1 阶段对话轮次通常可控，不需要 RAG 的复杂度
  - Session.to_summary() 接口设计已为 RAG 预留空间
- **后果**：
  - 摘要质量取决于 LLM 能力，可能丢失细节
  - 未来如需 RAG，SessionManager 内部实现可替换，外部接口不变

### ADR-004: Orchestrator 子任务用 DAG 而非简单线性列表

- **背景**：任务拆解后的子任务之间可能存在并行关系（如同时读取两个文件），线性列表无法表达并行性。
- **选项**：
  1. **线性列表**：简单，但所有子任务串行执行
  2. **DAG（有向无环图）**：可表达并行依赖
  3. **完全并行**：所有子任务同时执行
- **决定**：选择**DAG（选项 2）**。
- **理由**：
  - DAG 的退化为线性列表（所有任务串行依赖），不增加简单场景的复杂度
  - 但为并行场景提供了自然的表达方式
  - get_ready_tasks() 方法可轻松实现并行调度
- **后果**：
  - DAG 拓扑排序的实现是成熟算法，复杂度可控
  - 当前版本可先实现串行执行，并行执行作为未来优化点
  - 需防止循环依赖（DAG 创建时校验）

### ADR-005: 反思引擎用 LLM 辅助评估而非纯规则判断

- **背景**：Reflection Engine 需要判断 Agent 的行动是否有效。纯规则方式（如检查返回值非空）太粗糙，但每次都用 LLM 评估有 Token 成本。
- **选项**：
  1. **纯规则**：基于返回码、异常类型等硬编码规则
  2. **纯 LLM**：每次行动后调 LLM 评估结果质量
  3. **规则快筛 + LLM 精评**：先用规则过滤明显成功/失败，不确定的才用 LLM
- **决定**：选择**规则快筛 + LLM 精评（选项 3）**。
- **理由**：
  - 工具返回 success=True 且有合理输出 → 直接通过，零成本
  - 工具抛异常 → 直接判定失败，零成本
  - 工具成功但输出可能不对（如代码生成了但有 bug）→ 调 LLM 精评
  - 大约 60-70% 的情况可用规则解决，节省 Token
- **后果**：
  - 规则部分需要随工具类型增长而维护
  - LLM 精评增加了延迟（串行场景下每步多一次 LLM 调用）
  - 可以异步执行精评，不阻塞主流程

---

## 七、复杂度评估

| 模块 | 复杂度 | 原因 | 控制策略 |
|------|--------|------|---------|
| **Agent Core** | ⭐⭐⭐⭐ | 核心 ReAct 循环涉及 LLM 调用、工具分发、消息管理等多个关注点的交织 | 严格定义单次循环的输入/输出，每步只做一件事；不在此模块内做任务规划 |
| **Orchestrator** | ⭐⭐⭐ | DAG 编排 + 与 Reflection Engine 的交互 + replan 逻辑 | V1 只做串行执行，DAG 结构预留给未来并行；replan 只支持一轮调整 |
| **Reflection Engine** | ⭐⭐⭐⭐ | 需要判断"结果质量"这个模糊概念，规则和 LLM 混合评估逻辑复杂 | 用明确的评分阈值控制分支；LLM 精评的 prompt 模板化，不搞自由生成 |
| **Tool Registry** | ⭐⭐ | Schema 管理 + 权限检查，逻辑清晰 | 零状态设计（注册时校验完事），不做运行时动态热加载（V1） |
| **Session Manager** | ⭐⭐ | 消息列表 + Token 计算 + 摘要生成 | Token 计算用字符数估算（不精确但够用）；摘要生成频率可配置 |
| **Adapters** | ⭐⭐ | 每个适配器独立，单一职责 | 适配器之间零耦合；通过 TaskAdapter Protocol 约束接口 |

**最高复杂度模块：Agent Core 和 Reflection Engine。**

Agent Core 复杂度来源是 ReAct 循环中"推理→行动→观察→再推理"的状态管理。控制手段是把每一步的输入输出严格定义（Message in → ToolCall/Text out → ToolResult/Continue），避免状态泄漏。

Reflection Engine 复杂度来源是"质量评估"的模糊性。控制手段是先用规则做快筛（70% 情况直接判定），只对不确定的情况调 LLM，且 LLM 评估的 prompt 严格模板化。

---

## 八、未来扩展点

| 扩展点 | 当前状态 | 未来方向 |
|--------|---------|---------|
| 并行执行 | DAG 结构已设计，执行为串行 | 实现并行调度（asyncio / 线程池） |
| 多 Agent 协作 | 单 Agent | Agent 间通过消息传递协作 |
| 持久化 | 内存存储 | Session 持久化到数据库 |
| 工具沙箱 | 无隔离 | 工具在沙箱环境中执行 |
| 流式输出 | 未设计 | SSE / WebSocket 流式返回 |

---

## 九、自我评估

### 架构完整性评分：82 / 100

**扣分项**：
- -8：缺少详细的错误处理和恢复策略（只在 Reflection Engine 中提到了重试，没有全局的容错设计）
- -5：I/O Layer 和 Adapter 层的设计相对粗略，主要是接口定义，缺少实际交互流程
- -3：Token 预算管理没有跨模块的全局视图（Session Manager 管 Token 计算，但 Agent Core 的工具调用也消耗 Token，两者没有协调）
- -2：缺少配置管理模块的设计（系统提示、模型参数、超时等从哪里来？）

### 是否存在过度设计？

**部分是，但控制在合理范围内。**

- DAG 编排在 V1 可能只需要线性执行，但 DAG 结构的成本很低（一个拓扑排序），且为并行天然铺路——这是合理的提前设计。
- 规则快筛 + LLM 精评的设计有轻微过度，V1 可以先用纯 LLM 评估，但考虑到 Token 成本是 Agent 系统的真实痛点，快筛是一个有价值的优化——值得保留。

### 如果我来写代码

**最有信心写好的模块**：Tool Registry 和 Session Manager。原因：职责清晰、逻辑线性、没有模糊的"质量判断"环节。注册、查找、消息增删——这些是可以写单元测试彻底验证的确定性逻辑。

**最担心的模块**：Reflection Engine。原因：它本质上是让一个 AI 评估另一个 AI 的工作质量，这是一个开放性问题。规则快筛好写，但 LLM 精评的 prompt 设计、评分阈值的调优——这些需要大量实验，不是靠架构设计能解决的。而且评估错误会导致无意义重试，浪费 Token。

### 与 Cherny Mission 8 的架构的本质区别

| 维度 | Cherny Pipeline | 本架构 (Deep Agent) |
|------|----------------|---------------------|
| **核心范式** | 数据流管道（线性+分支） | ReAct Agent 循环 + 任务 DAG |
| **驱动方式** | 预定义的 Stage 函数，确定性地执行 | LLM 动态决策，每次执行路径不确定 |
| **复杂度来源** | 编排逻辑（分支、嵌套） | LLM 输出的不确定性 |
| **反思能力** | 无（Stage 成功/失败是二元的） | 有专门的 Reflection Engine 做质量评估 |
| **工具管理** | 无（Pipeline 本身就是处理步骤） | 有独立的 Tool Registry，动态注册发现 |
| **上下文** | Context 是 key-value 数据载体 | Session 管理对话历史、记忆和 Token 预算 |

**一句话总结区别**：Cherny 的 Pipeline 是"确定性编排框架"——你知道每一步会做什么；Deep Agent 是"非确定性智能框架"——每一步做什么由 LLM 决定。Pipeline 的复杂度在"怎么编排"，Agent 的复杂度在"怎么让 LLM 做出好决策"。

Cherny 的架构在确定性场景下更可靠、更可测试；我的架构在开放性场景下更灵活，但可靠性更难保证。两者不是替代关系——在 Deep Agent 框架内部，Orchestrator 编排子任务时，完全可以用类似 Cherny Pipeline 的模式来组织确定性的子任务执行流程。
