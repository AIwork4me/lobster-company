"""Pipeline 框架 - 执行结果模块。

提供 Stage 结果记录和 Pipeline 汇总报告生成。
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StageStatus(Enum):
    """Stage 执行状态。"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class StopPipeline(Exception):
    """从 Stage 内部提前终止整个 Pipeline。

    用法:
        def my_stage(ctx: Context) -> Context:
            if ctx.get("count") > 100:
                raise StopPipeline("数量超限，终止处理")
            return ctx
    """

    def __init__(self, message: str = "Pipeline stopped by stage") -> None:
        self.message = message
        super().__init__(message)


@dataclass
class StageResult:
    """单个 Stage 的执行结果。"""
    name: str
    status: StageStatus
    duration_ms: float = 0.0
    attempts: int = 1
    error: Exception | None = None
    input_snapshot: dict | None = None
    output_snapshot: dict | None = None


@dataclass
class PipelineReport:
    """Pipeline 执行汇总报告。"""
    pipeline_name: str
    total_stages: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    total_duration_ms: float = 0.0
    stage_results: list[StageResult] = field(default_factory=list)
    error_chain: list[str] = field(default_factory=list)
    final_context: dict | None = None

    def summary(self) -> str:
        """生成人类可读的汇总文本。"""
        lines = [
            f"Pipeline: {self.pipeline_name}",
            f"Total: {self.total_stages} stages, "
            f"{self.total_duration_ms:.1f}ms",
            f"  ✓ Success: {self.succeeded}",
        ]
        if self.failed > 0:
            lines.append(f"  ✗ Failed:  {self.failed}")
        if self.skipped > 0:
            lines.append(f"  ○ Skipped: {self.skipped}")

        for result in self.stage_results:
            status_icon = {
                StageStatus.SUCCESS: "✓",
                StageStatus.FAILED: "✗",
                StageStatus.SKIPPED: "○",
            }[result.status]

            duration_str = f"{result.duration_ms:.1f}ms"
            line = f"  {status_icon} {result.name}: {result.status.value}"
            if result.attempts > 1:
                line += f" ({result.attempts} attempts)"
            line += f" [{duration_str}]"
            lines.append(line)

            if result.error is not None:
                lines.append(f"      Error: {result.error}")

        if self.error_chain:
            lines.append("Error chain:")
            for err in self.error_chain:
                lines.append(f"  → {err}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """导出为字典。"""
        return {
            "pipeline_name": self.pipeline_name,
            "total_stages": self.total_stages,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped,
            "total_duration_ms": self.total_duration_ms,
            "stage_results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "attempts": r.attempts,
                    "error": str(r.error) if r.error else None,
                }
                for r in self.stage_results
            ],
            "error_chain": self.error_chain,
            "final_context": self.final_context,
        }
