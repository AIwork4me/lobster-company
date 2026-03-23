# gstack 深度技术分析报告

> 分析时间：2026-03-22 | 分析人：Amy（澳龙公司总经理）
> 项目路径：C:\Users\OpenVino\Desktop\gstack
> 版本范围：v0.9.4.1（截至 2026-03-20）

---

## 一、Skill 清单与功能说明

### 🎯 战略与规划层（Think First）

| Skill | 一句话功能 |
|-------|-----------|
| **office-hours** | 模拟 YC 合伙人 Office Hours，通过 6 个强制问题在写代码前逼迫创始人想清楚"到底该不该做"，输出设计文档 |
| **plan-ceo-review** | CEO 视角审查计划——重新审视问题定义，寻找 10x 可能性，支持四种审查模式（扩展/选择性扩展/保持/缩减） |
| **plan-eng-review** | 工程经理视角审查——锁定架构、数据流、状态机、边界条件、测试金字塔，用图表强制暴露隐含假设 |
| **plan-design-review** | 高级设计师视角审查——对每个设计维度打分 0-10，交互式修复计划中的视觉缺陷 |

### 🎨 设计层

| Skill | 一句话功能 |
|-------|-----------|
| **design-consultation** | 从零构建完整设计系统——调研竞品、提出安全选项与创意风险、生成可交互 HTML 预览、写入 DESIGN.md |
| **design-review** | 对线上站点进行 80 项视觉审计，自动修复 CSS 问题并逐条原子提交 |

### 🔍 审查与调试层

| Skill | 一句话功能 |
|-------|-----------|
| **review** | 偏执的 Staff Engineer 模式——找 CI 过得了但生产会炸的 Bug（N+1、竞态、信任边界），自动修复机械问题 |
| **investigate** | 系统化根因调查——数据流追踪、假设验证、3 次修复失败后停止而非瞎试 |
| **codex** | 调用 OpenAI Codex 做独立第二意见——代码审查（PASS/FAIL 门控）、对抗性挑战、开放咨询 |

### ✅ QA 与发布层

| Skill | 一句话功能 |
|-------|-----------|
| **qa** | 基于 git diff 自动识别受影响页面，启动真实浏览器测试，找 Bug → 修 Bug → 原子提交 → 回归测试 |
| **qa-only** | 只报告不修复的 QA 模式——纯 Bug 报告，附带截图和复现步骤 |
| **ship** | 一键发布——同步 main、跑测试、审查 diff、更新 CHANGELOG、推代码、建 PR |
| **document-release** | 发 PR 后自动同步更新所有文档（README/CLAUDE.md/CONTRIBUTING.md 等） |

### 📊 回顾与演进层

| Skill | 一句话功能 |
|-------|-----------|
| **retro** | 团队感知的周回顾——按人分析提交、代码质量、测试趋势、连续发布天数 |

### 🛡️ 安全与工具层

| Skill | 一句话功能 |
|-------|-----------|
| **careful** | 破坏性命令警告（rm -rf、DROP TABLE、force-push），用户可覆盖 |
| **freeze** | 将文件编辑锁定到指定目录，防止意外修改无关代码 |
| **guard** | careful + freeze 组合，最高安全模式 |
| **unfreeze** | 解除目录编辑锁定 |
| **gstack-upgrade** | 一键升级 gstack，自动检测全局/本地安装并同步 |
| **setup-browser-cookies** | 从真实浏览器导入 Cookie 到无头浏览器，测试需认证的页面 |

### 🌐 浏览器引擎

| Skill | 一句话功能 |
|-------|-----------|
| **browse** | 持久化无头 Chromium 守护进程——真实浏览器交互，~100ms/命令，是所有 QA/design skill 的基础设施 |

---

## 二、整体架构设计哲学

### 2.1 核心理念：**Markdown 是 UI，Prompt 是代码**

gstack 最激进的设计决策是：**整个工作流引擎不是代码，而是 Markdown**。

每个 Skill 就是一个 SKILL.md 文件——一段精心设计的 Prompt，告诉 AI Agent 在特定场景下该做什么、按什么顺序、遵守什么规则、输出什么格式。没有 DSL、没有工作流引擎、没有可视化编辑器。这是"Prompt-as-Code"的极致实践。

```
SKILL.md.tmpl（人类写的模板 + 占位符）
    ↓ gen-skill-docs.ts
SKILL.md（机器生成，提交到 Git，Claude 读取执行）
```

**为什么这个选择是对的：**
- LLM 天然理解 Markdown，不需要编译器
- 版本控制天然友好（Git diff 可读）
- 非程序员可以贡献（写 Prompt 比写代码门槛低）
- 迭代速度极快（改一行 Markdown = 改一个行为）

### 2.2 "想清楚再做"的硬管线

gstack 设计了一条严格的 **单向管线**：

```
office-hours（想清楚做什么）
    → plan-ceo-review（战略对不对）
        → plan-eng-review（技术怎么实现）
            → plan-design-review（视觉长什么样）
                → review（代码审查）
                    → qa（浏览器测试）
                        → ship（发布）
                            → document-release（文档同步）
                                → retro（复盘）
```

这不是建议，是结构。每个 skill 在结束时都会推荐下一步，形成强制性的工作流。**office-hours 里有硬性门禁：`HARD GATE: Do NOT invoke any implementation skill`**——不允许跳过思考直接写代码。

### 2.3 浏览器是基础设施，不是锦上添花

gstack 不把浏览器当作"可选工具"，而是当作 **AI Agent 的眼睛**。整个 QA、设计审查、Release 工作流都建立在持久化 Chromium 守护进程之上：

```
CLI（编译二进制）→ HTTP POST → Server（Bun.serve）→ CDP → Chromium
```

关键设计：浏览器进程在命令之间保持存活，Cookie、Tab、localStorage 持久化。第一次启动 ~3s，之后每次命令 ~100-200ms。这不是"每次启动浏览器截个图"——是真正的持久化会话。

### 2.4 技术选型的务实主义

gstack 选择 **Bun** 而非 Node.js，理由非常具体且务实：
1. 编译成单文件二进制（~58MB），用户不需要管理 node_modules
2. 原生 SQLite（解密 Cookie 数据库），不需要 better-sqlite3 和 native addon
3. 原生 TypeScript，开发时不需要编译步骤
4. 内置 HTTP server，10 个路由不需要 Express

不选 MCP、不选 WebSocket、不选多用户——每个"不做"都有明确的理由写在 ARCHITECTURE.md 里。

---

## 三、Skill 编排机制分析

### 3.1 显式推荐链（Soft Chaining）

Skill 之间不是硬编码的 DAG，而是通过 **Prompt 中的推荐文本** 实现软连接：

```
/office-hours 结束时：
  "Based on what we discussed, I'd recommend running /plan-ceo-review next."

/plan-ceo-review 结束时：
  "Engineering review recommended: /plan-eng-review"
```

**这不是代码调用，是 Prompt 引导 AI Agent 在合适时机推荐下一个 skill。** 这种设计的优势：
- 用户始终有选择权（可以忽略推荐）
- 每个 skill 独立可用（不依赖上游的输出格式）
- 修改工作流只需要改 Markdown，不需要改代码

### 3.2 数据流转：文件系统即数据库

Skill 之间通过 **文件系统** 传递数据：

```
~/.gstack/projects/{slug}/                    ← 设计文档存储
  {user}-{branch}-design-{datetime}.md        ← office-hours 产出
  ceo-plans/{date}-{feature}.md              ← plan-ceo-review 产出
  eng-plans/{date}-{feature}.md              ← plan-eng-review 产出

~/.gstack/analytics/                          ← 遥测与分析
  spec-review.jsonl                           ← 对抗性审查指标
  telemetry.jsonl                             ← 使用遥测

.gstack/review-readiness-dashboard.json       ← Review 状态聚合
.gstack/qa-reports/                           ← QA 报告与截图
.gstack/design-reports/                       ← 设计审查报告
```

**这是非常 Unix 哲学的做法**——每个工具读取标准格式的文件，写入标准格式的文件，不做紧耦合。`plan-eng-review` 产出的测试计划会被 `qa` 自动发现和使用，但它们之间没有任何代码依赖。

### 3.3 Review Readiness Dashboard：聚合决策点

所有 Review skill（CEO/Eng/Design/Codex）完成后都会更新一个共享的 Dashboard 文件，`ship` skill 在发布前读取这个 Dashboard 判断是否满足门控条件：

```
+====================================================================+
|                    REVIEW READINESS DASHBOARD                       |
+====================================================================+
| Review          | Runs | Last Run            | Status    | Required |
|-----------------|------|---------------------|-----------|----------|
| Eng Review      |  1   | 2026-03-16 15:00    | CLEAR     | YES      |
| CEO Review      |  1   | 2026-03-16 14:30    | CLEAR     | no       |
+====================================================================+
```

**Eng Review 是唯一的硬性门控**（可通过配置关闭）。CEO 和 Design 是信息性的推荐。

### 3.4 对抗性审查（Spec Review Loop）

多个 skill 内嵌了 **子代理对抗审查** 机制：office-hours 写完设计文档后，派出独立 AI 子代理对文档进行对抗性评审（完整性、一致性、清晰度、范围、可行性），最多 3 轮迭代。这个模式在 office-hours、plan-ceo-review、plan-eng-review 中复用。

### 3.5 Skill 建议系统

主 browse skill 内置了一个 **上下文感知的建议引擎**：根据用户的操作阶段（coding → suggest /review；ready to deploy → suggest /ship；debugging → suggest /investigate），主动推荐合适的 skill。用户可以关闭（`gstack-config set proactive false`）。

---

## 四、代码质量与工程实践分析

### 4.1 代码质量评估：**优秀（A 级）**

**亮点：**

1. **单一真相源（Single Source of Truth）**：`commands.ts` 是命令注册表，所有命令定义在一个地方。SKILL.md 中的命令文档从代码自动生成，杜绝文档漂移。

2. **零副作用设计**：`commands.ts` 文件顶部明确注释 `Zero side effects. Safe to import from build scripts and tests.`——这个文件可以被任何工具安全导入。

3. **加载时验证**：`commands.ts` 底部有自检循环——如果 COMMAND_DESCRIPTIONS 和命令 Set 不匹配，构建直接失败：
   ```typescript
   for (const cmd of allCmds) {
     if (!descKeys.has(cmd)) throw new Error(`COMMAND_DESCRIPTIONS missing entry for: ${cmd}`);
   }
   ```

4. **Ref 系统（@e1, @e2）**：不修改 DOM（避免 CSP 冲突和框架冲突），用 Playwright Locator 实现外部引用。导航时自动清除 stale refs，SPA 变更时通过 `count()` 检测过期。

5. **错误哲学**：每个错误消息都是为 AI Agent 设计的——不只是说"出错了"，而是告诉 Agent 下一步该怎么做：
   - `"Element not found. Run snapshot -i to see available elements."`
   - `"Ref @e3 is stale — element no longer exists. Run 'snapshot' to get fresh refs."`

6. **安全模型**：localhost-only HTTP、UUID bearer token、mode 0o600 状态文件、Cookie 从不写入明文磁盘、Shell 注入防护（硬编码浏览器注册表，不拼接用户输入）。

### 4.2 工程实践评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **文档质量** | A+ | ARCHITECTURE.md 详细解释每个设计决策的"为什么"；CLAUDE.md 是完整的开发指南；每个 skill 都有深度文档 |
| **测试分层** | A | 三层测试金字塔：免费静态验证（<5s）→ E2E（~$4）→ LLM Judge（~$0.15） |
| **CI/CD** | A- | Diff-based 测试选择（只跑受影响的测试），自动版本检测 |
| **可观测性** | A | 实时 E2E 进度看板、心跳文件、原子写入的 partial results |
| **开发者体验** | A | dev-setup/dev-teardown 符号链接、watch 模式自动重建、`bun run dev` 直接调试 |
| **跨平台** | B+ | v0.9.3.0 专门做了 Windows 支持（Node.js polyfill、路径处理），但 Cookie 解密仅支持 macOS |

### 4.3 测试基础设施亮点

- **Diff-based 测试选择**：每个测试声明文件依赖（`touchfiles.ts`），`git diff` 决定跑哪些测试，不浪费钱
- **E2E 独立进程**：用 `claude -p` 独立子进程跑，不嵌套在 Claude Code 内
- **非致命可观测性**：所有 I/O 写入都被 try/catch 包裹，写失败不会导致测试失败
- **增量持久化**：`savePartial()` 每跑完一个测试就原子写入，kill 也不丢数据
- **版本对比**：每次 eval 运行后自动对比上一次的结果，追踪退化

---

## 五、最值得澳龙公司学习的 5 个设计亮点

### 🥇 亮点 1：**SKILL.md 模板系统——文档即代码**

```
SKILL.md.tmpl（人写模板 + 占位符）
    ↓ gen-skill-docs.ts（从源代码元数据填充）
SKILL.md（提交到 Git，AI 直接读取执行）
```

**为什么值得学：** 解决了"Prompt Engineering 最致命的问题——文档漂移"。代码改了，Prompt 文档没改，Agent 就会犯错。gstack 的做法让命令列表、参数说明等机械性内容从代码自动生成，只有需要人类判断的 workflow 描述才手动维护。这给我们的启示：**我们自己的 Agent 配置文件和 Prompt 模板也可以用类似机制，确保一致性。**

### 🥈 亮点 2：**"想清楚再做"的硬管线设计**

```
office-hours → plan-ceo-review → plan-eng-review → plan-design-review → review → qa → ship
```

每个 skill 结束时推荐下一步，office-hours 有硬性门禁禁止跳过。**这不是自由度的问题，是纪律的问题。** 

**为什么值得学：** 我们在做 Deep Agent 产品时，用户（特别是企业用户）最大的痛点不是"AI 不够聪明"，而是"AI 太容易就开始干活了"。gstack 用 Prompt 层面的管线约束，几乎零成本地实现了"先诊断后开药"的纪律。我们可以将这种模式内建到产品中。

### 🥉 亮点 3：**三层测试金字塔 + Diff-based 选择**

| Tier | 成本 | 速度 | 覆盖 |
|------|------|------|------|
| 1 — 静态验证 | $0 | <5s | 95% 问题 |
| 2 — E2E | ~$3.85 | ~20min | 集成测试 |
| 3 — LLM Judge | ~$0.15 | ~30s | 质量评估 |

**为什么值得学：** 测试 LLM Agent 的 Skill 不是简单的单元测试。gstack 的分层策略是：免费测试捕获绝大多数问题，付费测试只在必要时跑，且只跑受影响的测试。**控制测试成本是 Agent 产品规模化的关键能力。** 我们的 Deep Agent 产品的自动化测试也应该采用类似策略。

### 🏅 亮点 4：**Ref 系统——无 DOM 污染的元素引用**

用 Playwright Locator + ARIA Tree 实现 `@e1`、`@e2` 引用，完全不修改 DOM：
- 避开 CSP 限制
- 避开 React/Vue 的 hydration 冲突
- 避开 Shadow DOM 隔离
- 导航时自动清除，SPA 变更时 count() 检测

**为什么值得学：** 这是一个教科书级别的"用框架能力而非对抗框架"的设计。当你的 Agent 需要和浏览器交互时，不要注入 data 属性或修改 DOM——用浏览器本身提供的 ARIA Tree 和 Locator。这对我们的浏览器自动化方案有直接参考价值。

### 🏅 亮点 5：**"每个错误都要可操作"的错误哲学**

```
Bad:  "Element not found"
Good: "Element not found. Run `snapshot -i` to see available elements."
```

**为什么值得学：** 这是面向 AI Agent 的 UX 设计，不是面向人类的。AI Agent 读到错误后应该知道下一步做什么，不需要人类的介入。这和我们 AGENTS.md 里的安全策略一脉相承——但 gstack 把这个理念延伸到了每一个工具的错误消息。**我们自己的 Agent 工具和 Skill 也应该遵循这个原则。**

---

## 六、局限性与不足分析

### 6.1 架构局限

**1. 编排机制是"建议"而非"强制"**
- Skill 之间的串联完全依赖 Prompt 中的推荐文本，没有代码层面的依赖管理
- 用户可以随意跳过任何步骤（除了 office-hours 的硬门禁也只是 Prompt 层面）
- **改进空间：** 引入轻量级的状态机或检查点系统，让管线可追踪但不强制

**2. 文件系统即数据库的扩展性问题**
- 所有状态存储在 `~/.gstack/` 的 JSON/Markdown 文件中
- 多项目、多用户的并发场景可能出现竞态（虽然目前设计为单用户）
- **改进空间：** SQLite 已经在 Cookie 解密中使用，可以考虑扩展到状态管理

**3. Cookie 解密仅支持 macOS**
- Windows（DPAPI）和 Linux（GNOME Keyring/kwallet）明确标注为"architecturally possible but not implemented"
- 限制了企业用户的使用场景
- **改进空间：** 优先支持 Windows（用户基数最大）

### 6.2 Prompt Engineering 局限

**4. Skill 文件过于庞大**
- 核心 skill（如 office-hours、plan-ceo-review）的 SKILL.md 超过 1000 行
- 虽然 Markdown 对人类可读，但对 LLM 来说，过长的 Prompt 可能导致注意力稀释
- **改进空间：** 将大型 skill 拆分为多个子 skill，或引入 "Phase-based Loading"（只在需要时加载特定阶段）

**5. 缺乏动态适应能力**
- 所有 skill 的工作流是静态的、预设的
- 不能根据项目类型（前端/后端/全栈/数据工程）自动调整审查重点
- **改进空间：** 引入项目特征检测，动态调整 skill 行为

### 6.3 产品与商业化局限

**6. 仅支持 Claude Code 生态**
- 虽然声称支持 Codex/Gemini/Cursor（v0.9.0），但核心体验围绕 Claude Code 设计
- 其他 Agent 平台的支持质量明显降级（hooks 变成 inline advisory prose）
- **改进空间：** 建立真正的 Agent-agnostic 抽象层

**7. 没有团队协作机制**
- 所有状态都是个人级别的（`~/.gstack/`）
- 设计文档、Review 结果不能在团队间共享
- retro 虽然有"团队感知"，但数据来源仅限 git log，没有真正的协作
- **改进空间：** 引入共享状态层（类似 Supabase 的后端已经在遥测中使用了）

**8. 缺乏成本控制和预算管理**
- E2E 测试每次 ~$3.85，LLM Judge ~$0.15——对个人开发者可能还行，团队使用成本会快速累积
- 没有使用量预警、月度预算、团队账单等企业级功能
- **改进空间：** 这恰好是我们的商业机会

### 6.4 工程局限

**9. 浏览器守护进程没有资源限制**
- Chromium 进程无内存/CPU 限制，长时间运行可能消耗大量资源
- 30 分钟空闲超时是唯一的保护机制
- **改进空间：** 增加内存限制和活跃度监控

**10. iframe 和 Shadow DOM 支持不完整**
- Ref 系统不跨 iframe 边界
- 作者自己在 ARCHITECTURE.md 中承认这是"most-requested missing feature"

---

## 七、总结与建议

### gstack 的本质

gstack 不是"一个工具"，而是 **"用 Markdown 写成的 AI 软件工程操作系统"**。它的创新不在于代码（代码是标准的 Playwright + Bun），而在于 **Prompt 架构**——用精心设计的 Prompt 文件构建了一套完整的软件开发工作流。

### 对澳龙公司的战略启示

1. **我们的 Deep Agent 产品应该学习 gstack 的管线设计思想**——不是给用户一个万能的 AI 助手，而是给用户一套有纪律的工作流。先诊断，再规划，再执行，再验证。纪律比自由更有价值。

2. **"模板系统"可以成为我们的差异化能力**——让企业用户通过 Markdown 模板定义自己的 Agent 工作流，同时用代码生成确保一致性。这是我们可以在产品层面超越 gstack 的方向。

3. **gstack 的商业化空白就是我们的机会**——团队协作、成本控制、企业级管理、跨平台支持。gstack 是一个优秀的技术产品，但不是一个商业化产品。我们可以在它的技术基础上构建真正的商业产品。

4. **测试基础设施的方法论可以直接借鉴**——三层测试金字塔 + Diff-based 选择 + 非致命可观测性，这应该是我们产品 QA 策略的基础。

5. **"错误即下一步指引"的设计理念**应该成为我们所有 Agent 交互的设计原则。

---

*报告完。*
