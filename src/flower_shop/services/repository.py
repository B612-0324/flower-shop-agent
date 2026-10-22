"""SQLite 运行隔离仓储；旧表保留，新数据使用版本化表。"""
import json
import sqlite3
from pathlib import Path
from uuid import uuid4
from contextlib import contextmanager


class OrderRepository:
    def __init__(self, db_path="data/shop.db", run_id=None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or uuid4().hex
        with self._conn() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    run_id TEXT PRIMARY KEY, seed INTEGER, days INTEGER);
                CREATE TABLE IF NOT EXISTS run_orders (
                    run_id TEXT, order_id TEXT, day INTEGER, customer TEXT,
                    vip_level INTEGER, items_json TEXT, total_price REAL,
                    cost REAL, status TEXT, refuse_reason TEXT, note TEXT,
                    PRIMARY KEY(run_id, order_id));
                CREATE TABLE IF NOT EXISTS run_inventory (
                    run_id TEXT, day INTEGER, flower TEXT, stock INTEGER,
                    freshness INTEGER, batches_json TEXT,
                    PRIMARY KEY(run_id, day, flower));
                CREATE TABLE IF NOT EXISTS run_daily (
                    run_id TEXT, day INTEGER, metrics_json TEXT,
                    PRIMARY KEY(run_id, day));
                CREATE TABLE IF NOT EXISTS run_timeline (
                    run_id TEXT, seq INTEGER, day INTEGER, order_id TEXT,
                    agent TEXT, action TEXT, PRIMARY KEY(run_id, seq));
            ''')

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def start_run(self, seed, days):
        with self._conn() as conn:
            conn.execute("INSERT INTO simulation_runs VALUES (?,?,?)",
                         (self.run_id, seed, days))

    def save_order(self, order):
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO run_orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (self.run_id, order.order_id, order.day, order.customer.name,
                          order.customer.vip_level,
                          json.dumps({k.value: v for k, v in order.items.items()}),
                          order.total_price, order.cost, order.status.value,
                          order.refuse_reason, order.note))

    def save_snapshot(self, day, inventory):
        with self._conn() as conn:
            for flower, item in inventory.items():
                conn.execute("INSERT OR REPLACE INTO run_inventory VALUES (?,?,?,?,?,?)",
                             (self.run_id, day, flower.value, item.stock,
                              item.freshness, json.dumps(item.batches)))

    def save_daily(self, state, metrics):
        self.save_snapshot(state.day, state.inventory)
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO run_daily VALUES (?,?,?)",
                         (self.run_id, state.day, json.dumps(metrics, ensure_ascii=False)))
            conn.executemany("INSERT OR REPLACE INTO run_timeline VALUES (?,?,?,?,?,?)",
                             [(self.run_id, e['seq'], e['day'], e['order_id'],
                               e['agent'], e['action']) for e in state.timeline])

    def list_orders(self):
        with self._conn() as conn:
            return conn.execute("SELECT * FROM run_orders WHERE run_id=? ORDER BY order_id",
                                (self.run_id,)).fetchall()
