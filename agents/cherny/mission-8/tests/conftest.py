"""测试路径配置。将项目根目录添加到 sys.path。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
