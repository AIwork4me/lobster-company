# 🚀 Getting Started: Lobster Company Rebirth

## Prerequisites

1. **Node.js 18+** — [Download](https://nodejs.org)
2. **OpenClaw** (or AutoClaw) — [Install Guide](https://docs.openclaw.ai)

## One-Command Setup

```bash
# Clone
git clone https://github.com/AIwork4me/lobster-company.git
cd lobster-company

# Linux / macOS
chmod +x scripts/rebirth.sh
./scripts/rebirth.sh --with-team

# Windows
.\scripts\rebirth.ps1 -WithTeam
```

That's it. CEO Taizong is now in office.

## What Just Happened?

The rebirth script:

1. ✅ Checked your environment (Node.js, OpenClaw)
2. ✅ Located CEO Taizong's workspace (SOUL.md, MEMORY.md, study notes)
3. ✅ Verified all critical files exist
4. ✅ Listed all available team agents

## Next Steps

### Talk to the CEO
```bash
openclaw chat
```
Or if using AutoClaw, just open the chat interface. The CEO (Taizong) will load its personality, memory, and management philosophy automatically.

### Customize the Company

| What to change | File | Why |
|---|---|---|
| CEO personality | `agents/taizong/SOUL.md` | Make the CEO think like you want |
| Company strategy | `company/STRATEGY.md` | Your company's mission |
| Team roles | `agents/*/SOUL.md` | Each agent's personality |
| Your info | `agents/taizong/USER.md` | So the CEO knows who you are |

### Add Your Own Agents

See [`agents/_templates/`](../agents/_templates/) for the template. The key files:

- **SOUL.md** — Personality, philosophy, behavior
- **AGENTS.md** — Task-specific rules and guardrails
- **USER.md** — What this agent knows about you

## Architecture

```
You (Founder)
    │
    ▼
CEO Taizong (Main Agent)
    │
    ├── SOUL.md        ← Personality (Mao Zedong + Zizhi Tongjian)
    ├── MEMORY.md      ← 30 management insights from real ops
    ├── study/         ← Learning materials
    │   ├── mao-thought-1-4.md
    │   ├── zizhitongjian-01~10.md
    │   └── gstack-research/
    └── self-improving/ ← Self-evolution system
```

## FAQ

**Q: Do I need all 7 agents?**
A: No. Start with just the CEO (Taizong). Add agents as needed.

**Q: Can I change the CEO's name?**
A: Yes. Edit `agents/taizong/IDENTITY.md` and `agents/taizong/SOUL.md`. The historical model is part of the charm, though.

**Q: Does this work with Claude, GPT, Gemini?**
A: OpenClaw supports multiple LLM providers. Configure your preferred model in `openclaw.json`.

**Q: How do the agents communicate?**
A: Through OpenClaw's `sessions_send` API. Agents can message each other, spawn sub-agents, and collaborate on tasks.

## Troubleshooting

| Problem | Solution |
|---|---|
| `openclaw: command not found` | Install OpenClaw: `npm install -g @openclaw/cli` |
| `Health check FAILED` | Check the missing files in the error output |
| Chinese characters garbled | Ensure your terminal supports UTF-8 |
| 429 errors | Don't run too many agents concurrently. Start with 1–2. |
