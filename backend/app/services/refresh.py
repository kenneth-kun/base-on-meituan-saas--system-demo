"""定时刷新：周期性从平台拉取新数据并写入数据库。"""
import hashlib
import random
import threading
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..adapters.mock import MockAdapter
from ..database import SessionLocal
from ..models import (Customer, DailyMetric, Order, OrderItem, Product, Review, Store)

_lock = threading.Lock()
_last_refresh_at: datetime | None = None


def _phone_hash(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()[:16]


def get_last_refresh_at() -> datetime | None:
    return _last_refresh_at


def _refresh_store(db: Session, store: Store, adapter: MockAdapter) -> tuple[int, int]:
    """刷新单个门店：拉取新订单/评价并写库，返回 (新增订单数, 新增评价数)。"""
    recent = adapter.generate_recent(n=random.randint(3, 8))

    product_map = {p.name: p for p in db.scalars(
        select(Product).where(Product.store_id == store.id)).all()}

    new_orders = 0
    new_reviews = 0
    for o in recent:
        cust = db.scalar(select(Customer).where(
            Customer.store_id == store.id,
            Customer.phone_hash == _phone_hash(o.customer_phone)))
        if cust is None:
            cust = Customer(store_id=store.id, phone_hash=_phone_hash(o.customer_phone),
                            first_order_at=o.placed_at)
            db.add(cust)
            db.flush()

        items = []
        for it in o.items:
            p = product_map.get(it.product_name)
            if p is None:
                continue
            items.append(OrderItem(product_id=p.id, qty=it.qty, unit_price=it.unit_price))
            p.sales += it.qty

        order = Order(store_id=store.id, customer_id=cust.id, order_no=o.order_no,
                      wm_order_id_view=o.wm_order_id_view, status=o.status,
                      total_amount=o.total_amount, commission=o.commission,
                      subsidy=o.subsidy, delivery_fee=o.delivery_fee,
                      original_price=o.original_price,
                      recipient_name=o.recipient_name, recipient_phone=o.recipient_phone,
                      recipient_address=o.recipient_address,
                      placed_at=o.placed_at, is_valid=o.is_valid, items=items)
        if o.review is not None:
            order.review = Review(store_id=store.id, rating=o.review.rating,
                                  accurate_star=o.review.accurate_star,
                                  consume_amount=o.review.consume_amount,
                                  content=o.review.content, tags=",".join(o.review.tags),
                                  created_at=o.review.created_at)
            new_reviews += 1
        db.add(order)
        new_orders += 1

    # 重新聚合今天的营业日报
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    valid_row = db.execute(select(
        func.coalesce(func.sum(Order.total_amount), 0),
        func.count(Order.id),
    ).where(Order.store_id == store.id, Order.placed_at >= start,
            Order.is_valid.is_(True))).one()
    total_count = db.scalar(select(func.count(Order.id)).where(
        Order.store_id == store.id, Order.placed_at >= start)) or 0

    dm = db.scalar(select(DailyMetric).where(
        DailyMetric.store_id == store.id, DailyMetric.date == today))
    if dm is None:
        dm = DailyMetric(store_id=store.id, date=today)
        db.add(dm)
    dm.revenue = valid_row[0] or 0
    dm.order_count = total_count
    dm.valid_order_count = valid_row[1]

    return new_orders, new_reviews


def refresh_data() -> dict:
    """拉取一批新订单/评价并写入数据库，返回本次刷新统计。"""
    global _last_refresh_at
    with _lock:
        db = SessionLocal()
        try:
            stores = db.scalars(select(Store).order_by(Store.id)).all()
            if not stores:
                return {"orders": 0, "reviews": 0, "last_refresh_at": None}

            # 模拟从美团平台拉取最近的新订单（同一 adapter 复用到所有门店）
            adapter = MockAdapter(seed=random.randint(1, 10 ** 9))
            total_orders = 0
            total_reviews = 0
            for store in stores:
                new_orders, new_reviews = _refresh_store(db, store, adapter)
                total_orders += new_orders
                total_reviews += new_reviews

            db.commit()
            _last_refresh_at = datetime.now()
            return {"orders": total_orders, "reviews": total_reviews,
                    "last_refresh_at": _last_refresh_at.isoformat()}
        finally:
            db.close()
