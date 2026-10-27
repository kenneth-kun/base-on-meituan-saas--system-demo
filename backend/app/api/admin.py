"""管理后台：套餐 / 商家 / 商家账号 / 订阅管理（仅平台管理员）。"""
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import (Merchant, MerchantUser, Plan, Platform, Store, Subscription)
from ..models.management import FEATURES
from ..services.auth import hash_password

router = APIRouter()


def _plan_dict(p: Plan) -> dict:
    return {"id": p.id, "name": p.name, "price": str(p.price), "status": p.status,
            "features": p.features, "quotas": p.quotas, "description": p.description}


# ---------- 功能点 ----------
@router.get("/admin/features")
def list_features(_admin: dict = Depends(require_admin)):
    return {"items": FEATURES}


# ---------- 套餐 ----------
@router.get("/admin/plans")
def list_plans(_admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    plans = db.scalars(select(Plan).order_by(Plan.id)).all()
    return {"items": [_plan_dict(p) for p in plans]}


@router.post("/admin/plans")
def create_plan(payload: dict, _admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    plan = Plan(
        name=payload.get("name") or "未命名套餐",
        price=Decimal(str(payload.get("price") or 0)),
        features=payload.get("features") or [],
        quotas=payload.get("quotas") or {},
        description=payload.get("description"),
        status=payload.get("status") or "active",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_dict(plan)


@router.put("/admin/plans/{plan_id}")
def update_plan(plan_id: int, payload: dict, _admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "套餐不存在")
    if "name" in payload:
        plan.name = payload["name"]
    if "price" in payload:
        plan.price = Decimal(str(payload["price"]))
    if "features" in payload:
        plan.features = payload["features"]
    if "quotas" in payload:
        plan.quotas = payload["quotas"]
    if "description" in payload:
        plan.description = payload["description"]
    if "status" in payload:
        plan.status = payload["status"]
    db.commit()
    db.refresh(plan)
    return _plan_dict(plan)


@router.delete("/admin/plans/{plan_id}")
def delete_plan(plan_id: int, _admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "套餐不存在")
    db.delete(plan)
    db.commit()
    return {"ok": True}


# ---------- 商家 ----------
def _merchant_dict(m: Merchant, db: Session) -> dict:
    sub = db.scalar(select(Subscription).where(Subscription.merchant_id == m.id)
                    .order_by(Subscription.id.desc()).limit(1))
    plan = db.get(Plan, sub.plan_id) if sub else None
    user = db.scalar(select(MerchantUser).where(MerchantUser.merchant_id == m.id).limit(1))
    return {"id": m.id, "name": m.name, "phone": m.phone,
            "plan_name": plan.name if plan else None,
            "sub_status": sub.status if sub else None,
            "expired_at": sub.expired_at.isoformat() if sub else None,
            "username": user.username if user else None,
            "user_status": user.status if user else None}


@router.get("/admin/merchants")
def list_merchants(_admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    merchants = db.scalars(select(Merchant).order_by(Merchant.id)).all()
    return {"items": [_merchant_dict(m, db) for m in merchants]}


@router.post("/admin/merchants")
def create_merchant(payload: dict, _admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    name = payload.get("name")
    username = payload.get("username")
    if not name:
        raise HTTPException(400, "商家名不能为空")
    if not username:
        raise HTTPException(400, "登录账号不能为空")
    if db.scalar(select(MerchantUser).where(MerchantUser.username == username)):
        raise HTTPException(400, "登录账号已存在")

    platform = db.scalar(select(Platform).where(Platform.code == "meituan"))
    if platform is None:
        raise HTTPException(500, "平台数据缺失，请先运行 seed_mock_data")

    merchant = Merchant(name=name, phone=payload.get("phone"))
    db.add(merchant)
    db.flush()
    db.add(Store(merchant_id=merchant.id, platform_id=platform.id,
                 name=payload.get("store_name") or name, phone=payload.get("phone")))
    db.add(MerchantUser(merchant_id=merchant.id, username=username,
                        password_hash=hash_password(payload.get("password") or "123456")))

    plan_id = payload.get("plan_id")
    if plan_id and db.get(Plan, plan_id):
        db.add(Subscription(merchant_id=merchant.id, plan_id=plan_id,
                            started_at=date.today(),
                            expired_at=date.fromisoformat(payload.get("expired_at") or "2099-12-31")))
    db.commit()
    return {"id": merchant.id, "name": merchant.name, "username": username}


@router.put("/admin/merchants/{merchant_id}/status")
def set_merchant_status(merchant_id: int, payload: dict, _admin: dict = Depends(require_admin),
                        db: Session = Depends(get_db)):
    status = payload.get("status")
    if status not in ("active", "disabled"):
        raise HTTPException(400, "status 需为 active 或 disabled")
    users = db.scalars(select(MerchantUser).where(MerchantUser.merchant_id == merchant_id)).all()
    for u in users:
        u.status = status
    db.commit()
    return {"ok": True, "status": status}


# ---------- 商家账号 ----------
@router.get("/admin/merchant-users")
def list_merchant_users(_admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(MerchantUser).order_by(MerchantUser.id)).all()
    return {"items": [{"id": u.id, "merchant_id": u.merchant_id,
                       "username": u.username, "status": u.status} for u in users]}


@router.post("/admin/merchant-users")
def create_merchant_user(payload: dict, _admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    merchant_id = payload.get("merchant_id")
    username = payload.get("username")
    if not merchant_id or not db.get(Merchant, merchant_id):
        raise HTTPException(400, "商家不存在")
    if not username:
        raise HTTPException(400, "账号不能为空")
    if db.scalar(select(MerchantUser).where(MerchantUser.username == username)):
        raise HTTPException(400, "账号已存在")
    u = MerchantUser(merchant_id=merchant_id, username=username,
                     password_hash=hash_password(payload.get("password") or "123456"))
    db.add(u)
    db.commit()
    return {"id": u.id, "merchant_id": u.merchant_id, "username": u.username}


# ---------- 订阅 ----------
@router.get("/admin/subscriptions")
def list_subscriptions(_admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    subs = db.scalars(select(Subscription).order_by(Subscription.id.desc())).all()
    items = []
    for s in subs:
        plan = db.get(Plan, s.plan_id)
        merchant = db.get(Merchant, s.merchant_id)
        items.append({"id": s.id, "merchant_id": s.merchant_id,
                      "merchant_name": merchant.name if merchant else None,
                      "plan_id": s.plan_id, "plan_name": plan.name if plan else None,
                      "started_at": s.started_at.isoformat(),
                      "expired_at": s.expired_at.isoformat(), "status": s.status})
    return {"items": items}


@router.post("/admin/subscriptions")
def assign_subscription(payload: dict, _admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    merchant_id = payload.get("merchant_id")
    plan_id = payload.get("plan_id")
    if not db.get(Merchant, merchant_id):
        raise HTTPException(400, "商家不存在")
    if not db.get(Plan, plan_id):
        raise HTTPException(400, "套餐不存在")
    s = Subscription(merchant_id=merchant_id, plan_id=plan_id, started_at=date.today(),
                     expired_at=date.fromisoformat(payload.get("expired_at") or "2099-12-31"))
    db.add(s)
    db.commit()
    return {"id": s.id, "merchant_id": s.merchant_id, "plan_id": s.plan_id}
