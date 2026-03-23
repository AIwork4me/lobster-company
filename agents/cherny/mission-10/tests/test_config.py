"""测试配置管理。"""

import json
import os
import tempfile
import unittest
from pr_queue.config import load_config, save_config
from pr_queue.models import Config


class TestConfigIO(unittest.TestCase):
    """配置加载和保存测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _tmp_path(self):
        return os.path.join(self.tmpdir, "config.json")

    def test_load_nonexistent_returns_default(self):
        config = load_config(self._tmp_path())
        self.assertIsInstance(config, Config)
        self.assertEqual(config.timeout_hours, 24)

    def test_save_and_load_roundtrip(self):
        config = Config(timeout_hours=36, tech_lead="alice")
        path = self._tmp_path()
        save_config(config, path)
        loaded = load_config(path)
        self.assertEqual(loaded.timeout_hours, 36)
        self.assertEqual(loaded.tech_lead, "alice")

    def test_saved_file_is_valid_json(self):
        config = Config(timeout_hours=12)
        path = self._tmp_path()
        save_config(config, path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["timeout_hours"], 12)

    def test_save_overwrites_existing(self):
        path = self._tmp_path()
        save_config(Config(timeout_hours=10), path)
        save_config(Config(timeout_hours=20), path)
        loaded = load_config(path)
        self.assertEqual(loaded.timeout_hours, 20)

    def test_load_preserves_complex_fields(self):
        config = Config(
            timeout_hours=48,
            high_risk_dirs=["payment", "auth"],
            reviewer_rules={"src/payment/**": ["alice", "bob"]},
        )
        path = self._tmp_path()
        save_config(config, path)
        loaded = load_config(path)
        self.assertEqual(loaded.reviewer_rules["src/payment/**"], ["alice", "bob"])

    def test_load_without_path_uses_default_filename(self):
        """不传路径时使用默认文件名。"""
        # 只测试不崩溃
        config = load_config("")
        self.assertIsInstance(config, Config)


if __name__ == "__main__":
    unittest.main()
