# 纠正记录 - 每次被纠正后永久改进

## 2026-03-19
- **C1**: 没读磁盘文件就回复"我刚上线"→ 完全丢失身份认知
  - 修复：SOP S1 - 每次session第一步读磁盘文件
- **C2**: 搜索只在pm/目录内→ 漏掉agents/全部7个员工
  - 修复：SOP S3 - 工作目录≠认知边界
- **C3**: 主session堆7篇笔记+大量web fetch→ 138k爆掉
  - 修复：SOP S2 - 长任务spawn子代理

## 2026-03-22
- **C4**: .env写了Key但OpenClaw不读→ 所有agent用GM配额
  - 修复：用openclaw.json注册独立provider，spawn时用model参数指定
  - 教训：M9 - 配置即生效是假设不是事实
