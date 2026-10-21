# 架构设计

## 三层架构

```
┌───────────────────────────────────────────────┐
│  CLI / Simulation (编排层)                    │
│  - 读配置、装配 Agent、跑 N 天                │
└───────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│  Agent 层     │◀────▶ │  事件总线     │
│ (6 个岗位)    │ Pub/Sub │ MessageBus  │
└──────────────┘        └──────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│  核心层 (core)                                  │
│  - ShopState 共享黑板                          │
│  - Order / FlowerItem / Customer 领域模型     │
│  - OrderStatus 状态机                          │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│  服务层 (services)                             │
│  - OrderRepository (SQLite)                   │
│  - ReportService (日报 / CSV)                │
│  - Logger / ConfigLoader                      │
└───────────────────────────────────────────────┘
```

## 一次订单的事件链

```
Sales.place_order()
  └─publish ORDER_RECEIVED
       └─> Manager: 校验库存+金额
             └─publish INVENTORY_CHECK_REQUEST
                   └─> Inventory: 二次校验 + 扣库存
                         └─publish MAKING_REQUEST
                               └─> Florist: 制作
                                     └─publish DELIVERY_REQUEST
                                           └─> Delivery: 配送 + 入账
```

## 为什么用发布订阅？

- **解耦**：销售不需要知道店长、库存、花艺师的存在
- **可扩展**：加一个新岗位（如"客服 Agent"）只需 subscribe 相关事件
- **可观测**：`bus.event_log` 保留全部事件，便于复盘
