# 《资治通鉴》第二遍阅读计划（v3 - 最终版）

> 作者：太宗 | 开始时间：2026-03-27
> 核心问题：**如何把澳龙公司做到年净利润1亿人民币？**
> v3更新：使用spawn子代理隔离context，彻底解决中断问题

---

## ✅ 上下文管理策略（v3最终版）

### 方案选择

| 方案 | 可行性 | 说明 |
|------|--------|------|
| ❌ 手动压缩 | 不可行 | OpenClaw无公开的slash命令触发compact |
| ⚠️ 依赖自动压缩 | 有风险 | 消耗API配额，429时会失败 |
| ✅ **spawn子代理** | **最佳** | context天然隔离，无此问题 |

### 最终方案：spawn子代理

每批次作为一个**独立子代理任务**执行：
- 每个batch是独立session，context天然隔离
- 不需要手动压缩
- 不需要担心context爆炸
- checkpoint.json支持断点续传

---

## 一、执行流程

### 董事长触发
`
董事长：开始批次N
  ↓
太宗：spawn子代理执行批次N
  ↓
子代理：
  1. 读取checkpoint.json
  2. 读取5卷原文
  3. 输出[史实]-[洞察]-[行动]-[比较]
  4. 写入round2-logs/batch-N.md
  5. 更新checkpoint.json
  6. 报告完成
  ↓
太宗：收到结果，向董事长报告
`

---

## 二、子代理任务模板

`
任务：
1. 读取 checkpoint.json 确定起始卷
2. 读取 5 卷原文（从 C:\Users\ASUS\Desktop\zizhitongjian\）
3. 读取第一遍笔记（从 C:\Users\ASUS\Desktop\lobster-company\references\zizhitongjian-XX.md）
4. 逐卷输出：
   【史实】发生了什么（1-2句）
   【洞察】对澳龙公司的启示（1-3条）
   【行动】我们应该做什么不同
   【比较】与第一遍对比，哪个更有利于'年净利润1亿'？
     - 升级 ✅ / 保留 ⭕ / 融合 🔀
5. 写入 round2-logs/batch-N.md
6. 更新 checkpoint.json
7. 报告完成

核心问题：如何把澳龙公司做到年净利润1亿人民币？
`

---

## 三、文件结构

`
lobster-company/references/
├── zizhitongjian-round2-plan.md          # 本计划（v3）
├── zizhitongjian-round2-report.md        # 学习心得报告（追加）
├── zizhitongjian-round2-checkpoint.json  # 断点记录
└── round2-logs/                          # 每批次日志
    ├── batch-01.md                       # 卷1-5
    ├── batch-02.md                       # 卷6-10
    └── ...
`

---

## 四、阅读计划（约50批次）

| 周次 | 批次 | 卷号 | 主题 | 状态 |
|------|------|------|------|------|
| 1 | 1 | 1-5 | 周纪：三家分晋 | ⏳ |
| 1 | 2 | 6-8 | 秦纪：商鞅变法 | ⏳ |
| 1 | 3 | 9-13 | 汉纪初：刘邦创业 | ⏳ |
| ... | ... | ... | ... | ... |

---

## 五、风险预案

| 风险 | 应对 |
|------|------|
| 子代理失败 | checkpoint记录断点，重试该批次 |
| API 429 | 子代理间隔执行，不并发 |
| 输出过长 | 每卷控制在500字内 |

---

## 六、执行日志

### 2026-03-27

- ✅ 创建阅读计划 v1
- ✅ 反思上下文风险
- ✅ 更新为 v2（增加上下文管理）
- ✅ 调研OpenClaw compact机制
- ✅ 更新为 v3（使用spawn子代理）
- ⏳ 开始批次1...

---

## 七、学习心得报告（持续追加）

> 报告位置：zizhitongjian-round2-report.md

### 待填写...
