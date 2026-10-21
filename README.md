# 花店多 Agent 协作运营模拟系统 v2.0

一个基于**发布-订阅消息总线 + 共享黑板**的多 Agent 协作模拟系统，模拟一家实体花店
连续 N 天的完整运营：接单、审批、出库、制作、配送、收款、日终盘点、花材报损、
自动补货、出报表。

零第三方依赖，Python 3.8+ 标准库即可运行。

## 快速开始

```bash
python main.py                  # 默认模拟 7 天
python main.py --days 14        # 模拟 14 天
python main.py --seed 42        # 固定随机种子，结果可复现
python main.py --no-dashboard   # 不生成 HTML 仪表盘
```

运行后打开 `data/dashboard.html` 即可看到可视化运营仪表盘。

## 七个 Agent

| Agent | 职责 |
|---|---|
| 销售Agent | 接待客户、计价（花材费+包装+配送+加急×VIP折扣）、创建订单 |
| 店长Agent | 审批订单、校验库存、金额特批、生成日报 |
| 库存Agent | 锁料出库、花材鲜度扣减与报损、低库存预警 |
| 采购Agent | 响应补货预警、按资金约束（保留1000元周转金）采购入库 |
| 花艺师Agent | 制作花束，加急单更快 |
| 配送Agent | 上门配送/到店自提、收款入账 |
| 市场Agent | 分析高价值客户、提醒回访、随机促销 |

## 架构

```
客户下单
  └─> 销售Agent: 发布 ORDER_RECEIVED
        └─> 店长Agent: 校验库存 → 发布 INVENTORY_CHECK_REQUEST
              └─> 库存Agent: 二次校验 + 扣库存 → 发布 MAKING_REQUEST
                    └─> 花艺师Agent: 制作 → 发布 DELIVERY_REQUEST
                          └─> 配送Agent: 配送 + 入账
日终: DAILY_REPORT_REQUEST
  ├─> 库存Agent: 花材报损 + 低库存预警 → LOW_STOCK_WARNING
  │     └─> 采购Agent: 资金够就进货
  ├─> 市场Agent: VIP 回访提醒
  └─> 店长Agent: 打印日报
```

## 项目结构

```
flower_shop_project/
├── main.py                  # 入口（CLI 参数解析 + 装配 Agent）
├── config/
│   └── shop_config.json      # 价目表/费用/VIP折扣/安全库存（外置配置）
├── core/
│   ├── enums.py              # 订单状态机 / 花材品类 / 事件类型
│   ├── message_bus.py        # 发布-订阅消息总线
│   ├── shop_state.py         # 共享黑板（库存/订单/账务）
│   └── logger.py             # 统一日志（控制台 + 文件）
├── agents/
│   ├── base_agent.py
│   ├── sales_agent.py
│   ├── shop_manager_agent.py
│   ├── inventory_agent.py
│   ├── purchasing_agent.py
│   ├── florist_agent.py
│   ├── delivery_agent.py
│   └── marketing_agent.py     # v2.0 新增
├── visualization/
│   └── generate_dashboard.py  # 生成 HTML 仪表盘
├── tests/
│   └── test_smoke.py         # 冒烟测试
├── docs/
│   └── architecture.md
└── data/                     # 运行后自动生成
    ├── orders.csv            #   订单流水
    ├── shop.db               #   SQLite 持久化
    ├── simulation.log         #   运行日志
    └── dashboard.html         #   可视化仪表盘
```

## v2.0 新特性

- **配置外置**：价目表、费用、VIP折扣全部在 `config/shop_config.json`，改数字不用动代码
- **统一日志**：`logging` 模块，同时输出控制台和 `data/simulation.log`
- **SQLite 持久化**：订单和库存写入 `data/shop.db`，程序重启不丢
- **订单时间线**：每笔订单记录经过哪些 Agent、何时、做了什么
- **花材保鲜模型**：每枝花有 shelf_life，每天鲜度-1，到 0 自动报损
- **VIP 复购**：VIP 越高当天复购概率越大
- **CLI 完善**：`--days`、`--seed`、`--db`、`--no-dashboard`
- **市场Agent**：分析高价值客户，提醒老板回访

## 实测数据（7 天模拟，seed=42）

- 总订单：41 笔（完成 32 / 拒绝 9）
- 营收：¥4954.85
- 成本：¥4147.90
- 利润：¥806.95（毛利率 16.3%）
- 自动补货：2 次（玫瑰、郁金香）
- 花材报损：郁金香 12 枝
