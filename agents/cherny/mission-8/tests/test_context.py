"""Context 模块测试。"""

import unittest
from pipeline.context import Context


class TestContextBasic(unittest.TestCase):
    """Context 基本操作测试。"""

    def test_create_empty(self):
        ctx = Context()
        self.assertEqual(ctx.to_dict(), {})

    def test_create_with_data(self):
        ctx = Context({"name": "test", "count": 42})
        self.assertEqual(ctx.get("name"), "test")
        self.assertEqual(ctx.get("count"), 42)

    def test_create_copies_input(self):
        original = {"key": "value"}
        ctx = Context(original)
        original["key"] = "modified"
        self.assertEqual(ctx.get("key"), "value")

    def test_set_and_get(self):
        ctx = Context()
        ctx.set("x", 100)
        self.assertEqual(ctx.get("x"), 100)

    def test_get_default(self):
        ctx = Context()
        self.assertIsNone(ctx.get("missing"))
        self.assertEqual(ctx.get("missing", "fallback"), "fallback")

    def test_has_key(self):
        ctx = Context()
        self.assertFalse(ctx.has("key"))
        ctx.set("key", "value")
        self.assertTrue(ctx.has("key"))

    def test_remove_existing(self):
        ctx = Context({"key": "value"})
        ctx.remove("key")
        self.assertFalse(ctx.has("key"))
        self.assertIsNone(ctx.get("key"))

    def test_remove_nonexistent(self):
        ctx = Context()
        ctx.remove("nope")  # should not raise
        self.assertEqual(ctx.to_dict(), {})

    def test_to_dict(self):
        ctx = Context({"a": 1, "b": 2})
        d = ctx.to_dict()
        self.assertEqual(d, {"a": 1, "b": 2})
        d["a"] = 999
        self.assertEqual(ctx.get("a"), 1)  # 不受影响


class TestContextSnapshot(unittest.TestCase):
    """Context 快照测试。"""

    def test_snapshot_is_deep_copy(self):
        inner = {"items": [1, 2, 3]}
        ctx = Context({"data": inner})
        snap = ctx.snapshot()
        snap["data"]["items"].append(4)
        self.assertEqual(ctx.get("data")["items"], [1, 2, 3])

    def test_snapshot_of_empty(self):
        ctx = Context()
        snap = ctx.snapshot()
        self.assertEqual(snap, {})

    def test_snapshot_preserves_all_keys(self):
        ctx = Context({"a": 1, "b": "hello", "c": [1, 2]})
        snap = ctx.snapshot()
        self.assertEqual(snap, {"a": 1, "b": "hello", "c": [1, 2]})


class TestContextRepr(unittest.TestCase):
    """Context repr 测试。"""

    def test_repr_empty(self):
        ctx = Context()
        self.assertEqual(repr(ctx), "Context(keys=[])")

    def test_repr_with_keys(self):
        ctx = Context({"x": 1, "y": 2})
        r = repr(ctx)
        self.assertIn("x", r)
        self.assertIn("y", r)


if __name__ == "__main__":
    unittest.main()
