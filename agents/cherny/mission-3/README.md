# Deep Agent 代码质量分析器

一个纯 Python 标准库实现的代码质量分析 CLI 工具。丢进去一个 Python 文件，输出结构化的质量报告。

## 功能

- 📊 **代码统计** — 行数、函数数、类数、注释比例
- 🔴 **问题检测** — 严重/警告/建议三级分类，覆盖 15+ 规则
- 🔄 **复杂度分析** — McCabe 圈复杂度，Top 10 排名
- 🔁 **重复代码检测** — AST 结构归一化 + 文本相似度双重匹配
- 🏆 **质量评分** — 0-100 综合评分

## 检测规则

| 级别 | 规则 | 说明 |
|------|------|------|
| 🔴 严重 | E001 | 裸 except 捕获 |
| 🔴 严重 | E003 | 空 except 体 |
| 🔴 严重 | D001 | 危险函数（eval/exec） |
| 🟡 警告 | F001 | 超大函数（>50行） |
| 🟡 警告 | E002 | 过宽异常捕获 |
| 🟡 警告 | N001 | 嵌套过深（>4层） |
| 🟡 警告 | C001/C002 | 类过大/方法过多 |
| 🟡 警告 | I001 | 通配符导入 |
| 💡 建议 | F002/F004 | 函数偏长/参数偏多 |
| 💡 建议 | M001/M003 | 缺少 docstring/文件过大 |

## 用法

```bash
# 分析单个文件
python -m codeanalyzer your_file.py

# JSON 格式输出
python -m codeanalyzer your_file.py --json

# 直接运行 demo（分析工具自身的源码）
python demo.py
```

## 项目结构

```
mission-3/
├── codeanalyzer/
│   ├── __init__.py      # 包入口
│   ├── __main__.py      # python -m 支持
│   ├── cli.py           # CLI 命令行入口
│   ├── analyzer.py      # 主分析流程
│   ├── stats.py         # 代码统计分析
│   ├── checks.py        # 问题检查规则
│   ├── complexity.py    # 圈复杂度计算
│   ├── duplicates.py    # 重复代码检测
│   └── report.py        # 报告生成与评分
├── tests/
│   └── test_analyzer.py # 34 个测试用例
├── demo.py              # 自我分析 demo
└── README.md
```

## 运行测试

```bash
python -m unittest discover -s tests -v
```

## 技术特点

- **零依赖** — 仅使用 Python 标准库（ast, re, collections 等）
- **AST 驱动** — 基于 Python AST 的精确分析，不是简单的正则匹配
- **双重重复检测** — AST 结构归一化 + LCS 文本相似度
- **可扩展** — 新增检查规则只需在 checks.py 中添加 visit 方法
