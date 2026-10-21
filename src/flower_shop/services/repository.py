"""SQLite 持久化：订单流水、库存快照。"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from ..core.enums import FlowerType, OrderStatus
from ..core.models import Order


class OrderRepository:
    def __init__(self, db_path: str | Path = "data/shop.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id      TEXT PRIMARY KEY,
                    day           INTEGER NOT NULL,
                    customer      TEXT NOT NULL,
                    vip_level     INTEGER NOT NULL,
                    items_json    TEXT NOT NULL,
                    total_price   REAL NOT NULL,
                    cost          REAL NOT NULL,
                    status        TEXT NOT NULL,
                    refuse_reason TEXT DEFAULT '',
                    note          TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS inventory_snapshot (
                    day        INTEGER NOT NULL,
                    flower     TEXT NOT NULL,
                    stock      INTEGER NOT NULL,
                    freshness  INTEGER NOT NULL,
                    PRIMARY KEY (day, flower)
                );
                """
            )

    def save_order(self, order: Order) -> None:
        items = ";".join(f"{k.value}:{v}" for k, v in order.items.items())
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO orders
                   (order_id, day, customer, vip_level, items_json,
                    total_price, cost, status, refuse_reason, note)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    order.order_id, order.day, order.customer.name,
                    order.customer.vip_level, items,
                    order.total_price, order.cost,
                    order.status.value, order.refuse_reason, order.note,
                ),
            )

    def save_snapshot(self, day: int, inventory: dict) -> None:
        with self._conn() as conn:
            for ftype, item in inventory.items():
                conn.execute(
                    """INSERT OR REPLACE INTO inventory_snapshot
                       (day, flower, stock, freshness) VALUES (?, ?, ?, ?)""",
                    (day, ftype.value, item.stock, item.freshness),
                )

    def list_orders(self) -> Iterable[sqlite3.Row]:
        with self._conn() as conn:
            return conn.execute("SELECT * FROM orders ORDER BY order_id").fetchall()
