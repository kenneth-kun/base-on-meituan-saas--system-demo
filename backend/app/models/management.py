"""管理系统：平台管理员、商家账号、套餐、订阅、配额用量。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (JSON, Date, DateTime, ForeignKey, Integer, Numeric,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, now

# 功能点标准清单（模块级权限）
FEATURES = [
    {"code": "dashboard", "name": "经营看板"},
    {"code": "orders", "name": "订单管理"},
    {"code": "products", "name": "商品管理"},
    {"code": "reviews", "name": "评价管理"},
    {"code": "alerts", "name": "预警中心"},
    {"code": "service", "name": "客服工作台"},
    {"code": "settings", "name": "设置"},
]


class AdminUser(Base):
    __tablename__ = "admin_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class MerchantUser(Base):
    __tablename__ = "merchant_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchant.id"))
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    openid: Mapped[str | None] = mapped_column(String(100), unique=True)  # 微信 openid
    status: Mapped[str] = mapped_column(String(20), default="active")  # active / disabled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Plan(Base):
    __tablename__ = "plan"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    features: Mapped[list] = mapped_column(JSON, default=list)   # ["dashboard", "orders", ...]
    quotas: Mapped[dict] = mapped_column(JSON, default=dict)     # {"ai_calls_monthly": 500}
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchant.id"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plan.id"))
    started_at: Mapped[date] = mapped_column(Date)
    expired_at: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active / expired / cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class QuotaUsage(Base):
    __tablename__ = "quota_usage"
    __table_args__ = (UniqueConstraint("merchant_id", "quota_key", "period"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchant.id"))
    quota_key: Mapped[str] = mapped_column(String(50))  # e.g. "ai_calls_monthly"
    period: Mapped[str] = mapped_column(String(7))      # "2026-09"
    used_count: Mapped[int] = mapped_column(Integer, default=0)
