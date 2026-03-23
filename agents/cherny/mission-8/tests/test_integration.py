"""集成测试 - 完整的数据处理场景。"""

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


class TestDataProcessingPipeline(unittest.TestCase):
    """模拟真实的数据处理场景：读取→清洗→验证→转换→输出。"""

    def test_complete_pipeline(self):
        """完整的 ETL Pipeline。"""
        # 模拟原始数据
        raw_data = {
            "records": [
                {"name": "Alice", "age": "30", "email": "alice@example.com"},
                {"name": "Bob", "age": "abc", "email": "invalid"},
                {"name": "", "age": "25", "email": "charlie@test.com"},
            ],
        }

        # Stage 1: 清洗 - 移除无效记录
        def clean(ctx: Context) -> Context:
            records = ctx.get("records", [])
            cleaned = []
            for r in records:
                if r.get("name") and isinstance(r.get("age"), (int, str)) and r["age"].isdigit():
                    cleaned.append(r)
            ctx.set("cleaned", cleaned)
            ctx.set("removed_count", len(records) - len(cleaned))
            return ctx

        # Stage 2: 验证 - 检查数据完整性
        def validate(ctx: Context) -> Context:
            cleaned = ctx.get("cleaned", [])
            issues = []
            for i, r in enumerate(cleaned):
                if not r.get("email") or "@" not in r.get("email", ""):
                    issues.append(f"Record {i}: invalid email")
            ctx.set("issues", issues)
            ctx.set("is_valid", len(issues) == 0)
            return ctx

        # Stage 3: 转换 - 添加处理时间戳
        def transform(ctx: Context) -> Context:
            import datetime
            cleaned = ctx.get("cleaned", [])
            for r in cleaned:
                r["processed_at"] = datetime.datetime.now().isoformat()
            ctx.set("transformed", cleaned)
            return ctx

        # Stage 4: 输出 - 汇总统计
        def summarize(ctx: Context) -> Context:
            transformed = ctx.get("transformed", [])
            ctx.set("output", {
                "total_input": 3,
                "total_cleaned": len(transformed),
                "removed": ctx.get("removed_count", 0),
                "records": transformed,
            })
            return ctx

        p = Pipeline("etl_pipeline")
        p.add_stage(Stage("clean", clean))
        p.add_stage(Stage("validate", validate))
        p.add_stage(Stage("transform", transform))
        p.add_stage(Stage("summarize", summarize))

        report = p.run(raw_data)
        self.assertEqual(report.succeeded, 4)
        output = report.final_context["output"]
        self.assertEqual(output["total_input"], 3)
        self.assertEqual(output["total_cleaned"], 1)
        self.assertEqual(output["removed"], 2)

    def test_pipeline_with_validation_branch(self):
        """验证失败走不同分支。"""
        def load_data(ctx: Context) -> Context:
            ctx.set("data", [1, 2, 3, 4, 5])
            return ctx

        def check_threshold(ctx: Context) -> Context:
            data = ctx.get("data", [])
            ctx.set("sum", sum(data))
            ctx.set("above_threshold", sum(data) > 20)
            return ctx

        def process_high(ctx: Context) -> Context:
            ctx.set("tier", "high")
            return ctx

        def process_low(ctx: Context) -> Context:
            ctx.set("tier", "low")
            return ctx

        def finalize(ctx: Context) -> Context:
            ctx.set("done", True)
            return ctx

        p = Pipeline("threshold_pipeline")
        p.add_stage(Stage("load", load_data))
        p.add_stage(Stage("check", check_threshold))
        p.add_stage(Branch(
            name="route",
            condition=lambda ctx: ctx.get("above_threshold"),
            true_stages=[Stage("high", process_high)],
            false_stages=[Stage("low", process_low)],
        ))
        p.add_stage(Stage("finalize", finalize))

        report = p.run()
        self.assertEqual(report.succeeded, 5)
        self.assertEqual(report.final_context["tier"], "low")
        self.assertTrue(report.final_context["done"])

    def test_retry_in_realistic_scenario(self):
        """模拟网络请求重试场景。"""
        attempt_log = []

        def fetch_data(ctx: Context) -> Context:
            attempt_log.append("fetch")
            if len(attempt_log) < 3:
                raise ConnectionError("Connection refused")
            ctx.set("fetched", [{"id": 1, "value": "hello"}])
            return ctx

        p = Pipeline("fetch_pipeline")
        p.add_stage(Stage(
            "fetch",
            fetch_data,
            retry_policy=RetryPolicy(
                max_retries=5,
                backoff_base=0.01,
            ),
        ))

        report = p.run()
        self.assertEqual(report.succeeded, 1)
        self.assertEqual(len(attempt_log), 3)
        self.assertEqual(report.stage_results[0].attempts, 3)

    def test_stop_pipeline_early_exit(self):
        """数据校验不通过时提前终止。"""
        def load(ctx: Context) -> Context:
            ctx.set("items", [{"id": 1}, {"id": 2}])
            return ctx

        def check_count(ctx: Context) -> Context:
            items = ctx.get("items", [])
            if len(items) < 5:
                raise StopPipeline(
                    f"数据不足: 需要5条，实际{len(items)}条"
                )
            return ctx

        def process(ctx: Context) -> Context:
            ctx.set("processed", True)
            return ctx

        p = Pipeline("early_exit")
        p.add_stage(Stage("load", load))
        p.add_stage(Stage("check_count", check_count))
        p.add_stage(Stage("process", process))

        report = p.run()
        self.assertEqual(report.succeeded, 1)
        self.assertFalse(report.final_context.get("processed"))
        self.assertTrue(any("数据不足" in e for e in report.error_chain))

    def test_empty_context_handling(self):
        """空上下文的边界情况。"""
        def read_empty(ctx: Context) -> Context:
            data = ctx.get("data", [])
            ctx.set("result", f"Got {len(data)} items")
            return ctx

        p = Pipeline("empty")
        p.add_stage(Stage("read", read_empty))
        report = p.run()
        self.assertEqual(report.succeeded, 1)
        self.assertEqual(report.final_context["result"], "Got 0 items")

    def test_multiple_branches_in_sequence(self):
        """多个分支串联。"""
        p = Pipeline("multi_branch")

        def set_flag(ctx: Context) -> Context:
            ctx.set("a", True)
            ctx.set("b", False)
            return ctx

        p.add_stage(Stage("set_flags", set_flag))
        p.add_stage(Branch(
            name="branch_a",
            condition=lambda ctx: ctx.get("a"),
            true_stages=[
                Stage("a_true", lambda ctx: ctx.set("a_result", "yes") or ctx),
            ],
        ))
        p.add_stage(Branch(
            name="branch_b",
            condition=lambda ctx: ctx.get("b"),
            true_stages=[
                Stage("b_true", lambda ctx: ctx.set("b_result", "yes") or ctx),
            ],
            false_stages=[
                Stage("b_false", lambda ctx: ctx.set("b_result", "no") or ctx),
            ],
        ))

        report = p.run()
        self.assertEqual(report.succeeded, 6)
        self.assertEqual(report.final_context["a_result"], "yes")
        self.assertEqual(report.final_context["b_result"], "no")


if __name__ == "__main__":
    unittest.main()
