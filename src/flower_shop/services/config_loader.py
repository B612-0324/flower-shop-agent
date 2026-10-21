"""配置加载：从 JSON 文件读入 ShopConfig。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from ..core.enums import FlowerType
from ..core.exceptions import InvalidConfigError
from ..core.models import FlowerItem, ShopConfig


def load_config(path: str | Path) -> ShopConfig:
    p = Path(path)
    if not p.exists():
        raise InvalidConfigError(f"配置文件不存在: {p}")
    raw = json.loads(p.read_text(encoding="utf-8"))

    inv: Dict[FlowerType, FlowerItem] = {}
    for key, item in raw["inventory"].items():
        try:
            ftype = FlowerType(key)
        except ValueError as exc:
            raise InvalidConfigError(f"未知花材品类: {key}") from exc
        inv[ftype] = FlowerItem(
            ftype=ftype,
            unit_price=float(item["unit_price"]),
            cost_price=float(item["cost_price"]),
            stock=int(item["stock"]),
            safety_stock=int(item["safety_stock"]),
            shelf_life=int(item.get("shelf_life", 5)),
        )

    return ShopConfig(
        initial_cash=float(raw["initial_cash"]),
        reserve_cash=float(raw["reserve_cash"]),
        package_fee=float(raw["package_fee"]),
        delivery_fee=float(raw["delivery_fee"]),
        urgent_surcharge=float(raw["urgent_surcharge"]),
        max_auto_price=float(raw["max_auto_price"]),
        vip_discount={int(k): float(v) for k, v in raw["vip_discount"].items()},
        inventory=inv,
    )
