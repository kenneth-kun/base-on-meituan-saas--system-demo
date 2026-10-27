"""初始化管理系统数据：默认管理员、套餐、商家账号、订阅。

用法（在 backend 目录下）:
    python -m scripts.seed_admin
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.models import AdminUser, Merchant, MerchantUser, Plan, Subscription
from app.services.auth import hash_password

DEFAULT_PLANS = [
    {"name": "免费试用", "price": 0,
     "features": ["dashboard", "orders", "products", "reviews"],
     "quotas": {"ai_calls_monthly": 0}, "description": "基础功能，不含 AI"},
    {"name": "基础版", "price": 99,
     "features": ["dashboard", "orders", "products", "reviews", "alerts", "service"],
     "quotas": {"ai_calls_monthly": 500}, "description": "含 AI 客服，500 次/月"},
    {"name": "高级版", "price": 299,
     "features": ["dashboard", "orders", "products", "reviews", "alerts", "service", "settings"],
     "quotas": {"ai_calls_monthly": 3000}, "description": "全部功能，3000 次/月"},
]


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        # 管理员（已存在则跳过）
        if not db.scalar(select(AdminUser).where(AdminUser.username == "admin")):
            db.add(AdminUser(username="admin", password_hash=hash_password("admin123")))

        # 套餐（按名去重）
        existing = {p.name for p in db.scalars(select(Plan)).all()}
        for p in DEFAULT_PLANS:
            if p["name"] not in existing:
                db.add(Plan(name=p["name"], price=p["price"], features=p["features"],
                            quotas=p["quotas"], description=p["description"]))
        db.flush()

        # 给已有商家建账号 + 订阅基础版
        merchant = db.scalar(select(Merchant).order_by(Merchant.id).limit(1))
        if merchant:
            if not db.scalar(select(MerchantUser).where(MerchantUser.merchant_id == merchant.id)):
                db.add(MerchantUser(merchant_id=merchant.id, username="merchant1",
                                    password_hash=hash_password("123456")))
            if not db.scalar(select(Subscription).where(Subscription.merchant_id == merchant.id)):
                base = db.scalar(select(Plan).where(Plan.name == "基础版"))
                if base:
                    db.add(Subscription(merchant_id=merchant.id, plan_id=base.id,
                                        started_at=date.today(),
                                        expired_at=date.today() + timedelta(days=365)))

        db.commit()
        print("✅ 管理系统数据已初始化")
        print("   管理员: admin / admin123")
        print("   商家账号: merchant1 / 123456")
        print("   套餐:", [p.name for p in db.scalars(select(Plan)).all()])
    finally:
        db.close()


if __name__ == "__main__":
    seed()
