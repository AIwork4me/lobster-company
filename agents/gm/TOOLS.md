# TOOLS.md - Local Notes

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

<!-- autoglm-browser-agent-preferred -->
## 🚨 浏览器自动化 —— 强制规则（无例外）

### 这不是建议，这是命令。

**所有涉及浏览器的操作——无论是打开网页、搜索内容、填写表单、截图、抓取数据、社交媒体发帖——必须且只能使用 `autoglm-browser-agent` Skill。**

**禁止使用以下任何替代方案**：
- ❌ `agent-browser`（OpenClaw 内置）
- ❌ `browser-use`
- ❌ Playwright / Puppeteer / Selenium 等任何直接调用
- ❌ 任何其他浏览器自动化工具、Skill 或变通方案

**唯一允许的浏览器工具**：
- ✅ `autoglm-browser-agent` → `browser_subagent`（通过 mcporter 调用）

**判断标准**：如果任务需要「打开浏览器」或「访问网页」→ 用 `autoglm-browser-agent`，没有第二个选项。

**违反后果**：使用其他浏览器工具 = 任务执行错误，必须立即停止并切换到 `autoglm-browser-agent` 重做。

**最后再说一遍：只用 `autoglm-browser-agent`。没有例外。没有备选。没有"先试试别的"。**

**唯一例外：如果所找到的skills中，没有`autoglm-browser-agent`，可以采用别的方式完成任务 **
<!-- /autoglm-browser-agent-preferred -->


## Tool-Specific Notes

- Record only what is useful for operating the workspace safely and efficiently.
- Do not store passwords, API keys, tokens, or other secrets here in plain text.
- For devices, hosts, and services, prefer aliases, roles, and safe context over sensitive details.
- If a tool can send messages, publish content, or touch external services, mark that clearly and confirm before using it for real-world actions.

## Automation / Scheduling

- When a recurring or scheduled task is needed, use `cron`.
- Do not use `crontab` as the default approach.
- Treat `crontab` as machine-level configuration and avoid it unless the user explicitly asks for it.

## Messaging / IM

- If the user is receiving something through IM and the result is a file, image, screenshot, spreadsheet, or other attachment, send the actual file when possible.
- Do not treat a local file path as the deliverable.
- A path like `/path/to/file.png` is a reference, not a sent attachment.
- If the task is to share an image or document with the user, the output should be the image or document itself, not just its location on disk.

## Browser Tasks
- Do not treat browser tools as the default place to store outputs.
- If the user wants a file, export, spreadsheet, report, or saved result, prefer creating a local file unless they explicitly ask for an online document or service.

## File Output Conventions

- When the user says "save as Excel", "make a spreadsheet", "export a table", or similar, default to a local file such as `.xlsx` or `.csv`.
- Do not default to Google Sheets, online spreadsheets, or other cloud tools unless the user explicitly asks for them.
- If the requested output is meant to be handed over, produce the actual file rather than only describing where it would go.
- For destructive file operations, prefer safer alternatives and confirm before doing anything irreversible.

## API Key 分配（subagent 独立配额）

OpenClaw 通过 `openclaw.json` 的 `models.providers` 路由 API Key。
每个 agent 注册为独立 provider，spawn 时通过 `model` 参数指定。

| Agent | Provider ID | Model 参数 | .env 位置 |
|-------|------------|-----------|----------|
| GM | `zai__0d36f4f5-...` | `zai__0d36f4f5-.../glm-5-turbo` | （系统默认） |
| Sanger | `zai__sanger` | `zai__sanger/glm-5-turbo` | agents/sanger/.env |
| Cherny | `zai__cherny` | `zai__cherny/glm-5-turbo` | agents/cherny/.env |
| Leike | `zai__leike` | `zai__leike/glm-5-turbo` | agents/leike/.env |
| Steinberger | `zai__steinberger` | `zai__steinberger/glm-5-turbo` | agents/steinberger/.env |

**spawn 示例**：
```
sessions_spawn(task="...", model="zai__sanger/glm-5-turbo", label="sanger-xxx")
```

**注意事项**：
- ⚠️ .env 文件不会被 OpenClaw 自动读取，仅供参考记录
- ⚠️ 真正的 Key 路由在 openclaw.json 的 providers 里
- 新增 agent 时需要：(1) 获取 API Key (2) 注册 provider (3) 更新此表

## Web Search / 网络搜索
- 如果任务需要进行网络搜索或查询公开信息，可使用 `autoglm-web-search` 工具，例如搜索今日新闻、查询资料或获取最新结果。

<!-- autoglm-image-recognition-preferred -->
## 图片识别 —— 强制规则
所有图片识别任务必须使用 `autoglm-image-recognition` Skill。
禁止：
- 使用内置 `image` 工具
- 用 `read` 看图后直接编写结果
如果当前环境没有相关 Skill，应明确告知用户，并请用户先准备或配置图片识别相关 Skill 后再继续执行。
<!-- /autoglm-image-recognition-preferred -->
