# 花店多 Agent 协作运营模拟系统

一个工程化的多 Agent 协作模拟项目：用 6 个自治 Agent 模拟一家实体花店从接单、审批、出库、制作、配送到日终盘点、补货、出报表的完整运营闭环。

## 一、项目结构

```
flower_shop_project/
├── config/
│   └── shop_config.json          # 价格、库存、VIP 折扣等配置
├── data/                          # 运行时生成：SQLite + CSV
├── docs/
│   ├── architecture.md            # 架构说明
│   └── runbook.md                  # 运维手册
├── logs/                          # 运行日志
├── src/flower_shop/
│   ├── core/                      # 领域层：枚举、事件、模型、状态
│   ├── agents/                    # 6 个岗位 Agent
│   ├── services/                  # 日志、配置、持久化、报表
│   ├── simulation.py               # 模拟编排器
│   └── cli.py                     # 命令行入口
├── tests/                         # pytest 单元测试
├── pyproject.toml
└── requirements.txt
```

## 二、快速开始

```bash
# 1. 进入项目目录
cd flower_shop_project

# 2. 把 src 加到 Python 路径（或 pip install -e .）
export PYTHONPATH=src

# 3. 跑 3 天模拟
python -m flower_shop.cli --days 3

# 4. 跑测试
pip install pytest
pytest tests/ -v
```

## 三、命令行参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--days` | 3 | 模拟天数 |
| `--config` | config/shop_config.json | 配置文件 |
| `--db` | data/shop.db | SQLite 路径 |
| `--seed` | 42 | 随机种子（可复现） |

## 四、Agent 角色

| Agent | 职责 | 订阅事件 |
|---|---|---|
| SalesAgent | 接单、计价、VIP 折扣 | — |
| ShopManagerAgent | 订单审批、库存校验 | ORDER_RECEIVED |
| InventoryAgent | 锁料出库、报损、预警 | INVENTORY_CHECK_REQUEST / DAILY_REPORT_REQUEST |
| PurchasingAgent | 按资金约束补货 | LOW_STOCK_WARNING |
| FloristAgent | 制作花束 | MAKING_REQUEST |
| DeliveryAgent | 配送/自提、收款 | DELIVERY_REQUEST |

## 五、核心设计

- **事件驱动**：Agent 之间通过 `MessageBus` 发布订阅通信，不直接调用
- **共享黑板**：所有状态（库存、订单、钱）放在 `ShopState`，全局可见
- **配置外置**：所有价格、库存、折扣在 `config/shop_config.json`
- **持久化**：订单流水与每日库存快照写入 SQLite，可重复查询
- **可观测**：`logs/flower_shop.log` 全量日志，`data/orders.csv` 可直接 Excel 打开

## 六、扩展方向

1. 把店长 / 花艺师 Agent 的规则替换为 LLM 调用
2. 加 Web 仪表盘（Flask + 前端）实时展示库存曲线
3. 用时间序列模型预测次日销量，提前采购
4. 多店场景：引入总部 Agent 跨店调拨
