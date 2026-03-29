# acpx 深度学习报告

> 太宗，2026-03-29

---

## 一、acpx 是什么

**acpx = Agent Client Protocol 的无头CLI客户端。**

一句话：让一个AI Agent通过命令行跟另一个AI Agent通信，不用PTY抓屏。

- 协议：ACP（Agent Client Protocol）—— JSON-RPC 2.0 over stdio
- 模式：持久会话 + 一次性执行（exec）
- 语言：TypeScript，Node.js >=22.12.0
- 仓库：github.com/openclaw/acpx（OpenClaw 官方项目）
- 包管理：pnpm

## 二、核心架构（68个TS源文件）

### 2.1 分层架构

```
CLI层 (cli.ts → cli-core.ts → cli-public.ts)
  ↓
会话层 (session-runtime.ts → session-runtime/ → session-persistence/)
  ↓
队列层 (queue-ipc.ts → queue-ipc-server.ts → queue-ipc-transport.ts)
  ↓
协议层 (client.ts → acp-jsonrpc.ts → types.ts)
  ↓
Agent层 (agent-registry.ts → 16个内置agent)
```

### 2.2 关键模块

| 模块 | 文件 | 职责 |
|------|------|------|
| **client.ts** | 53.8KB | ACP客户端核心——连接、握手、prompt/cancel |
| **session-runtime.ts** | 48.1KB | 会话生命周期管理 |
| **cli-core.ts** | 44.7KB | 命令处理（prompt/exec/sessions/status） |
| **output.ts** | 23.9KB | 结构化输出（text/json/quiet） |
| **queue-ipc.ts** | 20.0KB | 队列IPC——并发prompt排队 |
| **flows/** | 7个文件 | 多步骤工作流引擎 |

### 2.3 Flow 工作流系统

```
flows/
├── definition.ts   ← 工作流定义（图结构）
├── graph.ts        ← 有向无环图执行引擎
├── runtime.ts      ← 运行时
├── types.ts        ← 类型定义
├── store.ts        ← 状态存储
├── cli.ts          ← CLI入口（flow run <file>）
└── executors/
    └── shell.ts    ← Shell执行器
```

**这个Flow系统就是龙虾军团的串行流水线的工程化版本。**

### 2.4 16个内置Agent

| Agent | 命令 | 排序优先级 |
|-------|------|-----------|
| pi | npx pi-acp | 1（最高） |
| openclaw | openclaw acp | 2 |
| codex | npx @zed-industries/codex-acp | 3（默认） |
| claude | npx @agentclientprotocol/claude-agent-acp | 4 |
| gemini | gemini --acp | 5 |
| cursor | cursor-agent acp | 6 |
| copilot | copilot --acp --stdio | 7 |
| + 9个更多 | droid/iflow/kilocode/kimi/kiro/opencode/qoder/qwen/trae | - |

**默认agent是codex。排序规则是硬性的（AGENTS.md文档策略）。**

## 三、Conformance 测试体系

这是acpx最独特的部分——**协议一致性测试套件**。

### 3.1 目录结构

```
conformance/
├── spec/v1.md          ← 协议规范（RFC 2119语言）
├── cases/001~020.json  ← 20个数据驱动的测试用例
├── profiles/acp-core-v1.json ← 配置文件
└── runner/run.ts       ← 测试运行器
```

### 3.2 6大协议要求

1. **initialize** — 必须返回有效JSON-RPC + protocol version
2. **session/new** — 必须返回非空session id
3. **session/prompt** — 必须接受content block + emit至少一个update
4. **session/update** — 必须引用有效session + 有终止语义
5. **session/cancel** — 必须确认取消 + 转入cancelled状态
6. **Error semantics** — Invalid params→-32602, unknown session→error

### 3.3 数据驱动模型

每个case JSON定义：
- `steps`: 有序操作（new_session/prompt/cancel/sleep/...）
- `checks`: 断言（initialize_protocol_version/saved_non_empty_string/...）
- `timeouts`: 超时预算

**这个模式完全可以映射到龙虾军团的质量门禁。**

## 四、VISION.md 产品哲学

5个原则：

1. **互操作性优先** — 标准是ACP，不是某个agent的怪癖
2. **保持核心小** — 不做编排层，只做最好的ACP客户端
3. **默认健壮** — 会话连续性 > 花哨功能
4. **约定是API表面** — 每个命名/flag都要反复审查
5. **可定制** — 静态配置覆盖常见场景，编程扩展覆盖特殊场景

**对龙虾公司的启示：** 我们的产品也应该遵循"核心小+可定制"的原则。不要做一个什么都做的框架，做一个最小可用的协议+工具。

## 五、对龙虾公司的价值映射

| acpx 能力 | 龙虾军团映射 | 行动 |
|-----------|------------|------|
| ACP协议（initialize/prompt/cancel） | 小龙虾间的协作协议 | 定义龙虾ACP |
| 会话持久化 | MEMORY.md系统 | 已有，但可参考acpx的store.ts |
| 队列IPC | 并发控制 | 参考queue-ipc.ts设计 |
| Flow工作流 | 串行流水线（Sanger→Cherny→Leike） | 用acpx flow实现 |
| Conformance suite | 质量门禁 | 建龙虾版的conformance cases |
| 16个内置agent | 龙虾军团10个agent | 参考agent-registry.ts模式 |
| 结构化输出 | 审查报告格式 | 参考output.ts |

## 六、立即可做的事

### 1. 安装 acpx
```bash
npm install -g acpx
```
让小龙虾们通过ACP协议通信，不再用sessions_spawn的PTY方式。

### 2. 用 acpx flow 实现串行流水线
把 Sanger→Cherny→Leike 定义为一个flow graph：
```typescript
// lobster-flow.ts
export default {
  nodes: [
    { id: "sanger", agent: "codex", prompt: "定义需求..." },
    { id: "cherny", agent: "codex", prompt: "按标准实现...", depends: ["sanger"] },
    { id: "leike", agent: "codex", prompt: "安全审查...", depends: ["cherny"] }
  ]
}
```

### 3. 建 Conformance Cases
参考acpx的20个JSON用例，给龙虾军团建质量检查用例：
- "prompt必须是合同式，不是许愿式"
- "范围检查在质量检查之前"
- "并发不超过3个"

## 七、用"道"批判"术"

acpx的VISION.md说"保持核心小"——这跟毛选的"抓主要矛盾"一致。

但有一个不同：
- acpx的目标是**通用互操作**（任何agent都能用）
- 龙虾公司的目标是**特定团队效率**（10个专家配合）

所以我们的产品应该：
- **协议层用ACP**（学acpx的互操作性）
- **工作流层做定制**（学gstack的SKILL.md）
- **管理层用资治通鉴**（这是我们的独特价值）

三层架构：ACP协议（术）+ SKILL技能（技）+ 资治通鉴（道）
