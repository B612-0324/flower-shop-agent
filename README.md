# 花店多Agent协作运营模拟系统 2.1

七个**规则驱动Agent（非LLM）**通过进程内同步发布订阅消息总线和共享黑板协作，模拟接单、审批、批次出库、制作、配送收款、日终报损补货、客户回访建议及日报。业务运行仅使用Python标准库，不接入外部AI、云服务或外部数据库。客户为合成演示数据。

## 运行

Python 3.10+，推荐3.13。源码方式无需安装依赖：

```bash
python main.py --days 7 --seed 42 --output-dir outputs/demo_7d_seed42
python main.py --days 14 --seed 7 --output-dir outputs/demo_14d_seed7
python main.py --config config/shop_config.json --db shop.db --csv orders.csv --summary summary.json --dashboard dashboard.html
python main.py --no-dashboard
```

上述`python`表示本机Python解释器；托管环境请替换为解释器绝对路径。所有文件路径支持裸文件名、相对路径和绝对路径。`--days`必须为正整数，`--seed`为整数。默认7天、seed=42，默认输出`data/`。不传`--config`时使用包内默认资源；修改外置配置后应显式传`--config`。

安装方式（建议虚拟环境，不做全局安装）：

```bash
python -m pip install .
flower-shop --days 7 --seed 42 --output-dir data
python -m flower_shop.cli --days 7 --seed 42
```

`main.py`、模块入口与安装控制台入口均调用`src/flower_shop/cli.py`。顶层`agents/`、`core/`、`visualization/`只保留旧导入路径适配，实际业务只有src一套；旧FlowerItem构造参数顺序有兼容适配。默认配置随wheel打包，仓库外也可运行。

## 七个Agent

| Agent | 规则职责 |
|---|---|
| 销售 | 校验客户与花材数量，花材VIP折扣后加包装、配送、加急收费 |
| 店长 | 校验库存，自动审批或规则特批，拒绝缺货单 |
| 库存 | 二次校验、先到期先出FEFO、批次老化、报损、低库存预警 |
| 采购 | 安全库存补货，保留周转金，新批次不刷新旧批次保鲜期 |
| 花艺师 | 模拟制作时长，加急更快，不进行真实sleep等待 |
| 配送 | 区分配送与自提，完成后一次收款与确认销售成本 |
| 市场 | 根据已完成订单累计消费生成最高价值客户回访建议 |

## 业务口径

- 状态依次为PENDING → CONFIRMED → MATERIAL_READY → MAKING → READY → DELIVERING → COMPLETED；自提从READY直接完成；审批或出库失败进入REFUSED。阶段检查阻止重复消息造成重复扣料和收款。
- 每种花材维护数量和剩余保鲜天数的批次，先到期先出；当天营业结束后老化，剩余天数到0报损，再执行补货。日终每个day只执行一次，同一天同花材补货事件幂等。
- 采购记现金支出与库存资产，不在采购时重复计损益。销售成本在订单完成时确认，报损进入损益。利润=营收−销售成本−报损；现金=初始现金+营收−采购支出。初始库存是期初资产，不再次扣初始现金。本演示不包含租金、工资、税费或包装实际成本，利润不能视为真实净利润。
- 每日输出为当日增量，累计汇总另存；日终先报损补货、市场分析，最后生成日报和数据库快照。
- 使用每次Simulation独立的Random与客户、订单序号、库存深拷贝；相同配置与seed可复现。每次运行创建新ShopState/Simulation，同对象二次run明确报错。
- SQLite每次运行生成独立run_id；订单保存真实下单day、JSON花材、日终批次快照、每日指标和顺序时间线。旧表保留，新版使用run_*表，不迁移或混合旧历史。
- 同步单线程模型不代表分布式事务、并发锁或真实物流系统。异常处理器失败显式传播，避免静默假成功；不支持中断续跑。

## 输出

`summary.json`含运行标识、参数、七Agent标识、累计经营指标、每日指标、库存和产物路径；`orders.csv`为订单流水；`timeline.json`和SQLite保存协作事件；`flower_shop.log`记录实际运行。HTML仪表盘完全离线，展示每日营收趋势、当日指标、订单、库存批次和Agent时间线，所有文本经过HTML转义。

## 测试与交付

```bash
python -m pip install '.[dev]'
python -m pytest tests -v
python -m unittest discover -s tests -p test_regression.py -v
```

`docs/validate_delivery.py`用于隔离环境全套验证：全量pytest、标准库回归、指定两组模拟、wheel构建及仓库外安装模块/控制台入口运行。参见`docs/test_report.md`和`outputs/logs/`的实际记录。`outputs/summary.json`为交付总索引，演示目录有各自summary与仪表盘。完整项目zip不含.git、缓存、venv或真实个人资料。
