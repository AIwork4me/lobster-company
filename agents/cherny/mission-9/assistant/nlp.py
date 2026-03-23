"""自然语言命令解析器。

基于规则的中文意图识别与实体提取，覆盖常见表达模式。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Optional, List
import re

from .config import CATEGORY_KEYWORDS, DEFAULT_REVIEW_DAYS


@dataclass
class Command:
    """解析后的结构化命令。"""

    intent: str  # create_todo, list_todos, complete, delete,
                 # add_bookmark, list_bookmarks, daily_summary,
                 # stats, help, unknown
    content: str = ""
    deadline: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    person: Optional[str] = None
    url: Optional[str] = None
    todo_id: Optional[int] = None


# ─── URL 提取 ───────────────────────────────────────────

_URL_RE = re.compile(r"https?://\S+")


def _extract_url(text: str) -> Optional[str]:
    """提取文本中的第一个 URL。"""
    match = _URL_RE.search(text)
    return match.group(0).rstrip(".,;:!?，。；：！？") if match else None


# ─── 标签提取 ────────────────────────────────────────────

_TAG_RE = re.compile(r"#(\S+)")


def _extract_tags(text: str) -> List[str]:
    """提取 #标签。"""
    return _TAG_RE.findall(text)


# ─── 关联人提取 ──────────────────────────────────────────

_PERSON_RE = re.compile(
    r"(?:发给|告诉|和|找|给|约|联系|提醒)([\u4e00-\u9fff]{2,3})"
)
_NON_NAME_SUFFIX = {
    "下", "上", "晚", "早", "午", "去", "来",
    "开", "周", "月", "号", "日", "年", "说",
}


def _extract_person(text: str) -> Optional[str]:
    """提取关联人名（2-3 字中文人名）。"""
    match = _PERSON_RE.search(text)
    if not match:
        return None
    name = match.group(1)
    while len(name) > 2 and name[-1] in _NON_NAME_SUFFIX:
        name = name[:-1]
    if 2 <= len(name) <= 3:
        return name
    return None


# ─── 时间提取 ────────────────────────────────────────────

_WEEKDAY_MAP = {
    "周一": 0, "星期一": 0, "礼拜一": 0,
    "周二": 1, "星期二": 1, "礼拜二": 1,
    "周三": 2, "星期三": 2, "礼拜三": 2,
    "周四": 3, "星期四": 3, "礼拜四": 3,
    "周五": 4, "星期五": 4, "礼拜五": 4,
    "周六": 5, "星期六": 5, "礼拜六": 5,
    "周日": 6, "星期日": 6, "礼拜日": 6, "周末": 5,
}

_CN_NUM_MAP = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3,
    "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    "十": 10, "十二": 12, "十一": 11,
}

_TIME_RE = re.compile(
    r"(?:上午|早上?|早晨?|下午|晚上|夜里|中午|傍晚)?"
    r"([\d零一二两三四五六七八九十]+)"
    r"(?::(\d{2}))?"
    r"(?:点|时)"  # 必须有"点"或"时"才视为时间
    r"(?:半|三十)?"
)
_DATE_MD_RE = re.compile(r"(\d{1,2})月(\d{1,2})[日号]")
_RELATIVE_DAY_RE = re.compile(r"(\d+)天后")
_WEEKDAY_IN_TEXT_RE = re.compile(
    r"(?:本|这)周(" + "|".join(_WEEKDAY_MAP.keys()) + ")"
)
_NEXT_WEEKDAY_RE = re.compile(
    r"下周(" + "|".join(_WEEKDAY_MAP.keys()) + ")"
)

_DAY_OFFSETS = {"今天": 0, "明天": 1, "后天": 2, "大后天": 3}

_PERIOD_MAP = {
    "上午": 0, "早上": 0, "早晨": 0, "中午": 12,
    "下午": 12, "傍晚": 17, "晚上": 19, "夜里": 21,
}


def _resolve_hour(match_str: str, hour: int, minute: int) -> tuple:
    """根据时间段词修正小时数。返回 (hour, minute)。"""
    hour_offset = 0
    for period, offset in _PERIOD_MAP.items():
        if period in match_str:
            hour_offset = offset
            break

    if hour_offset > 0 and hour < 12:
        hour += hour_offset

    if hour_offset == 0 and hour <= 5 and "晚上" in match_str:
        hour += 12

    return hour, minute


def _cn_to_int(text: str) -> Optional[int]:
    """将中文数字转换为整数。"""
    if text.isdigit():
        return int(text)
    if text in _CN_NUM_MAP:
        return _CN_NUM_MAP[text]
    return None


def _parse_time_of_day(text: str, base_date: date) -> Optional[datetime]:
    """从文本中提取一天中的具体时间。"""
    match = _TIME_RE.search(text)
    if not match:
        return None

    hour_raw = _cn_to_int(match.group(1))
    if hour_raw is None:
        return None
    hour = hour_raw
    minute = int(match.group(2)) if match.group(2) else 0

    if "半" in text or "三十" in text:
        minute = 30

    hour, minute = _resolve_hour(text, hour, minute)

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None

    time_obj = datetime.min.time().replace(hour=hour, minute=minute)
    return datetime.combine(base_date, time_obj)


def _extract_date_offset(text: str) -> Optional[int]:
    """提取日期偏移量（今天=0, 明天=1, etc.）。"""
    for word, offset in _DAY_OFFSETS.items():
        if word in text:
            return offset
    rel_match = _RELATIVE_DAY_RE.search(text)
    if rel_match:
        return int(rel_match.group(1))
    return None


def _extract_specific_date(text: str, today: date) -> Optional[date]:
    """提取具体日期（X月X日、本周X、下周X）。"""
    now = datetime.now()

    # X月X日
    md_match = _DATE_MD_RE.search(text)
    if md_match:
        month, day = int(md_match.group(1)), int(md_match.group(2))
        try:
            target = date(now.year, month, day)
            if target < today:
                target = target.replace(year=now.year + 1)
            return target
        except ValueError:
            return None

    # 下周X
    next_match = _NEXT_WEEKDAY_RE.search(text)
    if next_match:
        wd = _WEEKDAY_MAP.get(next_match.group(1))
        if wd is not None:
            days_ahead = (wd - today.weekday()) % 7 or 7
            return today + timedelta(days=days_ahead + 7)

    # 本周X
    this_match = _WEEKDAY_IN_TEXT_RE.search(text)
    if this_match:
        wd = _WEEKDAY_MAP.get(this_match.group(1))
        if wd is not None:
            days_ahead = (wd - today.weekday()) % 7 or 7
            return today + timedelta(days=days_ahead)

    # 周末
    if "周末" in text:
        days_to_sat = (5 - today.weekday()) % 7 or 1
        return today + timedelta(days=days_to_sat)

    return None


def _combine_date_time(
    base_date: Optional[date], time_part: Optional[datetime], now: datetime
) -> Optional[datetime]:
    """组合日期和时间，验证不过期。"""
    if time_part and base_date:
        result = time_part.replace(
            year=base_date.year, month=base_date.month, day=base_date.day
        )
        return result if result >= now else None

    if base_date:
        return datetime.combine(
            base_date, datetime.min.time().replace(hour=9, minute=0)
        )

    return time_part


def extract_time(text: str) -> Optional[datetime]:
    """从中文文本中提取时间，返回 datetime 或 None。"""
    now = datetime.now()
    today = now.date()

    target_date = _extract_specific_date(text, today)
    day_offset = _extract_date_offset(text) if target_date is None else None

    base_date = target_date
    if base_date is None and day_offset is not None:
        base_date = today + timedelta(days=day_offset)

    ref_date = base_date if base_date else today
    time_part = _parse_time_of_day(text, ref_date)

    return _combine_date_time(base_date, time_part, now)


def extract_review_time(text: str) -> Optional[datetime]:
    """提取回顾时间（用于收藏功能）。"""
    now = datetime.now()
    today = now.date()

    if "周末" in text:
        days_to_sat = (5 - today.weekday()) % 7 or 1
        review_date = today + timedelta(days=days_to_sat)
        return datetime.combine(
            review_date, datetime.min.time().replace(hour=9)
        )

    rel_match = _RELATIVE_DAY_RE.search(text)
    if rel_match:
        return now + timedelta(days=int(rel_match.group(1)))

    return now + timedelta(days=DEFAULT_REVIEW_DAYS)


def classify_content(content: str, url: Optional[str]) -> str:
    """根据关键词自动分类内容。"""
    combined = content + (" " + url if url else "")
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return "未分类"


# ─── 内容清理 ────────────────────────────────────────────

_TIME_WORDS = [
    "今天", "明天", "后天", "大后天", "本周", "下周", "这周",
    "上午", "下午", "晚上", "早上", "中午", "傍晚", "夜里",
]
_ACTION_PREFIXES = [
    "帮我", "请", "麻烦", "提醒我", "加个待办", "新建待办",
    "添加待办", "记一下", "记得", "别忘了", "收藏", "保存",
]


def _strip_entities(text: str) -> str:
    """从文本中移除已解析的实体（URL、标签、时间词、人名上下文）。"""
    cleaned = _URL_RE.sub("", text)
    cleaned = _TAG_RE.sub("", cleaned)
    for word in _TIME_WORDS:
        cleaned = cleaned.replace(word, "")
    cleaned = re.sub(r"之前?$", "", cleaned)
    cleaned = re.sub(r"前把", "", cleaned)
    for prefix in _ACTION_PREFIXES:
        cleaned = cleaned.replace(prefix, "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.strip("，。、！？,.;:!? ")
    return cleaned


# ─── 意图检测 ────────────────────────────────────────────

_HELP_WORDS = {"帮助", "help", "怎么用", "使用说明", "命令"}
_STATS_WORDS = {"统计", "完成率", "逾期率", "数据", "复盘", "周报"}
_LIST_BOOKMARK_WORDS = {"待阅读", "收藏列表", "我的收藏", "待看"}
_COMPLETE_PREFIXES = ("完成了", "做完了", "搞定了", "已完成", "已做完")
_DELETE_WORDS = {"删除", "删掉", "取消", "移除"}
_LIST_KEYWORDS = {"什么", "待办", "任务", "事项", "安排", "该干",
                  "今天", "所有", "列表", "有哪些", "查看"}
_BOOKMARK_INTENT = {"收藏", "保存链接", "保存这个", "记一下链接",
                    "以后看", "稍后看", "待会看", "周末看"}
_CREATE_INDICATORS = {
    "创建", "加个", "新建", "添加", "帮忙", "提醒我",
    "记一下", "记得", "别忘了", "要做", "得做", "需要",
    "帮我", "请", "麻烦",
}


def _detect_intent(text: str, has_url: bool) -> str:
    """检测用户意图。返回 intent 字符串。"""
    lower = text.strip()

    if lower in _HELP_WORDS or lower == "?":
        return "help"

    if any(w in text for w in _STATS_WORDS):
        return "stats"

    if any(w in text for w in _LIST_BOOKMARK_WORDS):
        return "list_bookmarks"

    if any(text.startswith(p) for p in _COMPLETE_PREFIXES):
        return "complete"

    if any(text.startswith(w) for w in _DELETE_WORDS):
        return "delete"

    if has_url:
        if any(w in text for w in _BOOKMARK_INTENT):
            return "add_bookmark"
        return "add_bookmark"

    if any(w in text for w in _BOOKMARK_INTENT):
        return "add_bookmark"

    if any(w in text for w in _CREATE_INDICATORS):
        return "create_todo"

    if any(w in text for w in _LIST_KEYWORDS):
        return "list_todos"

    if "今天" in text and any(
        k in text for k in ("该干", "安排", "摘要", "要做什么")
    ):
        return "daily_summary"

    return "create_todo"


# ─── 待办 ID 提取 ─────────────────────────────────────────

_TODO_ID_RE = re.compile(r"#(\d+)")
_NUM_ID_RE = re.compile(r"(?:编号|ID|id)(?:\s*[：:=]\s*|\s+)(\d+)")


def _extract_todo_id(text: str) -> Optional[int]:
    """提取待办 ID。"""
    match = _TODO_ID_RE.search(text)
    if match:
        return int(match.group(1))
    match = _NUM_ID_RE.search(text)
    return int(match.group(1)) if match else None


# ─── 主入口 ──────────────────────────────────────────────

def parse_command(text: str) -> Command:
    """解析用户输入，返回结构化 Command。

    Args:
        text: 用户输入的自然语言文本

    Returns:
        Command 对象，包含 intent 和提取的实体
    """
    if not text or not text.strip():
        return Command(intent="unknown")

    url = _extract_url(text)
    tags = _extract_tags(text)
    person = _extract_person(text)
    intent = _detect_intent(text, url is not None)

    if intent in ("complete", "delete"):
        todo_id = _extract_todo_id(text)
        content = text if todo_id is None else _strip_entities(text)
        return Command(intent=intent, content=content, todo_id=todo_id)

    deadline = None
    content = text
    if intent == "create_todo":
        deadline = extract_time(text)
        content = _strip_entities(text)
    elif intent == "add_bookmark":
        content = _strip_entities(text)

    return Command(
        intent=intent,
        content=content,
        deadline=deadline,
        tags=tags,
        person=person,
        url=url,
    )
