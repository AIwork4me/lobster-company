"""Core 模块测试 - Pipeline、Stage、Branch。"""

import unittest
from pipeline import (
    Pipeline,
    Stage,
    Branch,
    Context,
    StageStatus,
    StopPipeline,
    RetryPolicy,
)


class TestStageExecution(unittest.TestCase):
    """Stage 基本执行测试。"""

    def test_stage_success(self):
        def add_data(ctx: Context) -> Context:
            ctx.set("result", 42)
            return ctx

        stage = Stage("add_data", add_data)
        result = stage.execute(Context())
        self.assertEqual(result.status, StageStatus.SUCCESS)
        self.assertEqual(result.attempts, 1)
        self.assertIsNone(result.error)

    def test_stage_returns_none_passthrough(self):
        """Stage 返回 None 时 Context 不变。"""
        def noop(ctx: Context) -> Context:
            return None

        ctx = Context({"original": "yes"})
        stage = Stage("noop", noop)
        result = stage.execute(ctx)
        self.assertEqual(result.status, StageStatus.SUCCESS)
        self.assertTrue(ctx.has("original"))

    def test_stage_failure_no_retry(self):
        def fail_stage(ctx: Context) -> Context:
            raise ValueError("bad data")

        stage = Stage("fail", fail_stage)
        result = stage.execute(Context())
        self.assertEqual(result.status, StageStatus.FAILED)
        self.assertIsInstance(result.error, ValueError)
        self.assertEqual(result.attempts, 1)

    def test_stage_with_retry_succeed(self):
        call_count = 0

        def flaky(ctx: Context) -> Context:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temporary")
            ctx.set("done", True)
            return ctx

        policy = RetryPolicy(max_retries=5, backoff_base=0.01)
        stage = Stage("flaky", flaky, retry_policy=policy)
        result = stage.execute(Context())
        self.assertEqual(result.status, StageStatus.SUCCESS)
        self.assertEqual(result.attempts, 3)

    def test_stage_retry_exhausted(self):
        def always_fail(ctx: Context) -> Context:
            raise ConnectionError("down")

        policy = RetryPolicy(max_retries=2, backoff_base=0.01)
        stage = Stage("always_fail", always_fail, retry_policy=policy)
        result = stage.execute(Context())
        self.assertEqual(result.status, StageStatus.FAILED)
        self.assertEqual(result.attempts, 3)  # 1 first + 2 retries

    def test_stage_non_retryable_exception(self):
        def bad_data(ctx: Context) -> Context:
            raise ValueError("bad")

        policy = RetryPolicy(
            max_retries=5,
            non_retryable_exceptions=(ValueError,),
            backoff_base=0.01,
        )
        stage = Stage("bad", bad_data, retry_policy=policy)
        result = stage.execute(Context())
        self.assertEqual(result.status, StageStatus.FAILED)
        self.assertEqual(result.attempts, 1)

    def test_stage_stop_pipeline_propagates(self):
        def stopper(ctx: Context) -> Context:
            raise StopPipeline("done early")

        stage = Stage("stopper", stopper)
        with self.assertRaises(StopPipeline) as cm:
            stage.execute(Context())
        self.assertEqual(cm.exception.message, "done early")


class TestPipelineLinear(unittest.TestCase):
    """Pipeline 线性执行测试。"""

    def test_empty_pipeline(self):
        p = Pipeline("empty")
        report = p.run()
        self.assertEqual(report.succeeded, 0)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.total_stages, 0)

    def test_single_stage(self):
        def add_x(ctx: Context) -> Context:
            ctx.set("x", 1)
            return ctx

        p = Pipeline("single")
        p.add_stage(Stage("add_x", add_x))
        report = p.run()
        self.assertEqual(report.succeeded, 1)
        self.assertEqual(report.final_context["x"], 1)

    def test_multiple_stages_sequential(self):
        def add_a(ctx: Context) -> Context:
            ctx.set("a", 1)
            return ctx

        def add_b(ctx: Context) -> Context:
            ctx.set("b", ctx.get("a") + 1)
            return ctx

        def add_c(ctx: Context) -> Context:
            ctx.set("c", ctx.get("b") + 1)
            return ctx

        p = Pipeline("chain")
        p.add_stage(Stage("add_a", add_a))
        p.add_stage(Stage("add_b", add_b))
        p.add_stage(Stage("add_c", add_c))
        report = p.run()
        self.assertEqual(report.succeeded, 3)
        self.assertEqual(report.final_context, {"a": 1, "b": 2, "c": 3})

    def test_chain_add(self):
        """链式调用 add_stage。"""
        p = (Pipeline("chain")
             .add_stage(Stage("s1", lambda ctx: ctx))
             .add_stage(Stage("s2", lambda ctx: ctx)))
        report = p.run()
        self.assertEqual(report.succeeded, 2)

    def test_fail_fast(self):
        def ok(ctx: Context) -> Context:
            ctx.set("a", 1)
            return ctx

        def bad(ctx: Context) -> Context:
            raise RuntimeError("boom")

        def after(ctx: Context) -> Context:
            ctx.set("c", 3)
            return ctx

        p = Pipeline("fail_fast")
        p.add_stage(Stage("ok", ok))
        p.add_stage(Stage("bad", bad))
        p.add_stage(Stage("after", after))
        report = p.run()
        self.assertEqual(report.succeeded, 1)
        self.assertEqual(report.failed, 1)
        self.assertNotIn("c", report.final_context)

    def test_initial_data(self):
        def double(ctx: Context) -> Context:
            ctx.set("val", ctx.get("val") * 2)
            return ctx

        p = Pipeline("init")
        p.add_stage(Stage("double", double))
        report = p.run({"val": 5})
        self.assertEqual(report.final_context["val"], 10)

    def test_stage_with_snapshots(self):
        def transform(ctx: Context) -> Context:
            ctx.set("x", 999)
            return ctx

        stage = Stage("transform", transform)
        p = Pipeline("snap")
        p.add_stage(stage)
        report = p.run({"x": 0})
        r = report.stage_results[0]
        self.assertEqual(r.input_snapshot, {"x": 0})
        self.assertEqual(r.output_snapshot, {"x": 999})


class TestPipelineBranch(unittest.TestCase):
    """条件分支测试。"""

    def test_branch_true_path(self):
        p = Pipeline("branch_true")
        p.add_stage(Branch(
            name="check",
            condition=lambda ctx: ctx.get("value") > 10,
            true_stages=[Stage("high", lambda ctx: ctx.set("path", "high") or ctx)],
            false_stages=[Stage("low", lambda ctx: ctx.set("path", "low") or ctx)],
        ))
        report = p.run({"value": 20})
        self.assertEqual(report.succeeded, 2)
        self.assertEqual(report.final_context["path"], "high")

    def test_branch_false_path(self):
        p = Pipeline("branch_false")
        p.add_stage(Branch(
            name="check",
            condition=lambda ctx: ctx.get("value") > 10,
            true_stages=[Stage("high", lambda ctx: ctx.set("path", "high") or ctx)],
            false_stages=[Stage("low", lambda ctx: ctx.set("path", "low") or ctx)],
        ))
        report = p.run({"value": 5})
        self.assertEqual(report.succeeded, 2)
        self.assertEqual(report.final_context["path"], "low")

    def test_branch_no_false_stages(self):
        """false_stages 为空时，条件为 False 跳过。"""
        p = Pipeline("branch_no_false")
        p.add_stage(Branch(
            name="check",
            condition=lambda ctx: False,
            true_stages=[Stage("x", lambda ctx: ctx)],
            false_stages=None,
        ))
        report = p.run()
        self.assertEqual(report.succeeded, 1)  # only branch node counted

    def test_branch_condition_error(self):
        """条件函数抛异常时报告失败。"""
        def bad_condition(ctx: Context) -> bool:
            raise TypeError("not comparable")

        p = Pipeline("branch_error")
        p.add_stage(Branch(
            name="bad_branch",
            condition=bad_condition,
            true_stages=[Stage("x", lambda ctx: ctx)],
        ))
        report = p.run()
        self.assertEqual(report.failed, 1)
        self.assertTrue(len(report.error_chain) > 0)

    def test_branch_failure_in_true_path(self):
        """true_stages 中有失败时 Fail-Fast。"""
        p = Pipeline("branch_fail")
        p.add_stage(Branch(
            name="check",
            condition=lambda ctx: True,
            true_stages=[
                Stage("fail_inner", lambda ctx: (_ for _ in ()).throw(RuntimeError("inner fail"))),
            ],
            false_stages=[Stage("safe", lambda ctx: ctx)],
        ))
        report = p.run()
        self.assertEqual(report.failed, 1)

    def test_nested_branch(self):
        """嵌套 Branch。"""
        p = Pipeline("nested")
        p.add_stage(Branch(
            name="outer",
            condition=lambda ctx: ctx.get("level1") == "A",
            true_stages=[
                Branch(
                    name="inner",
                    condition=lambda ctx: ctx.get("level2") == "X",
                    true_stages=[
                        Stage("ax", lambda ctx: ctx.set("result", "AX") or ctx),
                    ],
                    false_stages=[
                        Stage("a_other", lambda ctx: ctx.set("result", "A_other") or ctx),
                    ],
                ),
            ],
            false_stages=[
                Stage("not_a", lambda ctx: ctx.set("result", "not_A") or ctx),
            ],
        ))
        report = p.run({"level1": "A", "level2": "X"})
        self.assertEqual(report.succeeded, 3)
        self.assertEqual(report.final_context["result"], "AX")

    def test_branch_then_linear(self):
        """Branch 后面继续线性 Stage。"""
        p = Pipeline("branch_then_linear")
        p.add_stage(Branch(
            name="check",
            condition=lambda ctx: ctx.get("flag"),
            true_stages=[Stage("yes", lambda ctx: ctx.set("choice", "yes") or ctx)],
        ))
        p.add_stage(Stage("final", lambda ctx: ctx.set("done", True) or ctx))

        report = p.run({"flag": True})
        self.assertEqual(report.succeeded, 3)
        self.assertEqual(report.final_context["choice"], "yes")
        self.assertTrue(report.final_context["done"])


class TestPipelineStop(unittest.TestCase):
    """StopPipeline 提前终止测试。"""

    def test_stop_in_stage(self):
        def stage1(ctx: Context) -> Context:
            ctx.set("s1", True)
            return ctx

        def stage2(ctx: Context) -> Context:
            raise StopPipeline("stopped at stage 2")

        def stage3(ctx: Context) -> Context:
            ctx.set("s3", True)
            return ctx

        p = Pipeline("stop_test")
        p.add_stage(Stage("s1", stage1))
        p.add_stage(Stage("s2", stage2))
        p.add_stage(Stage("s3", stage3))
        report = p.run()

        self.assertEqual(report.succeeded, 1)
        self.assertTrue(report.final_context["s1"])
        self.assertFalse(report.final_context.get("s3"))
        self.assertTrue(any("stopped at stage 2" in e for e in report.error_chain))


class TestPipelineReport(unittest.TestCase):
    """Pipeline 报告质量测试。"""

    def test_duration_recorded(self):
        def slow(ctx: Context) -> Context:
            import time
            time.sleep(0.05)
            return ctx

        p = Pipeline("duration")
        p.add_stage(Stage("slow", slow))
        report = p.run()
        self.assertGreater(report.total_duration_ms, 40)
        self.assertGreater(report.stage_results[0].duration_ms, 40)

    def test_report_summary_readable(self):
        p = Pipeline("readable")
        p.add_stage(Stage("a", lambda ctx: ctx))
        report = p.run()
        text = report.summary()
        self.assertIn("Pipeline: readable", text)

    def test_to_dict_completeness(self):
        p = Pipeline("dict")
        p.add_stage(Stage("a", lambda ctx: ctx))
        report = p.run({"x": 1})
        d = report.to_dict()
        self.assertEqual(d["pipeline_name"], "dict")
        self.assertEqual(d["succeeded"], 1)
        self.assertEqual(len(d["stage_results"]), 1)
        self.assertEqual(d["final_context"], {"x": 1})


if __name__ == "__main__":
    unittest.main()
