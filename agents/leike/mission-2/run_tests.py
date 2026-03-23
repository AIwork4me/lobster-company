"""运行 Leike 补充测试。"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "cherny", "mission-10"))
import unittest
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover(".", pattern="test_leike_supplement.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
