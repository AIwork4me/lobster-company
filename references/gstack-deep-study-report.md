# gstack → lobster-company 学习报告

> 太宗，2026-03-29，第一遍精读

---

## 一、gstack 是什么

gstack 不是框架，不是库。它是 **21个 SKILL.md 文件 + 1个持久化浏览器 + 1套工程纪律**。

核心洞察：SKILL.md 就是一份结构化的 prompt。每个 skill 是一个专家角色， 定义了：
- 这个角色做什么（description）
- 它能用什么工具（allowed-tools）
- 它怎么工作（step-by-step 工作流）
- 它怎么保证质量（checklist、review dashboard）

Garry Tan 用这套东西让 Claude Code 变成了一个21人的虚拟工程团队。

## 二、gstack 的"道"—— 三个核心哲学

### 1. Boil the Lake（把湖烧干）
AI 让完整性的边际成本接近零。 以前团队做90%方案省70行代码，现在AI写70行只要几秒。
- 湖（能烧干的）：一个模块100%测试覆盖、完整错误处理
- 海（烧不干的）：从零重写整个系统、跨季度平台迁移

**资治通鉴批注：** "事未有不生于微而成于著" — 完整性不是奢侈，是基本功。但毛选说"抓主要矛盾"，不是所有湖都值得烧。

### 2. Search Before Building（先搜后建）
三层知识： Layer 1 已验证标准 > Layer 2 当前流行 > Layer 3 第一性原理（最值钱）

**毛选批注: "没有调查就没有发言权" — Layer 1=调查, Layer 3=发言。中间要防止经验主义。

### 3. User Sovereignty（用户主权）
AI推荐，用户决定。 两个AI同意也不等于命令。

**资治通鉴批注: "兼听则明，偏信则暗" — 魏征模式。AI是谋臣，用户是皇帝。

## 三、gstack 的"术"—— 六大工程最佳实践

### 1. SKILL.md 模板系统
- 每个skill有 `.tmpl` 模板文件，通过 `gen:skill-docs` 生成最终 SKILL.md
- 好处： 模板可复用公共部分（preamble、base branch detect），skill只写核心逻辑
- **我们要学: 给 lobster-company 建 skill 模板系统**

### 2. Review Readiness Dashboard（审查就绪看板）
- `/ship` 命令会显示一张 dashboard：哪些 review 做过了，哪些没做
- 用二进制状态：CLEAR / NOT CLEARED
- 只有一个 review（Eng Review）是必过的，其他都是建议
- **我们要学: 给公司建任务就绪看板**

### 3. Autoplan 自动审查流水线
- 6个决策原则自动回答中间问题
- 3个阶段严格串行：CEO → Design → Eng
- Dual Voices：Claude + Codex 双模型交叉验证
- Decision Audit Trail：每个自动决策都有记录
- **我们要学: 太宗的决策审核流水线**

### 4. Scope Drift Detection（范围漂移检测）
- 在review时先检查：他们建的是否是被要求的？
- 对比 stated intent vs actual changes
- **我们要学: 给每个任务加范围漂移检测**

### 5. Preamble 系统（技能初始化）
- 每个 skill 启动时运行一段 preamble 脚本
- 收集环境信息（分支、并发会话数、配置）
- 版本检查、遥测选择加入
- **我们要学: 给每个 agent 加初始化检查**

### 6. 允许的工具分级（allowed-tools）
- 每个 skill 明确声明它能用什么工具
- 最少权限原则：只给需要的工具
- **我们要学: 给每个小龙虾定工具权限**

## 四、gstack 技能映射到龙虾军团

| gstack Skill | 龙虾军团 | 改造方向 |
|------------|---------|---------|
| plan-ceo-review | 太宗 | 加入资治通鉴决策框架，4种模式改为：进攻/防守/巩固/撤退 |
| plan-eng-review | Steinberger | 加入架构师审查清单 |
| review | Cherny | 加入代码审查 + AI Safety 检查 |
| qa | Leike | 加入测试工程流程 |
| ship | Chase | 加入全栈发布流程 |
| debug | Packer | 加入运维排障流程 |
| browse | Richards | 侦察兵的浏览器能力 |
| retro | 全员 | 周报+个人复盘 |
| investigate | Richards | 系统性根因分析 |
| guard | 全员 | 安全防护（careful + freeze） |
| autoplan | 太宗 | 自动决策流水线（6原则→实践论螺旋） |

## 五、gstack 的 ETHOS.md —— 用"道"批判

gstack 的 ETHOS.md 三个哲学都很好，但缺少深度：

1. **Boil the Lake 缺少"度"** — 毛选讲"主要矛盾和次要矛盾"。不是所有湖都值得烧，先抓主要矛盾。ROI > 3 才投入。

2. **Search Before Building 缺少"独立自主"** — 搜完照搬是本本主义。搜的目的是理解为什么，然后用自己的路超越。

3. **User Sovereignty 很好,但需要"从谏如流"** — 唐太宗不是简单听从用户，而是兼听则明。AI是谋臣，用户是皇帝，但皇帝也要听谏臣的意见才能做最优决策。

## 六、立即行动计划

### Step 1: 给公司建 SKILL 体系
- [ ] 创建 `skills/` 目录结构
- [ ] 给每个小龙虾写 SKILL.md
- [ ] 定义 allowed-tools 权限

### Step 2: 建审查看板
- [ ] 定义任务就绪的检查清单
- [ ] 给每个任务加 review log

### Step 3: 建决策流水线
- [ ] 太宗的自动决策原则（映射 autoplan 的6原则到实践论）
- [ ] Dual Voices → 交叉验证（Cherny + Leike）

### Step 4: 建安全防护
- [ ] guard skill → 全公司安全策略
- [ ] scope drift detection → 任务范围监控

---

> "gstack是术的巅峰。但我们有资治通鉴的道。用道御术，才是龙虾公司的核心竞争力。"
