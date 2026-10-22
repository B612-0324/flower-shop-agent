# 实际测试与交付记录

执行时间：2026-10-22（本地工作区，Python 3.13 隔离验证环境）。

## 命令与结果

| 验证项 | 结果 |
|---|---:|
| `pytest tests -v` | 32 passed，5 subtests passed |
| `unittest discover ... test_regression.py` | 25 tests passed，5 subtests passed |
| 7天、seed=42、源码入口 | 返回码 0 |
| 14天、seed=7、源码入口 | 返回码 0 |
| `pip wheel . --no-deps --no-build-isolation` | 返回码 0，生成 `flower_shop_agent-2.1.0-py3-none-any.whl` |
| wheel `pip install --target` | 返回码 0 |
| 安装后 `python -m flower_shop.cli` | 返回码 0 |
| 安装后 `flower-shop.exe` | 返回码 0 |

全量命令的完整合并输出保存在 `outputs/logs/`，JUnit XML 在 `outputs/test-results.xml`，命令与返回码机器记录在 `outputs/validation_commands.json`。

## 演示指标

### 7天 / seed=42

- 订单 40；完成 31；拒绝 9
- 营收 ¥4,242.60；销售成本 ¥1,814.40；报损 ¥381.00；利润 ¥2,047.20
- 采购现金支出 ¥2,089.00；期末现金 ¥7,153.60
- 时间线事件 460；七个Agent；run_id见对应summary.json

### 14天 / seed=7

- 订单 91；完成 75；拒绝 16
- 营收 ¥9,580.25；销售成本 ¥3,984.20；报损 ¥299.00；利润 ¥5,297.05
- 采购现金支出 ¥4,090.00；期末现金 ¥10,490.25
- 时间线事件 1,075；七个Agent；run_id见对应summary.json

以上是规则模拟指标，不是现实经营预测。由于修改了业务口径与可复现客户池，不能与旧README中的历史数字直接比较。

## 覆盖范围

包含入口统一、参数校验、裸文件名输出、配置边界、七Agent装配、状态机非法跳转、订单和日终重复事件幂等、FEFO与批次鲜度、原子库存校验、采购/销售成本口径、周转金、seed复现、跨次状态隔离、SQLite run_id/真实订单day/库存批次/日报/时间线、HTML转义、配送/自提、安装入口及全量旧测试。
