"""Pipeline 框架 - 核心模块。

提供 Pipeline 编排、Stage 定义与执行、条件分支功能。
"""

import time
from typing import Any, Callable

from .context import Context
from .result import (
    StageResult,
    StageStatus,
    PipelineReport,
    StopPipeline,
)
from .retry import RetryPolicy


# Stage 处理函数签名
StageFunc = Callable[[Context], Context | None]
# 条件判断函数签名
ConditionFunc = Callable[[Context], bool]


class Stage:
    """Pipeline 中的一个处理步骤。

    封装一个处理函数，支持重试策略。
    """

    def __init__(
        self,
        name: str,
        func: StageFunc,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """初始化 Stage。

        Args:
            name: Stage 唯一名称。
            func: 处理函数，接收 Context，返回修改后的 Context（或 None）。
            retry_policy: 重试策略，None 使用默认策略（不重试）。
        """
        self.name = name
        self.func = func
        self.retry_policy = retry_policy or RetryPolicy(max_retries=0)

    def execute(self, context: Context) -> StageResult:
        """执行 Stage，返回 StageResult。

        根据重试策略在失败时自动重试。
        返回 None 时 Context 不变（透传）。

        Args:
            context: 当前上下文。

        Returns:
            StageResult 执行结果。
        """
        input_snapshot = context.snapshot()
        start = time.perf_counter()
        attempts = 1
        error: Exception | None = None

        while True:
            try:
                result = self.func(context)
                if result is not None and not isinstance(result, Context):
                    return result
                duration = (time.perf_counter() - start) * 1000
                return StageResult(
                    name=self.name,
                    status=StageStatus.SUCCESS,
                    duration_ms=duration,
                    attempts=attempts,
                    input_snapshot=input_snapshot,
                    output_snapshot=context.snapshot(),
                )
            except StopPipeline:
                raise
            except Exception as exc:
                error = exc
                if self.retry_policy.should_retry(exc, attempts):
                    delay = self.retry_policy.get_delay(attempts)
                    time.sleep(delay)
                    attempts += 1
                    continue
                break

        duration = (time.perf_counter() - start) * 1000
        return StageResult(
            name=self.name,
            status=StageStatus.FAILED,
            duration_ms=duration,
            attempts=attempts,
            error=error,
            input_snapshot=input_snapshot,
            output_snapshot=context.snapshot(),
        )


class Branch:
    """条件分支节点。

    根据条件函数的结果，选择执行不同的 Stage 列表。
    支持嵌套（Stage 列表中可包含其他 Branch）。
    """

    def __init__(
        self,
        name: str,
        condition: ConditionFunc,
        true_stages: list["Stage | Branch"],
        false_stages: list["Stage | Branch"] | None = None,
    ) -> None:
        """初始化条件分支。

        Args:
            name: 分支节点名称。
            condition: 条件函数，接收 Context 返回 bool。
            true_stages: 条件为 True 时执行的节点列表。
            false_stages: 条件为 False 时执行的节点列表（可选）。
        """
        self.name = name
        self.condition = condition
        self.true_stages = true_stages
        self.false_stages = false_stages or []


class Pipeline:
    """数据处理管道，编排 Stage 的执行。

    支持线性执行、条件分支、错误处理和重试。
    失败时采用 Fail-Fast 策略，立即中止并生成报告。
    """

    def __init__(self, name: str) -> None:
        """初始化 Pipeline。

        Args:
            name: Pipeline 名称。
        """
        self.name = name
        self._nodes: list[Stage | Branch] = []

    def add_stage(self, stage: Stage | Branch) -> "Pipeline":
        """添加 Stage 或 Branch，支持链式调用。

        Args:
            stage: Stage 或 Branch 节点。

        Returns:
            self，支持链式调用。
        """
        self._nodes.append(stage)
        return self

    def _count_stages(self, nodes: list[Stage | Branch] | None = None) -> int:
        """递归计算所有 Stage 数量。"""
        if nodes is None:
            nodes = self._nodes
        count = 0
        for node in nodes:
            if isinstance(node, Stage):
                count += 1
            elif isinstance(node, Branch):
                count += 1  # Branch 本身算一个节点
                count += self._count_stages(node.true_stages)
                count += self._count_stages(node.false_stages)
        return count

    def _execute_nodes(
        self,
        nodes: list[Stage | Branch],
        context: Context,
        report: PipelineReport,
        error_chain_prefix: str = "",
    ) -> bool:
        """执行节点列表。

        Args:
            nodes: 要执行的节点列表。
            context: 当前上下文。
            report: 报告对象（会被修改）。
            error_chain_prefix: 错误链前缀（用于嵌套分支）。

        Returns:
            True 表示全部成功，False 表示有失败。
        """
        for node in nodes:
            if isinstance(node, Stage):
                result = node.execute(context)
                report.stage_results.append(result)
                if result.status == StageStatus.SUCCESS:
                    report.succeeded += 1
                else:
                    report.failed += 1
                    report.error_chain.append(
                        f"{error_chain_prefix}{node.name}: "
                        f"{result.error}"
                    )
                    return False

            elif isinstance(node, Branch):
                branch_result = self._execute_branch(
                    node, context, report, error_chain_prefix
                )
                if not branch_result:
                    return False

        return True

    def _execute_branch(
        self,
        branch: Branch,
        context: Context,
        report: PipelineReport,
        error_chain_prefix: str = "",
    ) -> bool:
        """执行条件分支。

        Args:
            branch: Branch 节点。
            context: 当前上下文。
            report: 报告对象。
            error_chain_prefix: 错误链前缀。

        Returns:
            True 表示分支执行成功。
        """
        prefix = f"{error_chain_prefix}{branch.name} → "
        try:
            condition_result = branch.condition(context)
        except Exception as exc:
            report.failed += 1
            report.stage_results.append(
                StageResult(
                    name=f"{branch.name} (condition)",
                    status=StageStatus.FAILED,
                    error=exc,
                )
            )
            report.error_chain.append(f"{prefix}condition check: {exc}")
            return False

        if condition_result:
            ok = self._execute_nodes(
                branch.true_stages, context, report, prefix
            )
        else:
            if branch.false_stages:
                ok = self._execute_nodes(
                    branch.false_stages, context, report, prefix
                )
            else:
                ok = True

        if ok:
            report.succeeded += 1
            report.stage_results.append(
                StageResult(
                    name=f"{branch.name}",
                    status=StageStatus.SUCCESS,
                )
            )
        return ok

    def run(self, initial_data: dict | None = None) -> PipelineReport:
        """执行整个 Pipeline。

        Args:
            initial_data: 初始数据字典。

        Returns:
            PipelineReport 汇总报告。
        """
        context = Context(initial_data)
        report = PipelineReport(
            pipeline_name=self.name,
            total_stages=self._count_stages(),
        )

        start = time.perf_counter()
        success = True

        try:
            success = self._execute_nodes(
                self._nodes, context, report
            )
        except StopPipeline as exc:
            skipped_count = report.total_stages - (
                report.succeeded + report.failed
            )
            report.skipped = max(0, skipped_count)
            report.error_chain.append(f"Stopped: {exc.message}")

        report.total_duration_ms = (time.perf_counter() - start) * 1000
        report.final_context = context.to_dict()

        if success:
            report.skipped = 0
        elif report.skipped == 0 and not success:
            potential_skipped = report.total_stages - (
                report.succeeded + report.failed
            )
            if potential_skipped > 0:
                report.skipped = potential_skipped

        return report
