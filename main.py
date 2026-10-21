# -*- coding: utf-8 -*-
"""
花店多 Agent 协作运营模拟系统 v2.0
用法：
    python main.py                    # 默认 7 天，seed=42
    python main.py --days 14 --seed 7 # 可复现的 14 天模拟
    python main.py --no-dashboard     # 不生成 HTML
    python main.py --db data/shop.db  # 指定 SQLite 路径
"""
import argparse
import csv
import os
import random
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logger
from core.message_bus import MessageBus, Message
from core.shop_state import ShopState, Customer
from core.enums import FlowerType, EventType
from agents import (
    SalesAgent, ShopManagerAgent, InventoryAgent,
    PurchasingAgent, FloristAgent, DeliveryAgent, MarketingAgent,
)


CUSTOMER_POOL = [
    Customer("张小姐", "138****1001", vip_level=2),
    Customer("李先生", "139****2002", vip_level=1),
    Customer("王女士", "137****3003", vip_level=0),
    Customer("陈先生", "136****4004", vip_level=0),
    Customer("刘女士", "135****5005", vip_level=1),
    Customer("赵先生", "134****6006", vip_level=2),
    Customer("孙先生", "133****7007", vip_level=0),
    Customer("周女士", "132****8008", vip_level=1),
]

BUNDLES = [
    {FlowerType.ROSE: 19, FlowerType.EUCALYPTUS: 5, FlowerType.BABY_BREATH: 3},
    {FlowerType.LILY: 6, FlowerType.EUCALYPTUS: 4},
    {FlowerType.SUNFLOWER: 5, FlowerType.CARNATION: 10, FlowerType.BABY_BREATH: 4},
    {FlowerType.TULIP: 12, FlowerType.EUCALYPTUS: 3},
    {FlowerType.CARNATION: 20, FlowerType.BABY_BREATH: 5},
    {FlowerType.ROSE: 33, FlowerType.BABY_BREATH: 10},
]


def simulate_one_day(sales: SalesAgent, day: int):
    n = random.randint(3, 7)
    sales.log.info(f"--- 第 {day} 天：{n} 位客户进店 ---")
    for _ in range(n):
        cust = random.choice(CUSTOMER_POOL)
        bundle = random.choice(BUNDLES)
        sales.place_order(
            cust, bundle,
            note=random.choice(["", "生日", "探望", "教师节", "纪念日"]),
            is_delivery=random.random() < 0.7,
            is_urgent=random.random() < 0.2,
        )
        if random.random() < cust.repeat_prob(sales.state.config):
            sales.place_order(random.choice(CUSTOMER_POOL),
                              random.choice(BUNDLES), note="复购")


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY, customer TEXT, vip_level INT,
        items TEXT, total REAL, cost REAL, status TEXT,
        day INT, note TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS inventory (
        type TEXT PRIMARY KEY, stock INT, freshness INT, day INT)""")
    conn.commit()
    return conn


def save_to_db(conn, state):
    c = conn.cursor()
    for o in state.orders.values():
        items_str = ";".join(f"{k.value}x{v}" for k, v in o.items.items())
        c.execute("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?,?,?,?)",
                  (o.order_id, o.customer.name, o.customer.vip_level,
                   items_str, o.total_price, o.cost, o.status.value,
                   state.day, o.note))
    for ftype, item in state.inventory.items():
        c.execute("INSERT OR REPLACE INTO inventory VALUES (?,?,?,?)",
                  (ftype.value, item.stock, item.freshness, state.day))
    conn.commit()


def export_orders_csv(state, path="data/orders.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["单号", "客户", "VIP", "花材", "金额", "成本", "状态", "备注"])
        for o in state.orders.values():
            items_str = ";".join(f"{k.value}x{v}" for k, v in o.items.items())
            w.writerow([o.order_id, o.customer.name, o.customer.vip_level,
                        items_str, o.total_price, o.cost, o.status.value, o.note])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--db", default="data/shop.db")
    parser.add_argument("--no-dashboard", action="store_true")
    args = parser.parse_args()

    logger = setup_logger("data")
    logger.info("=" * 50)
    logger.info("花店多 Agent 协作运营模拟系统 v2.0")
    logger.info("=" * 50)

    random.seed(args.seed)
    bus = MessageBus()
    state = ShopState()

    sales = SalesAgent(bus, state)
    ShopManagerAgent(bus, state)
    InventoryAgent(bus, state)
    PurchasingAgent(bus, state)
    FloristAgent(bus, state)
    DeliveryAgent(bus, state)
    MarketingAgent(bus, state)
    logger.info("7 个 Agent 已上线，开始模拟 %d 天", args.days)

    for day in range(1, args.days + 1):
        state.day = day
        simulate_one_day(sales, day)
        bus.publish(Message(EventType.DAILY_REPORT_REQUEST, "system", {"day": day}))

    # 持久化
    conn = init_db(args.db)
    save_to_db(conn, state)
    conn.close()
    export_orders_csv(state)
    logger.info(f"订单流水：data/orders.csv")
    logger.info(f"SQLite 库：{args.db}")
    logger.info(f"日志文件：data/simulation.log")

    if not args.no_dashboard:
        from visualization.generate_dashboard import generate_dashboard
        path = generate_dashboard(state, "data/dashboard.html")
        logger.info(f"可视化仪表盘：{path}")

    logger.info("模拟结束。")


if __name__ == "__main__":
    main()
