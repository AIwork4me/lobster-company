---
name: lobster-ship
preamble-tier: 4
version: 1.0.0
description: |
  发布工作流：检测分支、运行测试、审查变更、更新版本、提交推送、创建PR。
  由 Chase（全栈工程师）执行。融合 gstack ship + 澳龙公司发布纪律。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

# 龙虾发布 — Chase 级 Ship 工作流

**"拿结果"是总经理对董事长的唯一承诺。发布就是拿结果。**

---

## Step 0: 预检

1. **分支检查** — 如果在基准分支上，中止："在基准分支上，不能 ship。切到功能分支。"
2. **状态检查** — 未提交的变更全部纳入
3. **变更概览** — 理解这次要 ship 什么

```bash
git branch --show-current
git status
git diff <base>...HEAD --stat
git log <base>..HEAD --oneline
```

---

## Step 1: 审查就绪看板

检查所有 review 状态：

```
+================================================================+
|                  任务就绪看板                                    |
+================================================================+
| 审查项         | 状态   | 必须通过 | 说明                     |
|---------------|--------|---------|--------------------------|
| CEO Review    | —      | 否      | 重大功能建议做           |
| 代码审查       | —      | ✅ 是   | 必须通过才能 ship        |
| QA 测试       | —      | 否      | 建议                     |
| 安全检查       | —      | 否      | 涉及凭证/权限时必须      |
+================================================================+
| 结论: [通过 / 未通过]                                            |
+================================================================+
```

**判断逻辑：**
- 代码审查通过 → CLEARED
- 代码审查未做或有问题 → NOT CLEARED，必须先修
- CEO Review / QA / 安全 → 建议但不阻塞（除非涉及安全敏感变更）

---

## Step 2: 运行测试

```bash
# 根据项目类型选择测试命令
# 优先读项目的 package.json / Makefile / CLAUDE.md 获取测试命令
# 如果找不到，问用户
```

- 测试全过 → 继续
- 测试有失败 → 停止，修完再 ship
- 没有测试 → 警告但继续（建议补测试）

---

## Step 3: 审查变更

1. `git diff <base>...HEAD` — 逐文件检查
2. 检查清单：
   - [ ] 没有调试代码（console.log、print、TODO hack）
   - [ ] 没有硬编码凭证
   - [ ] 没有意外提交的大文件
   - [ ] commit message 清晰
   - [ ] CHANGELOG 已更新

---

## Step 4: 版本和变更日志

1. 读取当前 VERSION 文件
2. 根据变更类型决定版本号：
   - 新功能 → minor 版本升级
   - Bug修复 → patch 版本升级
   - 破坏性变更 → major 版本升级
3. 更新 CHANGELOG.md：
   - 面向用户写，不面向开发者
   - "用户现在能做什么以前不能做的"
   - 不提内部实现细节

---

## Step 5: 提交和推送

```bash
# 逐项提交（bisect commits）
# 每个 commit 是一个逻辑变更
# 不用 git add .，逐文件 add

git add [具体文件]
git commit -m "type(scope): description"
git push -u origin HEAD
```

---

## Step 6: 创建 PR

```bash
gh pr create --title "type(scope): title" --body "## What
[用户能做什么新事]

## Why
[为什么做]

## Changes
[变更列表]

## Testing
[测试情况]

## Review Checklist
- [ ] CEO Review: [状态]
- [ ] Code Review: [状态]
- [ ] QA: [状态]"
```

---

## Step 7: 发布报告

输出格式：

```
## 发布报告

| 项目 | 结果 |
|------|------|
| 分支 | [branch] |
| 变更文件数 | [N] |
| 测试 | ✅通过 / ❌失败 / ⚠️无测试 |
| 代码审查 | ✅通过 |
| 版本 | [old] → [new] |
| PR | [链接] |
```
