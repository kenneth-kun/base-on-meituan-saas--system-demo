"""交易与派生数据：订单、订单明细、评价、营业日报。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (Date, DateTime, Float, ForeignKey, Integer, Numeric,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, now
from .enums import OrderStatus


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id"))
    order_no: Mapped[str] = mapped_column(String(40), unique=True)
    wm_order_id_view: Mapped[str | None] = mapped_column(String(30))  # 美团订单展示号
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.completed.value)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    subsidy: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    original_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    recipient_name: Mapped[str | None] = mapped_column(String(50))
    recipient_phone: Mapped[str | None] = mapped_column(String(20))
    recipient_address: Mapped[str | None] = mapped_column(String(200))
    placed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    is_valid: Mapped[bool] = mapped_column(default=True)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
    review: Mapped["Review"] = relationship(back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    qty: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), unique=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)  # 1-5 星
    accurate_star: Mapped[float | None] = mapped_column(Float)  # 精确星级 4.5
    consume_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # 消费金额
    content: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)  # 逗号分隔
    reply: Mapped[str | None] = mapped_column(Text)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    order: Mapped["Order"] = relationship(back_populates="review")


class DailyMetric(Base):
    __tablename__ = "daily_metric"
    __table_args__ = (UniqueConstraint("store_id", "date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    order_count: Mapped[int] = mapped_column(Integer, default=0)
    valid_order_count: Mapped[int] = mapped_column(Integer, default=0)
    new_customer_count: Mapped[int] = mapped_column(Integer, default=0)
    return_customer_count: Mapped[int] = mapped_column(Integer, default=0)
    exposure: Mapped[int] = mapped_column(Integer, default=0)
    visits: Mapped[int] = mapped_column(Integer, default=0)
    orders_funnel: Mapped[int] = mapped_column(Integer, default=0)
