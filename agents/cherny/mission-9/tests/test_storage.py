"""存储模块测试。"""

import sys
import os
import json
import shutil
import tempfile
import unittest

_test_dir = tempfile.mkdtemp()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import assistant.config as _cfg
_cfg.DATA_DIR = type(_cfg.DATA_DIR)(_test_dir)
_cfg.TODOS_FILE = _cfg.DATA_DIR / "todos.json"
_cfg.BOOKMARKS_FILE = _cfg.DATA_DIR / "bookmarks.json"

from assistant.storage import load_json, save_json


class TestStorage(unittest.TestCase):
    """JSON 持久化层测试。"""

    def test_save_and_load(self):
        data = [{"id": 1, "name": "test"}]
        save_json(config.TODOS_FILE, data)
        loaded = load_json(config.TODOS_FILE)
        self.assertEqual(loaded, data)

    def test_load_nonexistent(self):
        result = load_json(config.DATA_DIR / "nonexistent.json")
        self.assertEqual(result, [])

    def test_load_invalid_json(self):
        bad_file = config.DATA_DIR / "bad.json"
        bad_file.write_text("not json{{", encoding="utf-8")
        result = load_json(bad_file)
        self.assertEqual(result, [])

    def test_save_creates_directory(self):
        nested = config.DATA_DIR / "nested" / "deep" / "test.json"
        save_json(nested, [{"ok": True}])
        loaded = load_json(nested)
        self.assertEqual(loaded, [{"ok": True}])

    def test_save_empty_list(self):
        save_json(config.TODOS_FILE, [])
        loaded = load_json(config.TODOS_FILE)
        self.assertEqual(loaded, [])

    def test_unicode_handling(self):
        data = [{"content": "中文测试 🦞 标点符号"}]
        save_json(config.TODOS_FILE, data)
        loaded = load_json(config.TODOS_FILE)
        self.assertEqual(loaded[0]["content"], "中文测试 🦞 标点符号")

    def test_overwrite(self):
        save_json(config.TODOS_FILE, [{"id": 1}])
        save_json(config.TODOS_FILE, [{"id": 2}, {"id": 3}])
        loaded = load_json(config.TODOS_FILE)
        self.assertEqual(len(loaded), 2)


# Fix: use the patched config
config = _cfg


def _cleanup():
    try:
        shutil.rmtree(_test_dir, ignore_errors=True)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        _cleanup()
