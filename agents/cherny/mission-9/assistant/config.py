"""配置常量与路径管理。"""

from pathlib import Path

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"

# 数据文件
TODOS_FILE = DATA_DIR / "todos.json"
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"

# 优先级权重
PRIORITY_OVERDUE = 1
PRIORITY_TODAY = 2
PRIORITY_WITHIN_3_DAYS = 3
PRIORITY_THIS_WEEK = 4
PRIORITY_LATER = 5
PRIORITY_NO_DEADLINE = 5

# 收藏分类关键词
CATEGORY_KEYWORDS = {
    "待阅读": ["文章", "阅读", "看", "读", "博客", "新闻", "资讯", "报道",
               "/article", "/blog", "/news", "/post", "/story", "/read"],
    "学习资料": ["学习", "教程", "课程", "培训", "学习资料", "笔记",
                 "/tutorial", "/course", "/learn", "/guide"],
    "工具推荐": ["工具", "软件", "App", "应用", "插件", "扩展",
                 "/tool", "/app", "/plugin", "/extension"],
}

# 收藏默认回顾天数
DEFAULT_REVIEW_DAYS = 7

# 周末映射
WEEKEND_DAYS = {5, 6}  # 周六=5, 周日=6 (Python weekday)
