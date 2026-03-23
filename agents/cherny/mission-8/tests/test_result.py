"""Result 模块测试。"""

import unittest
from pipeline.result import (
    StageResult,
    StageStatus,
    PipelineReport,
    StopPipeline,
)


class TestStageResult(unittest.TestCase):
    """StageResult 数据类测试。"""

    def test_create_success(self):
        result = StageResult(
            name="test_stage",
            status=StageStatus.SUCCESS,
            duration_ms=10.5,
            attempts=1,
        )
        self.assertEqual(result.name, "test_stage")
        self.assertEqual(result.status, StageStatus.SUCCESS)
        self.assertAlmostEqual(result.duration_ms, 10.5)
        self.assertEqual(result.attempts, 1)
        self.assertIsNone(result.error)

    def test_create_failed(self):
        error = ValueError("bad data")
        result = StageResult(
            name="fail_stage",
            status=StageStatus.FAILED,
            error=error,
            attempts=3,
        )
        self.assertEqual(result.status, StageStatus.FAILED)
        self.assertEqual(result.error, error)
        self.assertEqual(result.attempts, 3)

    def test_default_values(self):
        result = StageResult(name="x", status=StageStatus.SUCCESS)
        self.assertAlmostEqual(result.duration_ms, 0.0)
        self.assertEqual(result.attempts, 1)
        self.assertIsNone(result.error)


class TestStopPipeline(unittest.TestCase):
    """StopPipeline 异常测试。"""

    def test_default_message(self):
        exc = StopPipeline()
        self.assertEqual(exc.message, "Pipeline stopped by stage")
        self.assertIn("stopped by stage", str(exc))

    def test_custom_message(self):
        exc = StopPipeline("数量超限")
        self.assertEqual(exc.message, "数量超限")
        self.assertIn("数量超限", str(exc))

    def test_is_exception(self):
        self.assertTrue(issubclass(StopPipeline, Exception))


class TestPipelineReport(unittest.TestCase):
    """PipelineReport 汇总报告测试。"""

    def test_empty_report(self):
        report = PipelineReport(pipeline_name="empty")
        self.assertEqual(report.pipeline_name, "empty")
        self.assertEqual(report.total_stages, 0)
        self.assertEqual(report.succeeded, 0)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.skipped, 0)
        self.assertEqual(report.stage_results, [])
        self.assertEqual(report.error_chain, [])

    def test_summary_success_only(self):
        report = PipelineReport(
            pipeline_name="test",
            total_stages=2,
            succeeded=2,
            total_duration_ms=100.0,
            stage_results=[
                StageResult(name="a", status=StageStatus.SUCCESS, duration_ms=50.0),
                StageResult(name="b", status=StageStatus.SUCCESS, duration_ms=50.0),
            ],
        )
        text = report.summary()
        self.assertIn("Pipeline: test", text)
        self.assertIn("✓ Success: 2", text)
        self.assertIn("✓ a:", text)
        self.assertIn("✓ b:", text)
        self.assertNotIn("✗", text)

    def test_summary_with_failure(self):
        report = PipelineReport(
            pipeline_name="fail_test",
            total_stages=2,
            succeeded=1,
            failed=1,
            total_duration_ms=200.0,
            stage_results=[
                StageResult(name="ok", status=StageStatus.SUCCESS, duration_ms=10.0),
                StageResult(
                    name="bad",
                    status=StageStatus.FAILED,
                    duration_ms=190.0,
                    error=ValueError("oops"),
                ),
            ],
            error_chain=["bad: oops"],
        )
        text = report.summary()
        self.assertIn("✗ Failed:  1", text)
        self.assertIn("✗ bad:", text)
        self.assertIn("Error: oops", text)
        self.assertIn("Error chain:", text)

    def test_summary_with_skipped(self):
        report = PipelineReport(
            pipeline_name="skip_test",
            total_stages=3,
            succeeded=1,
            skipped=2,
            total_duration_ms=10.0,
            stage_results=[
                StageResult(name="a", status=StageStatus.SUCCESS),
                StageResult(name="b", status=StageStatus.SKIPPED),
                StageResult(name="c", status=StageStatus.SKIPPED),
            ],
        )
        text = report.summary()
        self.assertIn("○ Skipped: 2", text)
        self.assertIn("○ b:", text)

    def test_summary_with_retry_attempts(self):
        report = PipelineReport(
            pipeline_name="retry_test",
            total_stages=1,
            succeeded=1,
            stage_results=[
                StageResult(
                    name="flaky",
                    status=StageStatus.SUCCESS,
                    attempts=3,
                    duration_ms=500.0,
                ),
            ],
        )
        text = report.summary()
        self.assertIn("(3 attempts)", text)

    def test_to_dict(self):
        report = PipelineReport(
            pipeline_name="dict_test",
            total_stages=1,
            succeeded=1,
            total_duration_ms=42.0,
            final_context={"key": "value"},
            stage_results=[
                StageResult(name="s1", status=StageStatus.SUCCESS),
            ],
        )
        d = report.to_dict()
        self.assertEqual(d["pipeline_name"], "dict_test")
        self.assertEqual(d["succeeded"], 1)
        self.assertEqual(len(d["stage_results"]), 1)
        self.assertEqual(d["stage_results"][0]["name"], "s1")
        self.assertEqual(d["final_context"], {"key": "value"})


if __name__ == "__main__":
    unittest.main()
