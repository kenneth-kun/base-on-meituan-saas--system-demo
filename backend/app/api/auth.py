from datetime import date

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import AdminUser, MerchantUser, Plan, Subscription
from ..models.management import FEATURES
from ..services.auth import create_token, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = "merchant"  # "admin" | "merchant"


@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if payload.role == "admin":
        user = db.scalar(select(AdminUser).where(AdminUser.username == payload.username))
        user_type = "admin"
    else:
        user = db.scalar(select(MerchantUser).where(MerchantUser.username == payload.username))
        user_type = "merchant"

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")

    if user_type == "merchant" and user.status != "active":
        raise HTTPException(403, "账号已被禁用")

    token = create_token(user_type, user.id)
    return {
        "token": token,
        "type": user_type,
        "username": payload.username,
        "merchant_id": user.merchant_id if user_type == "merchant" else None,
    }


@router.post("/auth/wx-login")
def wx_login(payload: dict, db: Session = Depends(get_db)):
    """微信小程序登录：code 换 openid，已绑定则返回 token，否则提示绑定。"""
    code = payload.get("code")
    if not code:
        raise HTTPException(400, "缺少 code")
    if not settings.wx_appid or not settings.wx_secret:
        raise HTTPException(400, "未配置微信小程序 appid/secret")

    url = ("https://api.weixin.qq.com/sns/jscode2session"
           f"?appid={settings.wx_appid}&secret={settings.wx_secret}"
           f"&js_code={code}&grant_type=authorization_code")
    try:
        data = httpx.get(url, timeout=10.0).json()
    except Exception as e:
        raise HTTPException(502, f"微信接口调用失败: {e}")

    if "openid" not in data:
        raise HTTPException(400, f"微信登录失败: {data.get('errmsg', '未知错误')}")
    openid = data["openid"]

    user = db.scalar(select(MerchantUser).where(MerchantUser.openid == openid))
    if user is None:
        return {"need_bind": True, "openid": openid}
    if user.status != "active":
        raise HTTPException(403, "账号已被禁用")
    token = create_token("merchant", user.id)
    return {"need_bind": False, "token": token, "type": "merchant",
            "username": user.username, "merchant_id": user.merchant_id}


@router.post("/auth/wx-bind")
def wx_bind(payload: dict, db: Session = Depends(get_db)):
    """首次微信登录时，用账号密码验证后绑定 openid。"""
    openid = payload.get("openid")
    username = payload.get("username")
    password = payload.get("password")
    if not openid or not username or not password:
        raise HTTPException(400, "参数不完整")
    user = db.scalar(select(MerchantUser).where(MerchantUser.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    if user.status != "active":
        raise HTTPException(403, "账号已被禁用")
    other = db.scalar(select(MerchantUser).where(MerchantUser.openid == openid))
    if other is not None and other.id != user.id:
        raise HTTPException(400, "该微信已绑定其他账号")
    user.openid = openid
    db.commit()
    token = create_token("merchant", user.id)
    return {"token": token, "type": "merchant",
            "username": user.username, "merchant_id": user.merchant_id}


@router.get("/auth/me")
def me(current: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """当前登录用户信息 + 功能列表（商家按套餐，管理员为全部）。"""
    user = current["user"]
    if current["type"] == "admin":
        return {"type": "admin", "username": user.username,
                "features": [f["code"] for f in FEATURES]}

    sub = db.scalar(select(Subscription).where(Subscription.merchant_id == user.merchant_id)
                    .order_by(Subscription.id.desc()).limit(1))
    plan = db.get(Plan, sub.plan_id) if sub else None
    features = plan.features if plan and sub and sub.status == "active" and sub.expired_at >= date.today() else []
    return {"type": "merchant", "username": user.username,
            "merchant_id": user.merchant_id, "features": features}
