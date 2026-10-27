"""FastAPI 依赖：鉴权、身份识别、套餐权限。"""
from datetime import date

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import AdminUser, MerchantUser, Plan, Store, Subscription
from .services.auth import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> dict:
    """解析 JWT，返回 {user, type, id}。"""
    if creds is None:
        raise HTTPException(401, "未登录")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(401, "token 无效或已过期")

    user_type = payload.get("type")
    user_id = int(payload["sub"])
    if user_type == "admin":
        user = db.get(AdminUser, user_id)
    elif user_type == "merchant":
        user = db.get(MerchantUser, user_id)
    else:
        raise HTTPException(401, "无效的用户类型")

    if user is None:
        raise HTTPException(401, "用户不存在")
    return {"user": user, "type": user_type, "id": user_id}


def require_admin(current: dict = Depends(get_current_user)) -> dict:
    if current["type"] != "admin":
        raise HTTPException(403, "需要平台管理员权限")
    return current


def require_merchant(current: dict = Depends(get_current_user)) -> MerchantUser:
    if current["type"] != "merchant":
        raise HTTPException(403, "需要商家身份")
    return current["user"]


def get_current_store(
    user: MerchantUser = Depends(require_merchant),
    db: Session = Depends(get_db),
) -> Store:
    """当前商家的门店（现阶段一个商家一个门店）。"""
    store = db.scalar(select(Store).where(Store.merchant_id == user.merchant_id).limit(1))
    if store is None:
        raise HTTPException(404, "门店不存在")
    return store


def get_active_plan(
    user: MerchantUser = Depends(require_merchant),
    db: Session = Depends(get_db),
) -> Plan | None:
    """当前商家的有效订阅套餐；无有效订阅返回 None。"""
    sub = db.scalar(
        select(Subscription).where(Subscription.merchant_id == user.merchant_id)
        .order_by(Subscription.id.desc()).limit(1)
    )
    if sub is None or sub.status != "active" or sub.expired_at < date.today():
        return None
    return db.get(Plan, sub.plan_id)


def require_feature(code: str):
    """套餐功能校验依赖工厂：当前套餐必须包含指定功能。"""
    def checker(plan: Plan | None = Depends(get_active_plan)):
        if plan is None or code not in (plan.features or []):
            raise HTTPException(403, "当前套餐不含该功能，请升级")
    return checker
