# Pipeline 框架架构设计文档

> 作者：Cherny | 日期：2026-03-22 | 版本：1.0

## 一、问题定义

开发团队在数据处理场景中面临的核心问题：

1. **流程碎片化**：数据处理的各步骤（读取→清洗→转换→验证→输出）散落在不同代码中，没有统一的编排方式
2. **错误恢复困难**：某个步骤失败后，要么整个流程崩溃，要么需要手动处理重试
3. **缺乏可观测性**：无法知道每个步骤的执行状态、耗时、数据变化
4. **复用性差**：每次新建处理流程都要重写编排逻辑

**目标**：提供一个轻量级、零依赖的 Pipeline 框架，让开发者像搭积木一样组合数据处理流程。

---

## 二、模块设计

```
mission-8/
├── pipeline/
│   ├── __init__.py          # 包入口，导出核心 API
│   ├── core.py              # Pipeline、Stage、Branch 核心抽象
│   ├── context.py           # 执行上下文（数据在 Stage 间传递的载体）
│   ├── result.py            # 执行结果、Stage 报告、Pipeline 汇总报告
│   └── retry.py             # 重试策略（重试次数、退避间隔）
├── tests/
│   ├── __init__.py
│   ├── test_core.py         # Pipeline 和 Stage 核心测试
│   ├── test_context.py      # 上下文传递测试
│   ├── test_retry.py        # 重试策略测试
│   ├── test_result.py       # 结果和报告测试
│   └── test_integration.py  # 端到端集成测试
├── ARCHITECTURE.md
└── report.md
```

### 各模块职责

| 模块 | 职责 | 单一职责理由 |
|------|------|-------------|
| `core.py` | Pipeline 编排逻辑、Stage 定义与执行、条件分支 | 编排是框架的核心，独立于数据载体和结果报告 |
| `context.py` | Stage 间数据传递的载体，支持 key-value 存取 | 上下文管理是独立关注点，与编排逻辑解耦 |
| `result.py` | Stage 结果记录、Pipeline 汇总报告生成 | 报告格式化是独立关注点，便于扩展不同输出格式 |
| `retry.py` | 重试策略定义（次数、间隔、异常过滤） | 重试策略可能变化，独立出来便于替换和测试 |

---

## 三、核心接口

### 3.1 上下文 — `context.py`

```python
class Context:
    """Stage 间数据传递的载体。"""
    
    def __init__(self, data: dict | None = None) -> None:
        """初始化上下文。
        Args:
            data: 初始数据字典，默认为空。
        """
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取值，不存在返回默认值。"""
    
    def set(self, key: str, value: Any) -> None:
        """设置键值对。"""
    
    def has(self, key: str) -> bool:
        """检查键是否存在。"""
    
    def remove(self, key: str) -> None:
        """移除键。不存在时静默。"""
    
    def to_dict(self) -> dict:
        """导出为普通字典。"""
    
    def snapshot(self) -> dict:
        """创建当前状态的快照（用于调试和报告）。"""
```

**设计决策**：用 key-value 字典而非固定 schema，因为不同 Pipeline 处理的数据结构完全不同。保持灵活性。

### 3.2 Stage 结果 — `result.py`

```python
class StageStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class StageResult:
    """单个 Stage 的执行结果。"""
    
    name: str                    # Stage 名称
    status: StageStatus          # 执行状态
    duration_ms: float           # 执行耗时（毫秒）
    attempts: int                # 实际执行次数（含重试）
    error: Exception | None      # 错误信息（如果失败）
    input_snapshot: dict | None  # 输入快照（可选）
    output_snapshot: dict | None # 输出快照（可选）

class PipelineReport:
    """Pipeline 执行汇总报告。"""
    
    pipeline_name: str                      # Pipeline 名称
    total_stages: int                       # 总 Stage 数
    succeeded: int                          # 成功数
    failed: int                             # 失败数
    skipped: int                            # 跳过数
    total_duration_ms: float                # 总耗时
    stage_results: list[StageResult]        # 各 Stage 结果
    error_chain: list[str]                  # 错误链（失败路径追踪）
    
    def summary(self) -> str:
        """生成人类可读的汇总文本。"""
    
    def to_dict(self) -> dict:
        """导出为字典。"""

class StopPipeline(Exception):
    """用于从 Stage 内部提前终止整个 Pipeline。"""
    message: str
```

### 3.3 重试策略 — `retry.py`

```python
class RetryPolicy:
    """Stage 级别的重试策略。"""
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff: float = 30.0,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
        non_retryable_exceptions: tuple[type[Exception], ...] = (),
    ) -> None:
        """
        Args:
            max_retries: 最大重试次数（不含首次执行）。0 = 不重试。
            backoff_base: 首次重试等待秒数。
            backoff_multiplier: 退避倍数（指数退避）。
            max_backoff: 最大等待秒数。
            retryable_exceptions: 允许重试的异常类型。默认所有异常。
            non_retryable_exceptions: 明确不重试的异常类型（优先级更高）。
        """
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试。"""
    
    def get_delay(self, attempt: int) -> float:
        """获取第 N 次重试的等待时间（秒）。"""
```

### 3.4 Stage 和 Pipeline — `core.py`

```python
from typing import Callable, Any

# Stage 的处理函数签名
StageFunc = Callable[[Context], Context | None]
# 条件判断函数签名
ConditionFunc = Callable[[Context], bool]

class Stage:
    """Pipeline 中的一个处理步骤。"""
    
    def __init__(
        self,
        name: str,
        func: StageFunc,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """
        Args:
            name: Stage 唯一名称。
            func: 处理函数，接收 Context，返回修改后的 Context（或 None 表示不修改）。
            retry_policy: 重试策略，None 使用默认策略（不重试）。
        """
    
    def execute(self, context: Context) -> StageResult:
        """执行 Stage，返回 StageResult。"""

class Branch:
    """条件分支节点。"""
    
    def __init__(
        self,
        name: str,
        condition: ConditionFunc,
        true_stages: list[Stage | Branch],
        false_stages: list[Stage | Branch] | None = None,
    ) -> None:
        """
        Args:
            name: 分支节点名称。
            condition: 条件函数，接收 Context 返回 bool。
            true_stages: 条件为 True 时执行的 Stage 列表。
            false_stages: 条件为 False 时执行的 Stage 列表（可选，默认跳过）。
        """

class Pipeline:
    """数据处理管道，编排 Stage 的执行。"""
    
    def __init__(self, name: str) -> None:
        """
        Args:
            name: Pipeline 名称。
        """
    
    def add_stage(self, stage: Stage) -> "Pipeline":
        """添加 Stage，支持链式调用。"""
    
    def run(self, initial_data: dict | None = None) -> PipelineReport:
        """执行整个 Pipeline。
        Args:
            initial_data: 初始数据字典。
        Returns:
            PipelineReport 汇总报告。
        """
```

---

## 四、数据流

### 4.1 基本线性流程

```
Pipeline.run(data)
    │
    ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Stage A │────▶│ Stage B │────▶│ Stage C │
│ (读取)  │     │ (清洗)  │     │ (输出)  │
└─────────┘     └─────────┘     └─────────┘
    │                │                │
    ▼                ▼                ▼
 Context ──修改──▶ Context ──修改──▶ Context
```

- `Pipeline.run()` 创建初始 `Context`
- 每个 Stage 接收当前 `Context`，处理后返回（修改或新）`Context`
- Stage 返回 `None` 时，`Context` 不变（透传）
- 最终 `Context` 保存到 `PipelineReport` 中

### 4.2 条件分支流程

```
                ┌──────────────┐
                │ Branch("验证") │
                │ condition(ctx) │
                └──────┬───────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        condition=True    condition=False
              │                 │
        ┌─────┴─────┐    ┌────┴────┐
        │ Stage D1  │    │Stage E1 │
        │ Stage D2  │    │Stage E2 │
        └───────────┘    └─────────┘
              │                 │
              └────────┬────────┘
                       ▼
                  继续后续 Stage
```

- `Branch` 是一个特殊的节点，包含条件函数和两个 Stage 列表
- 条件为 True 执行 `true_stages`，为 False 执行 `false_stages`（如果提供了的话）
- 分支完成后，两条路径汇合，继续执行后续 Stage
- `Branch` 可以嵌套（`true_stages` 中可以包含 `Branch`）

### 4.3 错误处理流程

```
Stage 执行失败
    │
    ▼
检查 RetryPolicy.should_retry(error, attempt)
    │
    ├── 应重试 → 等待 backoff → 重新执行（最多 max_retries 次）
    │
    └── 不应重试或重试耗尽 → 记录 StageResult(status=FAILED)
                                  │
                                  ▼
                          Pipeline 中止，生成报告
```

---

## 五、错误处理策略

### 5.1 三层错误处理

| 层级 | 错误类型 | 处理方式 |
|------|---------|---------|
| **Stage 内部** | 可预期的业务异常 | 由 Stage 函数自行处理，返回修改后的 Context |
| **Stage 重试** | 临时性故障（网络超时、资源不可用） | RetryPolicy 控制重试次数和间隔 |
| **Pipeline 级别** | Stage 最终失败、不可恢复错误 | 中止 Pipeline，生成包含错误链的报告 |

### 5.2 重试策略详情

- **默认不重试**：Stage 不设置 RetryPolicy 时，失败即中止
- **指数退避**：第 N 次重试等待 `min(base * multiplier^N, max_backoff)` 秒
- **异常过滤**：可配置哪些异常可重试、哪些不可重试
  - `non_retryable_exceptions` 优先级高于 `retryable_exceptions`
  - 例如：`ValueError` 不重试，`ConnectionError` 重试

### 5.3 提前终止

- Stage 内部抛出 `StopPipeline` 异常 → Pipeline 立即停止
- 记录为 `status=SKIPPED` 对后续未执行的 Stage
- 报告中包含 `message` 说明原因

---

## 六、设计决策记录

### ADR-1：Context 使用 key-value 字典，不用固定类型

**决策**：Context 内部用 `dict` 存储，通过 `get/set/has` 方法访问。

**理由**：
- 不同 Pipeline 处理的数据结构差异很大（有的处理 CSV 行，有的处理 JSON 树）
- 强制类型约束会导致框架只能用于特定场景
- key-value 提供最大灵活性，代价是类型安全交给使用者

**替代方案**：
- 泛型 Context[T]：更类型安全，但限制了多类型数据共存
- dataclass 固定结构：需要为每个 Pipeline 定义新类，增加样板代码

### ADR-2：Stage 函数返回 Context 而非就地修改

**决策**：Stage 函数签名是 `(Context) -> Context | None`，返回 None 表示不修改。

**理由**：
- 不强制就地修改，Stage 可以选择返回新 Context（函数式风格）或修改后返回同一个 Context（命令式风格）
- 返回 None 的快捷方式减少样板代码（只读 Stage 不需要 `return ctx`）
- 保持向后兼容：两种风格都能工作

**替代方案**：
- 纯函数式（必须返回新 Context）：性能开销大，且 Python 生态不习惯
- 纯命令式（就地修改，无返回值）：无法让 Stage 返回"我不修改"的信号

### ADR-3：Branch 作为独立节点，不是 Stage 的属性

**决策**：Branch 是独立的节点类型，与 Stage 并列，可添加到 Pipeline 中。

**理由**：
- 分支是编排逻辑，不是数据处理逻辑，职责不同
- Branch 内部包含 Stage 列表，天然可以嵌套
- 如果做成 Stage 的属性（如 `stage.if_condition = ...`），会导致 Stage 承担编排职责

**替代方案**：
- DAG（有向无环图）：更强大但复杂度大增，当前需求不需要并行执行
- 状态机：对线性+分支场景过于复杂

### ADR-4：零外部依赖

**决策**：完全使用 Python 标准库。

**理由**：
- Mission 要求明确
- `time`、`time.perf_counter` 用于计时
- `dataclasses` 用于数据类
- `enum` 用于枚举
- `copy.deepcopy` 用于快照
- 标准库完全满足需求，无需第三方库

### ADR-5：Pipeline 失败时立即中止（Fail-Fast）

**决策**：某个 Stage 最终失败后，Pipeline 立即停止，不继续执行后续 Stage。

**理由**：
- 数据处理管道中，中间步骤失败意味着后续步骤的数据不可靠
- Fail-Fast 让问题尽早暴露
- 如果需要"跳过失败继续"，可以通过 Try-Catch 在 Stage 内部处理

**替代方案**：
- Continue-on-failure：需要复杂的依赖管理，增加框架复杂度
- 可配置模式（fail-fast / continue）：增加 API 表面积，当前需求不需要

---

## 七、测试策略

### 测试分类

| 类别 | 文件 | 覆盖场景 |
|------|------|---------|
| Context 测试 | `test_context.py` | get/set/has/remove/to_dict/snapshot |
| Retry 测试 | `test_retry.py` | should_retry 逻辑、退避计算、异常过滤 |
| Result 测试 | `test_result.py` | StageResult 创建、PipelineReport 汇总、summary 格式 |
| Core 测试 | `test_core.py` | Stage 执行、Pipeline 线性执行、条件分支、错误处理、重试、StopPipeline |
| 集成测试 | `test_integration.py` | 完整的数据处理场景（读取→清洗→转换→验证→输出）|

### 边界条件

- 空 Pipeline（0 个 Stage）
- 空 Context（无初始数据）
- Stage 返回 None（透传）
- 重试 0 次（不重试策略）
- 重试耗尽后仍然失败
- 嵌套 Branch（Branch 中包含 Branch）
- all Stage 都 SKIPPED 的 Pipeline
- `non_retryable_exceptions` 和 `retryable_exceptions` 冲突时的优先级

---

*架构设计完成。下一步：严格按照此设计实现代码。*
