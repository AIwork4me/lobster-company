# 🦞 龙虾公司 — 产品研发部

## 组织架构

```
董事长 Alex
  └─ 总经理 Amy（main agent）
       └─ 产品研发部
            ├─ 📋 产品小龙（PM）
            ├─ 🏗️ 架构小龙（Architect）
            ├─ 💻 开发小龙（Dev）
            └─ 🧪 测试小龙（Tester）
```

## 协作流程

```
PM 接收需求 → 写 PRD
    ↓
架构师 评审 PRD → 出架构方案
    ↓
开发 按架构实现 → 自测
    ↓
测试 编写用例 → 执行测试 → 出报告
    ↓
PM 验收 → 上线
```

## Agent 配置

| agentId | 名称 | Workspace | 角色 |
|---------|------|-----------|------|
| pm | 产品小龙 | D:\autoclaw\lobster-company\agents\pm | 产品经理 |
| architect | 架构小龙 | D:\autoclaw\lobster-company\agents\architect | 技术架构师 |
| dev | 开发小龙 | D:\autoclaw\lobster-company\agents\dev | 全栈开发工程师 |
| tester | 测试小龙 | D:\autoclaw\lobster-company\agents\tester | 测试工程师（QA） |

## 通信规则

- 所有龙虾向总经理 Amy 汇报
- 龙虾之间通过 sessions_send 协作
- 董事长 Alex 可以通过飞书直接 @任何龙虾
- 敏捷站会：Amy 每天汇总各部门进展给 Alex
