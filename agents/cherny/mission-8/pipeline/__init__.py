"""Pipeline 框架 - 包入口。

导出核心 API，使用者通过 from pipeline import Pipeline, Stage, ... 访问。
"""

from .core import Pipeline, Stage, Branch
from .context import Context
from .result import StageResult, StageStatus, PipelineReport, StopPipeline
from .retry import RetryPolicy

__all__ = [
    "Pipeline",
    "Stage",
    "Branch",
    "Context",
    "StageResult",
    "StageStatus",
    "PipelineReport",
    "StopPipeline",
    "RetryPolicy",
]
