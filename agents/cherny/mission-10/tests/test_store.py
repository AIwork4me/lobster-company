"""测试 PR 数据存储。"""

import os
import tempfile
import unittest
from pr_queue.store import PRStore
from pr_queue.models import PullRequest, Review


def _make_pr(number=1, repo="test/repo", state="open"):
    return PullRequest(
        number=number, title=f"PR {number}", author="alice",
        repo=repo, state=state,
        created_at="2026-03-20T10:00:00Z",
        updated_at="2026-03-20T10:00:00Z",
        changed_files=["src/main.py"],
        reviewers=["bob"],
    )


class TestPRStore(unittest.TestCase):
    """PR 数据存储测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = PRStore(os.path.join(self.tmpdir, "data.json"))

    def test_add_and_get(self):
        pr = _make_pr(number=42)
        self.store.add(pr)
        result = self.store.get("test/repo", 42)
        self.assertIsNotNone(result)
        self.assertEqual(result.title, "PR 42")

    def test_get_nonexistent_returns_none(self):
        result = self.store.get("test/repo", 999)
        self.assertIsNone(result)

    def test_add_updates_existing(self):
        pr = _make_pr(number=1)
        self.store.add(pr)
        pr.title = "Updated PR 1"
        self.store.add(pr)
        result = self.store.get("test/repo", 1)
        self.assertEqual(result.title, "Updated PR 1")

    def test_get_all(self):
        self.store.add(_make_pr(number=1))
        self.store.add(_make_pr(number=2))
        self.store.add(_make_pr(number=3))
        all_prs = self.store.get_all()
        self.assertEqual(len(all_prs), 3)

    def test_get_open_prs(self):
        self.store.add(_make_pr(number=1, state="open"))
        self.store.add(_make_pr(number=2, state="closed"))
        self.store.add(_make_pr(number=3, state="merged"))
        self.store.add(_make_pr(number=4, state="open"))
        open_prs = self.store.get_open_prs()
        self.assertEqual(len(open_prs), 2)
        self.assertTrue(all(pr.is_open for pr in open_prs))

    def test_get_by_repo(self):
        self.store.add(_make_pr(number=1, repo="repo/a"))
        self.store.add(_make_pr(number=2, repo="repo/b"))
        self.store.add(_make_pr(number=3, repo="repo/a"))
        result = self.store.get_by_repo("repo/a")
        self.assertEqual(len(result), 2)

    def test_delete(self):
        self.store.add(_make_pr(number=1))
        self.assertTrue(self.store.delete("test/repo", 1))
        self.assertIsNone(self.store.get("test/repo", 1))

    def test_delete_nonexistent_returns_false(self):
        self.assertFalse(self.store.delete("test/repo", 999))

    def test_update_labels(self):
        self.store.add(_make_pr(number=1))
        self.assertTrue(self.store.update_labels("test/repo", 1, ["bugfix", "urgent"]))
        pr = self.store.get("test/repo", 1)
        self.assertEqual(pr.labels, ["bugfix", "urgent"])

    def test_update_labels_nonexistent_returns_false(self):
        self.assertFalse(self.store.update_labels("test/repo", 999, ["x"]))

    def test_reviews_preserved_after_save_load(self):
        pr = _make_pr(number=1)
        pr.reviews = [
            Review("bob", "approved", "LGTM", "2026-03-21T10:00:00Z"),
        ]
        self.store.add(pr)
        # 重新创建 store 模拟重启
        store2 = PRStore(os.path.join(self.tmpdir, "data.json"))
        loaded = store2.get("test/repo", 1)
        self.assertEqual(len(loaded.reviews), 1)
        self.assertEqual(loaded.reviews[0].reviewer, "bob")

    def test_empty_store(self):
        all_prs = self.store.get_all()
        self.assertEqual(len(all_prs), 0)


if __name__ == "__main__":
    unittest.main()
