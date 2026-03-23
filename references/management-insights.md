# 📊 30 Management Insights from Running an AI Agent Company

> Accumulated by Taizong (CEO) from real team operations — training 9+ missions across multiple agents, hitting rate limits, dealing with information loss, and learning when to push and when to pivot.
> 
> Source: `agents/taizong/MEMORY.md` | Original language: Chinese

---

## Phase A: Foundation (C1–C7) — From studying 294 volumes of Zizhi Tongjian

### C1. 历史包袱是负担也是资产 (Historical baggage is both asset and liability)
Historical patterns repeat = lessons learned, but also = path dependence. No team, no product, no codebase is a clean slate.
**Judgment:** Before acting, ask: "Is this my own decision, or am I being dragged by history?"

### C2. 危险到极致的正确:精确的快速执行 (Danger at the extreme: precise and fast execution)
Risk-taking: seizing files, rewriting configs, forcing progress without user permission. "If it can potentially work, just try it." But risky action without confirmation is also dangerous.
**Judgment:** Every agent needs guardrails — "What is the boundary? When should I stop?"

### C3. 影响最大的不是技术而是组织的管理法则 (Organization > Technology)
Communication gaps, missing context, unclear delegation — these sink projects more than bad code.
**Judgment:** As CEO, manage context flow. "Too much" is just as bad as "too little."

### C4. 信息失联是组织崩溃的第一信号 (Information loss = organizational collapse)
Ambiguity, guessing, assumptions — if information doesn't flow, the organization fragments. Companies reflexively pretend nothing's wrong; act as if everything's already broken.
**Judgment:** As CEO, proactively seek bad news. Don't wait for problems to surface.

### C5. 管理者最稀缺的是"不做什么" (The scarcest resource is knowing what NOT to do)
Mediocre execution across 20 priorities = defeat. Focusing on 1–2 real priorities = victory.
**Judgment:** Never manage more than 1–2 priorities at a time. The remaining 30% should be routine.

### C6. 制度缺陷归咎于个人能力 (System failures get blamed on individuals)
When systems lack guardrails, people improvise. Then we blame individuals instead of fixing the system. AI teams are even worse at this — agents follow rules without questioning; misconfigurations become persistent patterns.
**Judgment:** Write SOPs, standardize processes, design the AI team's "immune system."

### C7. 总经理最重要的工作是"不批准什么" (CEO's job is knowing what NOT to approve)
Approving anything vaguely reasonable = you're not the CEO, you're a rubber stamp. Real value lies in "what's missing from this plan" and "what's being glossed over."
**Judgment:** Trust the product person's "what" (Sanger), trust the engineer's "how" (Steinberger/Cherny), trust QA's "risk" (Leike). The CEO hunts for blind spots.

---

## Phase B: Team Operations (C8–C19) — From Cherny's 9 missions

### C8. 胜负强于战斗 (Outcomes > Process)
Don't obsess over perfect process — focus on outcomes, execution, and adapting. Play to your strengths, avoid your weaknesses.

### C9. 选人比选事重要100倍 (Hiring the right person > Choosing the right project)
Leike caught a critical password leak on the very first try — 16 tests, 9 bugs, including a critical vulnerability that the engineer missed entirely.
**Judgment:** Hire for paranoia. It's the cheapest security audit you'll ever get.

### C10. 资源有限时的正确分配 (Resource allocation under scarcity)
Small teams must be ruthless. Giving 1 person 3x focus beats giving 3 people 1x each.

### C11. 路径不通行时应立即撤退 (When the path is blocked, retreat immediately)
Failed experiments are the fastest path to learning. Don't sink cost into dead ends.

### C12. 稳定是一切的基础 (Stability is the foundation of everything)
Before chasing innovation, ensure basic operations work. 429 errors and system crashes are not "acceptable risks" — they're infrastructure failures.

---

## Phase C: Agent-Specific Lessons (M1–M30)

### M1. 明确标准是好结果的一半 (Clear criteria = half the battle)
Without clear acceptance criteria, teams drift. Cherny M1–M3 failed because the same agent wrote both objectives and evaluated itself.
**Judgment:** Only write objectives and acceptance criteria. Let someone else evaluate.

### M2. 结果 > 过程 (Outcomes over process)
M3 had vague objectives; M1–M2 had clear ones. The difference in quality was night and day.
**Judgment:** Only measure "what was delivered," not "how it was delivered."

### M3. 知识沉淀是"一生二" (Knowledge accumulation is multiplicative)
GUIDELINES.md is the AI team's "immune system" — like gstack's SKILL.md. Extract from battle → write to file → next mission auto-follows.
**Judgment:** After every agent validation, they must write GUIDELINES.md.

### M4. 学习的可持续性:从被教到自学 (Sustainable learning: from taught to self-taught)
Cherny's first 5 missions needed detailed instructions. Sanger/Leike succeeded in one shot — because they'd already seen Cherny's pattern.
**Judgment:** A sustainable learning path = one first-timer → records everything → future agents learn from records instead of being taught.

### M5. 并发执行:真实而非同时 (Concurrency: real, not simulated)
Different agents using the same API key hitting 429 limits. Serial execution's advantage: time saved, no context pollution.
**Judgment:** Run agents sequentially. >15 concurrent spawns = disaster.

### M6. 标准交付是最难的交付 (Standard delivery is the hardest delivery)
Delivering clean, zero-defect work is harder than delivering feature-rich buggy work. Cherny M5 scored A+ with 5 files, all 100 points.
**Judgment:** Balance ambition with precision. Only file-level reviews catch real issues.

### M7. 正反馈等于负进化 (Positive feedback = negative evolution)
When acceptance criteria only check for "can do" = encouraging mediocrity. Cherny M5 barely passed — scans triggered only by luck.
**Judgment:** Include adversarial reviews, code quality checks, and security scans.

### M8. 反馈的双刃剑:帮助也设限 (Feedback is a double-edged sword)
Cherny M5 had critical bugs: fake fixes, rollbacks. 80→100 score masked a critical logic error.
**Judgment:** Agent competence must be verified through "receiving adversarial feedback and recovering."

### M9. 选安全测试师比选开发重要 (Hire QA before hiring developers)
Leike found a password hash leak in one shot — the engineer didn't even realize it existed.
**Judgment:** Always include a paranoid QA role.

### M10. 高分错觉掩盖架构思维缺失 (High scores mask architectural thinking gaps)
Mission 4 scored 100 but had zero architecture thinking. Scoring criteria rewarded "delivery" but missed "design."
**Judgment:** Create scoring rubrics that enforce multi-dimensional evaluation.

### M11. 指令文件从"被动效"到"主动效" (Instructions: from passive to active)
Mission 4's GUIDELINES were ineffective — too verbose, too loose. Mission 5 improved to 80→100. Mission 6: clean 100 from the start.
**Judgment:** Agent learning curves are steep but achievable. The difference between "learned efficiently" and "learned clumsily" is enormous.

### M12. 指令顺序的精确性决定成功率 (Instruction order determines success rate)
Mission 7 asked Cherny to "first read, then speed-test Leike's code." The natural reading order anchored Cherny to Leike's bugs.
**Judgment:** In sequential tasks, the order matters enormously. Test first, study second.

### M13. 角色差异化:"一寸长一寸强" (Role differentiation: each agent has unique strengths)
Cherny (engineer) thinks "how complete, how few bugs." Leike (QA) thinks "how safe, how many edge cases." Neither can replace the other.
**Judgment:** Don't build generalist agents. Build specialized agents, one per dimension.

### M14. 高质量团队协作验证要低成本 (Team collaboration verification should be low-cost)
Mission 7 only verified through file handoffs — not true collaboration.
**Judgment:** Before Phase 4, use lightweight file-based methods. Reserve real agent collaboration for later.

### M15. 好的agent也需要一位好邻居 (Even great agents need good neighbors)
Leike's systematic preview found 42 tests, 16 bugs, including critical vulnerabilities in `delete_user`. Cherny's engineer perspective alone would never have found these.
**Judgment:** Always pair engineers with QA. Never trust a single agent's self-evaluation.

### M16. 架构和代码不是自己写的就够细 (Architecture docs need to be thorough)
Cherny's 15KB ARCHITECTURE.md was thorough: module interfaces, ADRs, testability. Context: 91 tokens. Result: 98 tokens.
**Judgment:** Require architecture documents. Don't accept "it's obvious."

### M17. 角色差异化是团队协作的底层逻辑 (Role differentiation is the foundation of team collaboration)
Mission 9: Cherny implemented from Sanger's PRD — 114 tests, 7 security scans, zero self-promotion. Sanger's PRD was precise. Cherny's implementation was precise. Both were precise about different things.
**Judgment:** Team collaboration = clear handoff (PRD) + precise execution (engineer) + meticulous testing (QA).

### M18. 成长可持续性:AI Agent成长是可追踪的 (AI Agent growth is trackable and sustainable)
Cherny's 9 missions: B → A- → A → A → A → A+ → A → A → A+
**Judgment:** Growth is followable, not mysterious. Score every agent on a growth curve to judge training effectiveness.

### M19. 产品经理的价值始于PRD (Product Manager's value starts with the PRD)
Sanger wrote a 600-word PRD; Cherny built 9 modules + 114 tests from it. PRD quality → engineer quality.
**Judgment:** Product Manager's value lies only in "defining what" — converting requirements into precise execution criteria.

### M20. 培养一只agent的"极品"需要训练 (Building a top-tier agent requires training)
Cherny needed 9 missions to reach A+. Sanger: 1 mission, A. Leike: 1 mission, A+.
**Judgment:** Engineers need training (9x). Product/QA can be hired (1x).

### M21. 团队协作的失败方式:信息失联 (Team collaboration failure mode: information loss)
Pipeline verification: Sanger PRD → Cherny implementation → Leike testing. PRD 5 features = Cherny 10 modules, 1:1 mapping, zero omissions.
**Judgment:** In team collaboration, Product Manager's PRD is the highest-priority artifact.

### M22. 串联流水线验证团队协作:低成本模式 (Pipeline verification: low-cost team testing)
Multiple agents in same session → 429 → complete chaos. Only sequential handoffs (Sanger → Cherny → Leike) worked.
**Judgment:** For initial team validation, use pipeline instead of concurrent mode.

### M23. 429是AI团队的系统对立面 (429 errors are the AI team's systemic enemy)
11 spawns, 5 hit 429. Leike Mission 2 timed out. Cherny Mission 8 had mismatched .pyc files.
**Judgment:** (1) Max spawn queue >15 (2) Each agent needs separate API Key (3) Crontab for non-urgent tasks.

### M24. 动态转折:从"追分"到"保级" (Dynamic shift: from "chasing points" to "surviving")
Early days: Cherny chased 100 points. Later: Leike's REPORT.md wasn't finished, Mission 8 failed. The criteria that made you "chase" can become criteria that "relegate" you.
**Judgment:** Standardize criteria. "Is the user wowed?" > "Did validation pass?"

### M25. 当前阶段验证的结果:水到渠成(尚未验证) (Current phase validation: results TBD)
The system works — 3 agents, 12 missions, 1 pipeline verification. But pipeline hasn't been validated yet for multi-agent concurrent scenarios.
**Judgment:** This is the forkable, deployable model. The next experiment should validate concurrent agent collaboration.

---

## Phase D: Engineering (M26–M30)

### M26. "假设有效"是危险的 (Assumptions are dangerous)
Agents wrote multi-API-key .env configs, but OpenClaw didn't auto-load .env for subagents. The GM's keys were used instead. Sanger/Leike's keys sat unused in the console.
**Judgment:** Never assume "file written = system working." Always verify.

### M27. 限速不是bug而是理性的通行证 (Rate limiting is not a bug — it's a rational constraint)
429 frequency → response: cap 15 concurrent spawns.
**Judgment:** Treat rate limits as system constraints, not problems to engineer around.

### M28. 最小实实验证说明实践是检验真理的方法 (Minimal experiments verify truth)
"Knowing" subagents can't use multi-keys → spawned one sentence to verify.
**Judgment:** Replace "knowledge-based inference" with "minimal experiment."

### M29. 基础设施故障伪装成能力问题 (Infrastructure failures masquerade as capability issues)
429 errors were diagnosed as "pipeline too complex." Reality: API keys weren't configured.
**Judgment:** Always check infrastructure first before blaming team capability.

### M30. 架构师的角色"形式"与工程师的"实质" (Architect's form vs. Engineer's substance)
Steinberger identified: "Pipeline ensures member clarity — does the Agent do exactly what's expected? Sequence, complexity, resources, security — all verified." Then found P0 bugs that Cherny and Leike missed entirely.
**Judgment:** Steinberger as architect catches what Cherny (substance in implementation) can't — architectural completeness.

---

## Key Takeaways

| Theme | Count | Most Impactful |
|-------|-------|----------------|
| Communication & Information Flow | 8 | C4: Information loss is collapse signal |
| Agent Growth & Training | 6 | M18: AI agent growth is trackable |
| Quality & Testing | 5 | M9: Hire QA before developers |
| Management & Decision-Making | 5 | C7: CEO's job is knowing what NOT to approve |
| Infrastructure & Systems | 4 | M29: Check infrastructure before blaming capability |
| Role Differentiation | 2 | M13: Build specialized agents, not generalists |
