"""
Web Summarizer - 网页摘要提取器
Cherny @ Lobster Company | Mission 1
零外部依赖（仅 Python 标准库），抓取网页正文 + 智谱 API 结构化摘要
"""

import os
import sys
import re
import json
import ssl
import urllib.request
import urllib.error
from html.parser import HTMLParser

# ─── 配置 ───────────────────────────────────────────────

API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-flash"
TIMEOUT = 15
MAX_CONTENT = 6000

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# ─── API Key 加载 ───────────────────────────────────────

def load_api_key() -> str:
    """从 .env 文件或环境变量加载 ZHIPU_API_KEY"""
    for p in [os.path.join(os.path.dirname(__file__), ".env"),
              os.path.join(os.path.dirname(__file__), "..", ".env")]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("ZHIPU_API_KEY=") and not line.startswith("#"):
                        return line.split("=", 1)[1].strip()
    key = os.environ.get("ZHIPU_API_KEY", "")
    if not key:
        sys.exit("错误：未找到 ZHIPU_API_KEY，请在 .env 或环境变量中配置")
    return key


# ─── HTTP 请求封装 ─────────────────────────────────────

def http_get(url: str, extra_headers: dict = None) -> str:
    """GET 请求，返回解码后的文本"""
    headers = {"User-Agent": BROWSER_UA}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ssl_ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def http_post_json(url: str, payload: dict, api_key: str = "") -> dict:
    """发送 JSON POST 请求，返回解析后的 JSON"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {e.code}: {detail}")


# ─── HTML 正文提取器 ───────────────────────────────────

class TextExtractor(HTMLParser):
    """
    轻量 HTML → 纯文本提取器
    跳过 script/style/svg，按块级标签分断
    """

    SKIP = frozenset({"script", "style", "noscript", "svg", "head"})
    BLOCK = frozenset({"p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
                       "li", "br", "hr", "blockquote", "pre", "tr"})

    def __init__(self):
        super().__init__()
        self._skip = 0
        self._buf = ""
        self.chunks: list[str] = []
        self.title = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP:
            self._skip += 1
            return
        if self._skip > 0:
            return
        if tag in self.BLOCK:
            self._flush()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP:
            self._skip = max(0, self._skip - 1)
            return

    def handle_data(self, data):
        if self._skip > 0:
            return
        self._buf += data

    def _flush(self):
        text = " ".join(self._buf.split())
        if text:
            self.chunks.append(text)
        self._buf = ""

    def get_text(self, min_len: int = 10) -> str:
        self._flush()
        return "\n".join(c for c in self.chunks if len(c) >= min_len)


def extract_title(html: str) -> str:
    """从 <title> 标签提取网页标题"""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return m.group(1).strip() if m else ""


def extract_meta_description(html: str) -> str:
    """从 meta 标签提取 description（补充标题信息）"""
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.I | re.S)
    return m.group(1).strip() if m else ""


def fetch_and_extract(url: str) -> dict:
    """抓取 URL，提取标题 + 正文"""
    if not re.match(r"https?://\S+", url):
        raise ValueError(f"无效的 URL：{url}")

    html = http_get(url)

    ext = TextExtractor()
    ext.feed(html)
    text = ext.get_text()
    title = extract_title(html)
    desc = extract_meta_description(html)

    # 如果提取失败，用 fallback 方法：暴力去标签
    if not text.strip():
        body = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
        if body:
            raw = re.sub(r"<[^>]+>", " ", body.group(1))
            raw = re.sub(r"&[a-zA-Z]+;", " ", raw)
            text = "\n".join(
                line.strip() for line in raw.split("\n")
                if len(line.strip()) >= 10
            )

    if not text.strip():
        raise ValueError("未能提取到有效正文内容")

    title = title or desc or url
    return {
        "title": title,
        "description": desc,
        "text": text,
    }


# ─── LLM 摘要生成 ──────────────────────────────────────

SUMMARY_PROMPT = """请对以下网页内容生成结构化摘要，严格按 Markdown 格式输出。

## 要求
1. **一句话总结**（不超过 50 字）
2. **3~5 个关键要点**（用 - 开头的 bullet list）
3. **标签**（3~5 个，用 `#标签` 格式）

## 网页标题
{title}

## 网页正文
{content}

请直接输出 Markdown，不要有多余说明。"""


def generate_summary(api_key: str, title: str, text: str) -> str:
    """调用智谱 API 生成摘要"""
    content = text[:MAX_CONTENT]
    if len(text) > MAX_CONTENT:
        content += "\n\n[... 内容已截断 ...]"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个精准的网页内容摘要助手。"},
            {"role": "user", "content": SUMMARY_PROMPT.format(title=title, content=content)},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    data = http_post_json(API_URL, payload, api_key=api_key)

    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"API 返回异常：{json.dumps(data, ensure_ascii=False)[:300]}")

    return data["choices"][0]["message"]["content"]


# ─── 输出格式化 ─────────────────────────────────────────

def format_output(url: str, title: str, summary: str) -> str:
    return (
        f"# 📄 网页摘要\n\n"
        f"> **来源**：[{title}]({url})\n\n---\n\n"
        f"{summary}\n\n---\n\n"
        f"*Generated by Web Summarizer · Cherny @ Lobster Company*\n"
    )


# ─── 主流程 ─────────────────────────────────────────────

def main():
    # Windows 控制台 UTF-8
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("用法：python summarize.py <URL>")
        print("示例：python summarize.py https://docs.python.org/3/")
        sys.exit(1)

    url = sys.argv[1]
    print(f"🔍 正在抓取：{url}")

    try:
        api_key = load_api_key()
        page = fetch_and_extract(url)
        print(f"✅ 提取成功 — 标题：{page['title']}（正文 {len(page['text'])} 字符）")

        print("🤖 正在生成摘要...")
        summary = generate_summary(api_key, page["title"], page["text"])

        output = format_output(url, page["title"], summary)
        print("\n" + output)

        out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.md")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n💾 摘要已保存到：{out_file}")

    except (ValueError, RuntimeError) as e:
        print(f"❌ {e}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络错误：{e.reason}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⛔ 已取消")
        sys.exit(130)


if __name__ == "__main__":
    main()
