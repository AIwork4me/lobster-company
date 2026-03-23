"""Pipeline 框架 - 重试策略模块。

提供 Stage 级别的重试控制，支持指数退避和异常过滤。
"""

import time
from typing import Any


class RetryPolicy:
    """Stage 级别的重试策略。

    支持配置重试次数、指数退避间隔、异常类型过滤。
    non_retryable_exceptions 优先级高于 retryable_exceptions。
    """

    def __init__(
        self,
        max_retries: int = 0,
        backoff_base: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff: float = 30.0,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
        non_retryable_exceptions: tuple[type[Exception], ...] = (),
    ) -> None:
        """初始化重试策略。

        Args:
            max_retries: 最大重试次数（不含首次执行）。0 = 不重试。
            backoff_base: 首次重试等待秒数。
            backoff_multiplier: 退避倍数（指数退避）。
            max_backoff: 最大等待秒数。
            retryable_exceptions: 允许重试的异常类型。默认所有异常。
            non_retryable_exceptions: 明确不重试的异常类型（优先级更高）。
        """
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
        self.retryable_exceptions = retryable_exceptions
        self.non_retryable_exceptions = non_retryable_exceptions

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试。

        Args:
            error: 捕获到的异常。
            attempt: 已执行次数（1 = 首次执行）。

        Returns:
            是否应该重试。
        """
        if attempt - 1 >= self.max_retries:
            return False

        if isinstance(error, self.non_retryable_exceptions):
            return False

        return isinstance(error, self.retryable_exceptions)

    def get_delay(self, attempt: int) -> float:
        """获取第 N 次重试的等待时间（秒）。

        使用指数退避: min(base * multiplier^(attempt-1), max_backoff)

        Args:
            attempt: 重试序号（1 = 第一次重试）。

        Returns:
            等待秒数。
        """
        delay = self.backoff_base * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_backoff)
