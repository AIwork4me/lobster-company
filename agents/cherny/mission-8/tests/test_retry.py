"""RetryPolicy 模块测试。"""

import unittest
from pipeline.retry import RetryPolicy


class TestShouldRetry(unittest.TestCase):
    """should_retry 逻辑测试。"""

    def test_no_retry_by_default(self):
        policy = RetryPolicy()
        self.assertFalse(policy.should_retry(ValueError("err"), 1))
        self.assertFalse(policy.should_retry(ValueError("err"), 2))

    def test_retry_within_limit(self):
        policy = RetryPolicy(max_retries=3)
        self.assertTrue(policy.should_retry(ValueError("err"), 1))
        self.assertTrue(policy.should_retry(ValueError("err"), 2))
        self.assertTrue(policy.should_retry(ValueError("err"), 3))
        self.assertFalse(policy.should_retry(ValueError("err"), 4))

    def test_non_retryable_exception_skipped(self):
        policy = RetryPolicy(
            max_retries=5,
            non_retryable_exceptions=(ValueError,),
        )
        self.assertFalse(policy.should_retry(ValueError("err"), 1))
        self.assertTrue(policy.should_retry(RuntimeError("err"), 1))

    def test_non_retryable_takes_priority(self):
        """non_retryable 优先级高于 retryable。"""
        policy = RetryPolicy(
            max_retries=5,
            retryable_exceptions=(ValueError, RuntimeError),
            non_retryable_exceptions=(ValueError,),
        )
        self.assertFalse(policy.should_retry(ValueError("err"), 1))
        self.assertTrue(policy.should_retry(RuntimeError("err"), 1))

    def test_specific_retryable_only(self):
        policy = RetryPolicy(
            max_retries=3,
            retryable_exceptions=(ConnectionError, TimeoutError),
        )
        self.assertTrue(policy.should_retry(ConnectionError("err"), 1))
        self.assertTrue(policy.should_retry(TimeoutError("err"), 1))
        self.assertFalse(policy.should_retry(ValueError("err"), 1))

    def test_zero_max_retries(self):
        policy = RetryPolicy(max_retries=0)
        self.assertFalse(policy.should_retry(Exception("err"), 1))


class TestGetDelay(unittest.TestCase):
    """退避间隔计算测试。"""

    def test_exponential_backoff(self):
        policy = RetryPolicy(
            backoff_base=1.0,
            backoff_multiplier=2.0,
            max_backoff=30.0,
        )
        self.assertAlmostEqual(policy.get_delay(1), 1.0)
        self.assertAlmostEqual(policy.get_delay(2), 2.0)
        self.assertAlmostEqual(policy.get_delay(3), 4.0)
        self.assertAlmostEqual(policy.get_delay(4), 8.0)

    def test_max_backoff_cap(self):
        policy = RetryPolicy(
            backoff_base=1.0,
            backoff_multiplier=2.0,
            max_backoff=5.0,
        )
        self.assertAlmostEqual(policy.get_delay(1), 1.0)
        self.assertAlmostEqual(policy.get_delay(2), 2.0)
        self.assertAlmostEqual(policy.get_delay(3), 4.0)
        self.assertAlmostEqual(policy.get_delay(4), 5.0)  # capped
        self.assertAlmostEqual(policy.get_delay(5), 5.0)  # capped

    def test_custom_base(self):
        policy = RetryPolicy(
            backoff_base=0.5,
            backoff_multiplier=2.0,
            max_backoff=30.0,
        )
        self.assertAlmostEqual(policy.get_delay(1), 0.5)
        self.assertAlmostEqual(policy.get_delay(2), 1.0)


if __name__ == "__main__":
    unittest.main()
