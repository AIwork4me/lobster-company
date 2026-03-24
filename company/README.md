# 🦞 龙虾公司 — 产品研发部

## 组织架构

```
董事长 Alex
  └─ CEO 太宗 (Taizong)
       ├─ 🔭 Richards（侦察兵 / Scout）
       ├─ 🏗️ Steinberger（架构师 / Architect）
       ├─ 🧠 Cherny（AI 工程师）
       ├─ 💻 Chase（全栈工程师）
       ├─ ⚙️ Packer（运维工程师 / DevOps）
       ├─ 🛡️ Leike（测试工程师 / QA）
       └─ 📋 Sanger（产品经理 / PM）
```

## 协作流程

```
Sanger 接收需求 → 写 PRD
    ↓
Steinberger 评审 PRD → 出架构方案
    ↓
Cherny / Chase 按架构实现 → 自测
    ↓
Leike 编写用例 → 执行测试 → 出报告
    ↓
Sanger 验收 → 上线
```

## Agent 配置

| agentId | 名称 | Workspace | 角色 |
|---------|------|-----------|------|
| taizong | 太宗 (Taizong) | agents/taizong | CEO |
| richards | Richards | agents/richards | 侦察兵 (Scout) |
| steinberger | Steinberger | agents/steinberger | 架构师 (Architect) |
| cherny | Cherny | agents/cherny | AI 工程师 |
| chase | Chase | agents/chase | 全栈工程师 |
| packer | Packer | agents/packer | 运维工程师 (DevOps) |
| leike | Leike | agents/leike | 测试工程师 (QA) |
| sanger | Sanger | agents/sanger | 产品经理 (PM) |

## 通信规则

- 所有 Agent 向 CEO 太宗汇报
- Agent 之间通过 sessions_send 协作
- 董事长 Alex 可以直接 @任何 Agent
- 敏捷站会：太宗每天汇总各部门进展给 Alex
