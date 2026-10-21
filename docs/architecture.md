# 架构说明

本项目综合使用三种模式：
- 发布-订阅：MessageBus，Agent 间不直接调用
- 黑板模式：ShopState，所有 Agent 共享状态
- 状态机：OrderStatus，订单状态单向流转

库存由店长和库存 Agent 双重校验，防止并发超卖。
