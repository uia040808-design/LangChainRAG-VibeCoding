---
name: unit-test
description: 为项目代码创建单元测试、执行测试并生成测试报告
allowed-tools: Bash(pip *), Bash(pytest *), Bash(python *)
user-invocable: true
---

# 单元测试

为当前项目的 Python 代码创建单元测试，执行测试，并生成测试报告。

## 什么是单元测试

单元测试就像是给代码写的"自动检查员"——提前写好检查规则，每次代码改动后跑一遍，确保之前的功能没被改坏。

## 执行步骤

1. **安装依赖** — 确保 `pytest` 已安装
2. **分析代码** — 找到项目中可以被测试的函数和类
3. **编写测试** — 针对核心功能创建测试用例
4. **执行测试** — 运行 pytest
5. **生成报告** — 汇总测试结果，显示通过/失败详情

## 编写测试的原则

- 测试文件的命名：`test_<原文件名>.py`，放在 `backend/tests/` 目录下
- 测试函数命名：`test_<被测函数名>_<测试场景>`
- 每个测试覆盖一种情况（正常、边界、异常）
- 数据库测试使用临时文件，不影响真实数据
- 涉及 API 调用的测试使用 mock 模拟

## 常用命令

检查 pytest 是否安装：
```bash
pip show pytest 2>&1 >/dev/null || pip install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple
```

运行测试（详细报告）：
```bash
python -m pytest backend/tests/ -v
```

运行测试（含覆盖率）：
```bash
pip show pytest-cov 2>&1 >/dev/null || pip install pytest-cov -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m pytest backend/tests/ -v --tb=short
```
