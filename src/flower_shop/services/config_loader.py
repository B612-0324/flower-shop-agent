"""外置配置加载与边界校验。"""
import json
import math
from pathlib import Path
from ..core.enums import FlowerType
from ..core.exceptions import InvalidConfigError
from ..core.models import FlowerItem, ShopConfig


def load_config(path=None):
    path = Path(path) if path else Path(__file__).parent.parent / 'default_config.json'
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
        def number(value, integer=False, minimum=0):
            if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
                raise ValueError('配置数值无效')
            if integer and type(value) is not int:
                raise ValueError('数量和保鲜期必须为整数')
            return value
        inventory = {}
        for key, item in raw['inventory'].items():
            flower = FlowerType(key)
            inventory[flower] = FlowerItem(
                flower, number(item['unit_price']), number(item['cost_price']),
                number(item['stock'], True), number(item['safety_stock'], True),
                number(item.get('shelf_life', 5), True, 1))
        if not inventory:
            raise ValueError('库存品类不可为空')
        discounts = {int(k): number(v) for k, v in raw['vip_discount'].items()}
        repeat = {int(k): number(v) for k, v in raw.get('vip_repeat_prob',
                  {'0': .05, '1': .2, '2': .35}).items()}
        if set(discounts) != {0, 1, 2} or set(repeat) != {0, 1, 2}:
            raise ValueError('VIP配置必须包含0/1/2')
        if any(v > 1 for v in list(discounts.values()) + list(repeat.values())):
            raise ValueError('折扣和概率必须在0到1之间')
        config = ShopConfig(**{key: number(raw[key]) for key in
                            ('initial_cash', 'reserve_cash', 'package_fee', 'delivery_fee',
                             'urgent_surcharge', 'max_auto_price')},
                            vip_discount=discounts, inventory=inventory, vip_repeat_prob=repeat)
        if config.reserve_cash > config.initial_cash:
            raise ValueError('初始现金不可低于周转金')
        return config
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise InvalidConfigError(f'配置加载失败：{path}：{exc}') from exc
