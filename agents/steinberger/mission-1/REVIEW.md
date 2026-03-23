# 架构评审：Cherny Mission 8 Pipeline 框架

> 评审人：Steinberger（架构师） | 日期：2026-03-22 | 被评审对象：Cherny Mission 8 Pipeline 框架

---

## 一、优点

### 1. 模块划分干净，职责边界清晰

四个模块（core、context、result、retry）各司其职，每个模块用一句话就能描述清楚。`context.py` 只管数据传递，`retry.py` 只管重试策略，`result.py` 只管结果记录——这是教科书级别的单一职责。模块间没有循环依赖，依赖方向为 core → context/result/retry，单向无环。

### 2. 接口设计简洁实用

`Stage` 的函数签名 `(Context) -> Context | None` 是一个很好的设计——简单、直觉、Python 风格自然。`return None` 作为透传的语义清晰，减少了样板代码。`Pipeline.add_stage()` 的链式调用也是好的 API 设计选择，让使用者可以流畅地定义管道。

### 3. 错误处理分层合理

三层错误处理（Stage 内部 → 重试 → Pipeline 级别中止）逻辑清晰，每层的职责不重叠。`StopPipeline` 作为提前终止的机制比抛出通用异常更明确。`RetryPolicy` 的 `non_retryable_exceptions` 优先级高于 `retryable_exceptions` 的设计很周到，避免了"全允许然后排除"的反直觉逻辑。

### 4. 文档质量高

ARCHITECTURE.md 包含了完整的背景、模块设计、接口定义、数据流、ADR 和测试策略。每个 ADR 都列出了替代方案和理由。这不是一份"写完代码补的文档"，而是一份真正指导实现的架构文档。

### 5. 测试覆盖思路全面

测试策略覆盖了边界条件（空 Pipeline、空 Context、嵌套 Branch、重试耗尽等），说明作者在写代码前就思考了异常情况。

---

## 二、问题（按严重程度排序）

### 🔴 P0：Stage.execute() 中的返回值检查逻辑有 bug

```python
# core.py, Stage.execute(), 第 53-54 行
result = self.func(context)
if result is not None and not isinstance(result, Context):
    return result  # ← 这里直接 return 了 result（不是 StageResult）
```

当 `result` 不是 `None` 且不是 `Context` 时（比如 Stage 函数返回了一个字符串或数字），代码直接返回了这个原始值，而不是 `StageResult`。这会导致调用方（`Pipeline._execute_nodes`）收到非 `StageResult` 类型的返回值，后续的 `result.status` 访问会抛 `AttributeError`。

**影响**：运行时错误。任何 Stage 函数返回了非 None、非 Context 的值，Pipeline 就会崩溃。

**修复**：应该抛出 `TypeError` 或按失败处理，而不是直接返回原始值。

### 🟠 P1：Branch 的 _execute_branch 和 _execute_nodes 耦合度高

`Pipeline._execute_branch()` 和 `Pipeline._execute_nodes()` 都直接操作 `PipelineReport` 的内部字段（`succeeded`、`failed`、`stage_results`、`error_chain`）。这意味着 Pipeline 类承担了"执行节点"和"维护报告"两个职责。

如果未来想支持不同的报告格式（比如 JSON 报告、HTML 报告），或者想让报告生成可插拔，就需要修改 Pipeline 的核心执行逻辑。

**建议**：将报告维护逻辑封装到 `PipelineReport` 内部（提供 `record_success()`、`record_failure()` 方法），Pipeline 只调用报告方法，不直接操作字段。

### 🟠 P1：Context.snapshot() 使用 deepcopy 可能有性能和兼容性问题

`deepcopy` 对于包含不可深拷贝的对象（如文件句柄、数据库连接、线程锁）会失败或产生意外行为。在数据处理场景中，Context 中存储的内容类型不可控。

另外，即使数据都是可拷贝的，对大对象做 deepcopy 在每个 Stage 前后都执行两次（input_snapshot + output_snapshot），可能有性能影响。

**建议**：
- V1 中将 snapshot 设为可选（默认关闭），仅在调试模式开启
- 或者在 Context 上标记哪些 key 是可快照的

### 🟡 P2：Pipeline 是最终类，无法扩展执行策略

当前 `Pipeline` 类直接实现了线性+分支的执行逻辑。如果用户需要：
- 并行执行（多个 Branch 同时跑）
- 条件跳过（某个 Stage 失败后跳到另一个 Stage）
- 自定义执行顺序

唯一的办法是修改 `Pipeline` 类本身或完全重写。

**建议**：将执行逻辑抽取为 `ExecutionStrategy` 接口，Pipeline 使用策略而非硬编码执行逻辑。V1 可以只有一个 `LinearStrategy`，但架构上为扩展留了空间。

### 🟡 P2：缺少 Pipeline 的序列化和持久化

Pipeline 只能在内存中构建和执行。如果需要：
- 将 Pipeline 定义保存到文件/数据库，下次加载执行
- 在分布式系统中传递 Pipeline 定义
- 跨进程复用 Pipeline

当前设计不支持。

**建议**：为 Pipeline 提供 `to_dict()` / `from_dict()` 序列化方法（Stage 函数除外，因为函数不可序列化——这确实是个限制，需要用注册名代替函数引用）。

### 🟡 P2：Branch 缺少对 true_stages 和 false_stages 都为空的校验

如果 `Branch(true_stages=[], false_stages=None)`，条件判断结果毫无意义——无论 True 还是 False 都什么都不做。这可能是用户的配置错误，但框架不会给出任何提示。

---

## 三、改进建议

### 1. 修复 Stage.execute() 的返回值 bug（立即）

```python
result = self.func(context)
if result is not None and not isinstance(result, Context):
    raise TypeError(
        f"Stage '{self.name}' returned {type(result).__name__}, "
        f"expected Context or None"
    )
```

### 2. 将报告维护封装到 PipelineReport 中

```python
class PipelineReport:
    def record_stage_result(self, result: StageResult) -> None:
        self.stage_results.append(result)
        if result.status == StageStatus.SUCCESS:
            self.succeeded += 1
        elif result.status == StageStatus.FAILED:
            self.failed += 1
    
    def record_error(self, chain_prefix: str, name: str, error: Exception) -> None:
        self.error_chain.append(f"{chain_prefix}{name}: {error}")
```

### 3. 为 Stage 和 Branch 添加 `__repr__` 方法

当前调试时看到的都是 `<pipeline.core.Stage object at 0x...>`，不方便。添加 `__repr__` 返回名称，调试体验会好很多。

### 4. Pipeline.add_stage 支持装饰器语法

```python
pipeline = Pipeline("data-pipeline")

@pipeline.stage("clean_data")
def clean(ctx: Context) -> Context:
    ctx.set("cleaned", True)
    return ctx
```

这种语法更 Pythonic，减少样板代码。

### 5. 为 RetryPolicy 添加抖动（jitter）

纯指数退避在多个 Pipeline 同时重试时会产生"惊群效应"（thundering herd）。建议在退避时间上加入随机抖动：

```python
import random

def get_delay(self, attempt: int) -> float:
    base_delay = self.backoff_base * (self.backoff_multiplier ** (attempt - 1))
    jitter = random.uniform(0.8, 1.2)  # ±20% 抖动
    return min(base_delay * jitter, self.max_backoff)
```

---

## 四、架构评分

### 总分：8.0 / 10

| 维度 | 评分 | 说明 |
|------|------|------|
| 模块划分 | 9/10 | 四个模块职责清晰，单向无环 |
| 接口设计 | 8/10 | 简洁实用，但缺乏扩展点 |
| 错误处理 | 8/10 | 分层合理，有 StopPipeline 机制 |
| 代码质量 | 7/10 | 有一个 P0 bug，报告维护耦合在 Pipeline 中 |
| 文档完整性 | 9/10 | 架构文档全面，ADR 规范 |
| 可测试性 | 8/10 | 零依赖，纯函数风格易测试 |
| 可扩展性 | 7/10 | 执行策略硬编码，序列化不支持 |
| 实用性 | 8/10 | 对 Mission 8 的场景（数据处理管道）完全够用 |

**总结**：这是一个"恰到好处"的架构——不过度设计，职责清晰，文档规范。P0 bug 修复后，作为数据处理管道的基础框架完全可用。主要的架构局限在于扩展性（执行策略、序列化），但这些在 Mission 8 的场景下不是刚需——"先够用，再扩展"是正确的策略。

---

*评审完成。Cherny 的 Pipeline 框架在确定性数据处理场景下是一个扎实的设计。*
