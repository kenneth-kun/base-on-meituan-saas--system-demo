"""MockAdapter —— 用仿真数据实现 PlatformAdapter。

真实接入美团后，用 MeituanAdapter 替换它，业务层无感知。
"""
from __future__ import annotations

import random
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from faker import Faker

from .base import (DailyMetricData, MessageData, OrderData, OrderItemData,
                   PlatformAdapter, ProductData, ReviewData)

# 分类与菜品（共 40 个）
CATEGORIES = ["主食", "小吃", "饮品", "烧烤", "甜品", "汤品"]

MENU: dict[str, list[str]] = {
    "主食": ["招牌炒饭", "牛肉面", "鸡腿饭", "番茄鸡蛋面", "扬州炒饭", "卤肉饭", "水饺", "担担面", "肉夹馍"],
    "小吃": ["炸鸡块", "薯条", "春卷", "盐酥鸡", "烤肠", "花生米"],
    "饮品": ["冰可乐", "柠檬茶", "酸梅汤", "豆浆", "奶茶", "矿泉水"],
    "烧烤": ["烤羊肉串", "烤鸡翅", "烤韭菜", "烤茄子", "烤玉米", "烤面筋"],
    "甜品": ["红豆沙", "绿豆汤", "双皮奶", "芒果布丁", "糖水", "芝麻糊", "杨枝甘露"],
    "汤品": ["紫菜蛋花汤", "西红柿蛋汤", "玉米排骨汤", "冬瓜汤", "酸辣汤", "罗宋汤"],
}

PRICE_RANGE: dict[str, tuple[int, int]] = {
    "主食": (18, 35),
    "小吃": (8, 20),
    "饮品": (5, 15),
    "烧烤": (3, 12),
    "甜品": (6, 15),
    "汤品": (8, 18),
}

REVIEW_CONTENT: dict[int, list[str]] = {
    5: ["味道很好，下次还点！", "分量足，包装也好", "配送很快，好吃！", "推荐，很满意"],
    4: ["味道不错，就是稍微有点慢", "整体满意", "好吃，会回购"],
    3: ["一般般吧", "味道还可以，分量有点少", "中规中矩"],
    2: ["有点失望，味道一般", "包装漏了", "偏咸了"],
    1: ["太差了，量少还难吃", "不新鲜", "送错餐了，很生气"],
}

POSITIVE_TAGS = ["味道好", "分量足", "包装好", "配送快"]
NEGATIVE_TAGS = ["分量少", "太咸", "太辣", "不新鲜"]

# 顾客 IM 消息样本（按意图 + 美团场景标签 scene_tag）
MESSAGE_SAMPLES = [
    ("商品咨询", "你们家牛肉面辣吗？", "商品咨询"),
    ("商品咨询", "有没有不辣的菜推荐一下", "商品咨询"),
    ("营业信息", "你们几点关门啊？", "营业时间"),
    ("营业信息", "能开发票吗？", "发票"),
    ("催单", "我的单好了没，等好久了", "催单"),
    ("催单", "还要多久能送到？", "催单"),
    ("售后", "少送了一份鸡翅，麻烦处理下", "少送"),
    ("售后", "菜有点凉了，不满意", "售后"),
    ("改地址", "麻烦帮我加双筷子", "改地址"),
    ("闲聊", "谢谢老板，好评了！", "闲聊"),
]

# 小时分布权重（0-23），午餐/晚餐双高峰
HOUR_WEIGHTS = [1, 1, 1, 1, 1, 1, 2, 3, 4, 5, 8, 15, 20, 18, 6, 5, 5, 16, 20, 18, 10, 6, 3, 2]


class MockAdapter(PlatformAdapter):
    """生成 90 天仿真经营数据（含刻意注入的异常，用于测试预警）。"""

    def __init__(self, seed: int | None = 42):
        self._rng = random.Random(seed)
        self._faker = Faker("zh_CN")
        if seed is not None:
            Faker.seed(seed)
        self.categories = CATEGORIES
        self._dataset: dict | None = None

    # ---------- 对外统一入口 ----------

    def init_products(self) -> None:
        """初始化商品名/价格映射（轻量，供增量生成复用）。"""
        if not hasattr(self, "_all_product_names"):
            products = self._gen_products()
            self._all_product_names = [p.name for p in products]
            self._price_map = {p.name: p.price for p in products}
            self._products = products

    def generate_dataset(self, days: int = 90) -> dict:
        """生成完整数据集，返回 products/orders/daily_metrics/messages。"""
        if self._dataset is not None:
            return self._dataset

        self.init_products()

        orders, customer_phones = self._gen_orders(days)
        daily_metrics = self._gen_daily_metrics(orders)
        # 顾客 → 最新美团订单号（IM 消息关联订单）
        latest_order = {}
        for o in orders:
            latest_order[o.customer_phone] = o.wm_order_id_view
        messages = self._gen_messages(customer_phones, latest_order)

        self._dataset = {
            "products": self._products,
            "orders": orders,
            "daily_metrics": daily_metrics,
            "messages": messages,
        }
        return self._dataset

    # ---------- 生成器 ----------

    def _phone(self) -> str:
        second = self._rng.choice("35789")
        rest = "".join(self._rng.choices("0123456789", k=9))
        return "1" + second + rest

    def _gen_products(self) -> list[ProductData]:
        products = []
        seq = 0
        for cat in CATEGORIES:
            low, high = PRICE_RANGE[cat]
            for name in MENU[cat]:
                seq += 1
                price = Decimal(self._rng.randint(low * 2, high * 2)) / 2  # 精确到 0.5 元
                stock = self._rng.randint(20, 150)
                products.append(ProductData(name=name, category=cat, price=price,
                                            stock=stock, status="on",
                                            app_food_code=f"SP{seq:03d}"))
        return products

    def _gen_review(self, placed_at: datetime, consume_amount: Decimal = Decimal("0")) -> ReviewData:
        r = self._rng.random()
        if r < 0.02:
            rating = 1
        elif r < 0.05:
            rating = 2
        elif r < 0.13:
            rating = 3
        elif r < 0.35:
            rating = 4
        else:
            rating = 5
        content = self._rng.choice(REVIEW_CONTENT[rating])
        # 标签与评分关联：好评正标签、差评负标签、中评混合
        if rating >= 4:
            tag_pool = POSITIVE_TAGS
        elif rating <= 2:
            tag_pool = NEGATIVE_TAGS
        else:
            tag_pool = POSITIVE_TAGS + NEGATIVE_TAGS
        tags = self._rng.sample(tag_pool, k=self._rng.randint(1, 3))
        accurate_star = min(5.0, rating + self._rng.choice([0.0, 0.5]))
        return ReviewData(rating=rating, content=content, tags=tags,
                          created_at=placed_at + timedelta(hours=2),
                          accurate_star=accurate_star, consume_amount=consume_amount)

    def _gen_orders(self, days: int) -> tuple[list[OrderData], list[str]]:
        """返回 (订单列表按时间升序, 去重顾客手机号列表)。"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        orders: list[OrderData] = []
        customer_phones: list[str] = []
        bad_reviews_injected = 0
        seq = 0

        for day_offset in range(days - 1, -1, -1):
            day = today - timedelta(days=day_offset)
            is_weekend = day.weekday() >= 5
            base = self._rng.randint(60, 180)
            target = int(base * (1.3 if is_weekend else 1.0))
            # 异常注入①：3 天前订单骤降
            if day_offset == 3:
                target = int(target * 0.4)

            for _ in range(target):
                hour = self._rng.choices(range(24), weights=HOUR_WEIGHTS, k=1)[0]
                placed_at = day + timedelta(hours=hour, minutes=self._rng.randint(0, 59))

                # 顾客：约 60% 新客，40% 回头客
                if customer_phones and self._rng.random() > 0.6:
                    phone = self._rng.choice(customer_phones)
                else:
                    phone = self._phone()
                    customer_phones.append(phone)

                n_items = self._rng.choices([1, 2, 3, 4], weights=[30, 40, 20, 10], k=1)[0]
                items = []
                for _ in range(n_items):
                    pname = self._rng.choice(self._all_product_names)
                    qty = self._rng.choices([1, 2, 3], weights=[70, 22, 8], k=1)[0]
                    items.append(OrderItemData(product_name=pname, qty=qty,
                                               unit_price=self._price_map[pname]))

                subtotal = sum(it.unit_price * it.qty for it in items)
                delivery_fee = Decimal(self._rng.randint(0, 5))
                subsidy = Decimal(self._rng.randint(0, 10))
                total = max(subtotal + delivery_fee - subsidy, Decimal("0"))
                commission = (total * Decimal("0.18")).quantize(Decimal("0.01"))
                original_price = total + subsidy  # 原价 = 实付 + 优惠补贴
                recipient_name = self._faker.name()
                recipient_phone = phone  # 收货人 = 下单顾客
                recipient_address = self._faker.address().replace("\n", " ")

                # 订单状态：历史订单绝大多数已完成；今天的订单含待接单/制作中/配送中
                roll = self._rng.random()
                if day_offset == 0:
                    if roll < 0.15:
                        status, is_valid = "pending", True
                    elif roll < 0.45:
                        status, is_valid = "confirmed", True
                    elif roll < 0.70:
                        status, is_valid = "delivering", True
                    elif roll < 0.95:
                        status, is_valid = "completed", True
                    else:
                        status, is_valid = "cancelled", False
                elif roll < 0.05:
                    status, is_valid = "cancelled", False
                elif roll < 0.07:
                    status, is_valid = "refunding", False
                else:
                    status, is_valid = "completed", True

                # 评价：约 30% 已完成订单产生
                review = None
                if status == "completed" and self._rng.random() < 0.30:
                    review = self._gen_review(placed_at, consume_amount=total)
                    # 异常注入②：昨天前 3 条评价强制 1 星（差评激增）
                    if day_offset == 1 and bad_reviews_injected < 3:
                        review = ReviewData(rating=1, content=self._rng.choice(REVIEW_CONTENT[1]),
                                            tags=["不新鲜"], created_at=placed_at + timedelta(hours=1))
                        bad_reviews_injected += 1

                seq += 1
                order_no = f"MT{day:%Y%m%d}{seq:06d}"
                wm_order_id_view = "10" + "".join(self._rng.choices("0123456789", k=17))
                orders.append(OrderData(order_no=order_no, customer_phone=phone,
                                        wm_order_id_view=wm_order_id_view, status=status,
                                        total_amount=total, commission=commission,
                                        subsidy=subsidy, delivery_fee=delivery_fee,
                                        placed_at=placed_at, is_valid=is_valid,
                                        items=items, review=review,
                                        recipient_name=recipient_name,
                                        recipient_phone=recipient_phone,
                                        recipient_address=recipient_address,
                                        original_price=original_price))

        orders.sort(key=lambda o: o.placed_at)
        return orders, customer_phones

    def _gen_daily_metrics(self, orders: list[OrderData]) -> list[DailyMetricData]:
        per_day: dict = defaultdict(lambda: {
            "revenue": Decimal("0"), "count": 0, "valid": 0,
            "new_phones": set(), "return_phones": set(),
        })
        seen: set = set()
        for o in orders:
            rec = per_day[o.placed_at.date()]
            rec["count"] += 1
            if o.is_valid:
                rec["valid"] += 1
                rec["revenue"] += o.total_amount
            if o.customer_phone not in seen:
                seen.add(o.customer_phone)
                rec["new_phones"].add(o.customer_phone)
            else:
                rec["return_phones"].add(o.customer_phone)

        metrics = []
        for d in sorted(per_day):
            rec = per_day[d]
            valid = rec["valid"]
            # 漏斗：下单转化率 ~11-13%，进店转化率 ~22-28%
            orders_funnel = valid
            visits = int(valid / self._rng.uniform(0.11, 0.13)) if valid else 0
            exposure = int(visits / self._rng.uniform(0.22, 0.28)) if visits else 0
            metrics.append(DailyMetricData(
                date=d, revenue=rec["revenue"], order_count=rec["count"],
                valid_order_count=valid, new_customer_count=len(rec["new_phones"]),
                return_customer_count=len(rec["return_phones"]),
                exposure=exposure, visits=visits, orders_funnel=orders_funnel,
            ))
        return metrics

    def _gen_messages(self, customer_phones: list[str], latest_order: dict) -> list[MessageData]:
        messages = []
        now = datetime.now()
        for _ in range(20):
            _intent, text, scene = self._rng.choice(MESSAGE_SAMPLES)
            phone = self._rng.choice(customer_phones) if customer_phones else self._phone()
            created_at = now - timedelta(minutes=self._rng.randint(10, 48 * 60))
            msg_id = "wm" + "".join(self._rng.choices("0123456789", k=18))
            open_user_id = "u" + "".join(self._rng.choices("0123456789", k=10))
            order_no = latest_order.get(phone)
            messages.append(MessageData(customer_phone=phone, content=text,
                                        order_no=order_no, created_at=created_at,
                                        msg_id=msg_id, scene_tag=scene,
                                        open_user_id=open_user_id))
        messages.sort(key=lambda m: m.created_at)
        return messages

    def generate_recent(self, n: int = 6) -> list[OrderData]:
        """生成 n 条最近的新订单（含评价），模拟实时数据刷新。"""
        self.init_products()
        now = datetime.now()
        orders: list[OrderData] = []
        for _ in range(n):
            placed_at = now - timedelta(minutes=self._rng.randint(1, 30))
            phone = self._phone()
            n_items = self._rng.choices([1, 2, 3], weights=[30, 45, 25], k=1)[0]
            items = []
            for _ in range(n_items):
                pname = self._rng.choice(self._all_product_names)
                qty = self._rng.choices([1, 2, 3], weights=[70, 22, 8], k=1)[0]
                items.append(OrderItemData(product_name=pname, qty=qty, unit_price=self._price_map[pname]))
            subtotal = sum(it.unit_price * it.qty for it in items)
            delivery_fee = Decimal(self._rng.randint(0, 5))
            subsidy = Decimal(self._rng.randint(0, 8))
            total = max(subtotal + delivery_fee - subsidy, Decimal("0"))
            commission = (total * Decimal("0.18")).quantize(Decimal("0.01"))
            roll = self._rng.random()
            if roll < 0.7:
                status = "completed"
            elif roll < 0.9:
                status = "delivering"
            else:
                status = "confirmed"
            review = None
            if status == "completed" and self._rng.random() < 0.35:
                review = self._gen_review(placed_at, consume_amount=total)
            orders.append(OrderData(
                order_no=f"MT{now:%Y%m%d%H%M%S}{self._rng.randint(1000, 9999)}",
                customer_phone=phone,
                wm_order_id_view="10" + "".join(self._rng.choices("0123456789", k=17)),
                status=status, total_amount=total, commission=commission,
                subsidy=subsidy, delivery_fee=delivery_fee, placed_at=placed_at,
                is_valid=True, items=items, review=review,
                recipient_name=self._faker.name(), recipient_phone=phone,
                recipient_address=self._faker.address().replace("\n", " "),
                original_price=total + subsidy,
            ))
        orders.sort(key=lambda o: o.placed_at)
        return orders

    # ---------- PlatformAdapter 接口实现 ----------

    def fetch_products(self, store_id):
        return self.generate_dataset()["products"]

    def fetch_orders(self, store_id, since: datetime, until: datetime) -> list[OrderData]:
        ds = self.generate_dataset()
        return [o for o in ds["orders"] if since <= o.placed_at <= until]

    def fetch_reviews(self, store_id, since: datetime, until: datetime) -> list[ReviewData]:
        ds = self.generate_dataset()
        return [o.review for o in ds["orders"]
                if o.review is not None and since <= o.review.created_at <= until]

    def fetch_daily_metrics(self, store_id, since, until) -> list[DailyMetricData]:
        ds = self.generate_dataset()
        return [m for m in ds["daily_metrics"] if since <= m.date <= until]

    def receive_messages(self, store_id) -> list[MessageData]:
        return self.generate_dataset()["messages"]

    def send_reply(self, message_id, content: str) -> None:
        # Mock：真实场景调用平台 API 发送回复，这里不落库
        return None

    def update_product_price(self, product_id, price: Decimal) -> None:
        return None

    def set_product_status(self, product_id, status: str) -> None:
        return None
