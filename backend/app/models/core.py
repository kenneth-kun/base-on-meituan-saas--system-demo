"""主数据：平台、商家、门店、分类、商品、顾客。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import ProductStatus


class Platform(Base):
    __tablename__ = "platform"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(50))


class Merchant(Base, TimestampMixin):
    __tablename__ = "merchant"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))

    stores: Mapped[list["Store"]] = relationship(back_populates="merchant")


class Store(Base, TimestampMixin):
    __tablename__ = "store"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchant.id"))
    platform_id: Mapped[int] = mapped_column(ForeignKey("platform.id"))
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(200))
    business_hours: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    settings: Mapped[dict] = mapped_column(JSON, default=dict)  # 商家端设置

    merchant: Mapped["Merchant"] = relationship(back_populates="stores")
    platform: Mapped["Platform"] = relationship()


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"))
    name: Mapped[str] = mapped_column(String(50))
    sort: Mapped[int] = mapped_column(Integer, default=0)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base, TimestampMixin):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    name: Mapped[str] = mapped_column(String(100))
    app_food_code: Mapped[str | None] = mapped_column(String(50))  # 商品编码（美团 app_food_code）
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(10), default=ProductStatus.on.value)
    sales: Mapped[int] = mapped_column(Integer, default=0)

    category: Mapped["Category"] = relationship(back_populates="products")


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"))
    phone_hash: Mapped[str] = mapped_column(String(64), index=True)
    first_order_at: Mapped[datetime] = mapped_column(DateTime)
