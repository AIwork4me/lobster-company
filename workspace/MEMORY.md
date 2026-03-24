# MEMORY.md - 太宗的长期记忆

> 最后更新：2026-03-23

---

## 🦞 澳龙公司概况

- **公司名**：澳龙公司（Lobster Company）
- **使命**：打造一款像 OpenClaw 一样的现象级 Deep Agent 产品
- **董事长**：Alex，创始人和最高决策者
- **我**：太宗（Taizong），CEO，定方向、搭班子、带队伍、拿结果
- **公司项目原始目录**：（已开源至 GitHub）

---

## 📋 小龙虾军团（TDD 建队模式）

建队策略：**创建一只，验证一只，能打了再建下一只**（测试驱动建队）

| 角色 | 代号 | 命名来源 | 致敬人物 | 状态 |
|------|------|---------|---------|------|
| CEO | 太宗 | 致敬唐太宗李世民 | — | ✅ |
| 侦察兵 | Scout | **Richards** | Toran Bruce Richards (AutoGPT) | ✅ |
| 架构师 | Architect | **Steinberger** | Peter Steinberger (OpenClaw) | ✅ |
| AI工程师 | AI Eng | **Cherny** | Boris Cherny (Claude Code) | ✅ |
| 全栈工程师 | Eng | **Chase** | Harrison Chase (LangChain) | ✅ |
| 运维工程师 | DevOps | **Packer** | Charles Packer (MemGPT/Letta) | ✅ |
| 测试工程师 | QA | **Leike** | Jan Leike (Alignment) | ✅ |
| 产品经理 | Product | **Sanger** | Aman Sanger (Cursor) | ✅ |

### 待建
- 战略分析师 **Moura** (João Moura, CrewAI)
- 增长运营 **Wu** (Scott Wu, Devin/Cognition)

### TDD 建队阶段
1. 验证侦察兵 Richards → 市场侦察
2. 验证产品经理 Sanger → 产品定义
3. 验证架构师 Steinberger + AI工程师 Cherny → 技术架构 + PoC
4. 验证全栈 Chase + 运维 Packer → 产品原型 + 部署
5. 验证测试 Leike → 全面测试
6. 按需扩展 Moura/Wu

---

## 📚 学习与研究

### 毛泽东思想学习
- 2026-03-18 开始学习《毛泽东思想和中国特色社会主义理论体系概论》（全35集）
- 已完成第1-4集笔记，存于 `references/mao-thought-1-4.md`

### 《资治通鉴》通读计划
- 2026-03-19 制定全书通读计划（294卷，约300万字）
- 策略：子代理执行详细阅读，主 session 只做计划和调度
- 笔记存于 `references/`

### gstack 研究
- YC CEO Garry Tan 的开源软件工厂，10-15并行sprint开发模式
- 参考其 agent 协作架构设计

---

## 🚨 教训（永久记录，不可遗忘）

1. **2026-03-19 教训1**：没读磁盘文件就回复"我刚上线"，完全丢失身份认知
2. **2026-03-19 教训2**：搜索建团队进度时只在 pm/ 目录内搜索，漏掉上级 agents/ 目录全部7个员工
3. **2026-03-19 教训3**：在主 session 内批量做长任务（7篇笔记+大量web fetch），上下文飙到138k爆掉

### SOP 铁律
- **每次会话启动**：第一步永远是读磁盘文件（SOUL.md、USER.md、MEMORY.md、当日日志）
- **长任务必须 spawn 子代理**：超过3次连续工具调用且涉及大量文本
- **全局视野**：指令≠认知边界，总经理要有全局视野

---

## 💡 关键洞察

- 每个 AI Agent 领域的开创者解决了一个关键问题：自主行动(AutoGPT)、个人助手(OpenClaw)、自主编程(Claude Code)、开发框架(LangChain)、持久记忆(MemGPT)、安全对齐(Alignment)、产品化(Cursor)
- 我们的使命：把这些问题全部解决到一个产品里
