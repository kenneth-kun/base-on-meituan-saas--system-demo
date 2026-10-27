"""PlatformAdapter —— 平台无关的统一接口。

业务层只依赖这里的接口和数据结构，不碰具体平台 API。
未来接饿了么/抖音，只需新增一个 adapter 实现。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass
class OrderItemData:
    product_name: str
    qty: int
    unit_price: Decimal


@dataclass
class ReviewData:
    rating: int
    content: str
    tags: list[str]
    created_at: datetime
    accurate_star: float = 0.0
    consume_amount: Decimal = Decimal("0")


@dataclass
class OrderData:
    order_no: str
    customer_phone: str
    wm_order_id_view: str
    status: str
    total_amount: Decimal
    commission: Decimal
    subsidy: Decimal
    delivery_fee: Decimal
    placed_at: datetime
    is_valid: bool = True
    items: list[OrderItemData] = field(default_factory=list)
    review: ReviewData | None = None
    recipient_name: str = ""
    recipient_phone: str = ""
    recipient_address: str = ""
    original_price: Decimal = Decimal("0")


@dataclass
class ProductData:
    name: str
    category: str
    price: Decimal
    stock: int
    status: str
    sales: int = 0
    app_food_code: str = ""


@dataclass
class DailyMetricData:
    date: date
    revenue: Decimal
    order_count: int
    valid_order_count: int
    new_customer_count: int
    return_customer_count: int
    exposure: int
    visits: int
    orders_funnel: int


@dataclass
class MessageData:
    customer_phone: str
    content: str
    order_no: str | None
    created_at: datetime
    msg_id: str = ""
    scene_tag: str = ""
    open_user_id: str = ""


class PlatformAdapter(ABC):
    """平台无关的统一接口，业务层只依赖它。"""

    @abstractmethod
    def fetch_products(self, store_id):
        """拉取商品。"""

    @abstractmethod
    def fetch_orders(self, store_id, since: datetime, until: datetime) -> list[OrderData]:
        """拉取订单（含明细、评价）。"""

    @abstractmethod
    def fetch_reviews(self, store_id, since: datetime, until: datetime) -> list[ReviewData]:
        """拉取评价。"""

    @abstractmethod
    def fetch_daily_metrics(self, store_id, since: date, until: date) -> list[DailyMetricData]:
        """拉取营业日报（预聚合）。"""

    @abstractmethod
    def receive_messages(self, store_id) -> list[MessageData]:
        """接收顾客 IM 消息。"""

    @abstractmethod
    def send_reply(self, message_id, content: str) -> None:
        """发送回复。"""

    @abstractmethod
    def update_product_price(self, product_id, price: Decimal) -> None:
        """改价。"""

    @abstractmethod
    def set_product_status(self, product_id, status: str) -> None:
        """上下架。"""
