"""商家端设置：门店信息、知识库 FAQ、AI 客服、预警阈值、账号安全。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_store, require_merchant
from ..models import KnowledgeItem, MerchantUser, Store
from ..models.enums import KnowledgeType
from ..services.auth import hash_password, verify_password

router = APIRouter()

# 默认设置
DEFAULT_SETTINGS = {
    "ai_auto_send": True,       # AI 高置信度自动回复开关
    "ai_threshold": 0.85,       # 自动回复置信度阈值
    "order_drop_ratio": 0.7,    # 订单骤降阈值（较近7天同时段均值 × 70%）
    "bad_review_count": 3,      # 差评激增阈值（24h ≥ N 条）
    "rating_min": 4.2,          # 评分跌破阈值
    "sound_enabled": True,      # 紧急消息声音提醒开关
}


def _get_settings(store: Store) -> dict:
    s = dict(DEFAULT_SETTINGS)
    s.update(store.settings or {})
    return s


def _faq_dict(f: KnowledgeItem) -> dict:
    return {"id": f.id, "question": f.question, "answer": f.answer, "keywords": f.keywords}


@router.get("/settings")
def get_settings(store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    faqs = db.scalars(
        select(KnowledgeItem).where(
            KnowledgeItem.store_id == store.id, KnowledgeItem.type == KnowledgeType.faq.value
        ).order_by(KnowledgeItem.id)
    ).all()
    return {
        "store": {"name": store.name, "address": store.address,
                  "phone": store.phone, "business_hours": store.business_hours},
        "settings": _get_settings(store),
        "faqs": [_faq_dict(f) for f in faqs],
    }


@router.put("/settings/store")
def update_store(payload: dict, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    """更新门店信息（AI 客服上下文）。"""
    if "name" in payload:
        store.name = payload["name"]
    if "address" in payload:
        store.address = payload["address"]
    if "phone" in payload:
        store.phone = payload["phone"]
    if "business_hours" in payload:
        store.business_hours = payload["business_hours"]
    db.commit()
    return {"ok": True}


@router.put("/settings/ai")
def update_settings(payload: dict, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    """更新 AI 客服 / 预警 / 通知设置。"""
    settings = _get_settings(store)
    for key in DEFAULT_SETTINGS:
        if key in payload:
            settings[key] = payload[key]
    store.settings = settings
    db.commit()
    return {"settings": settings}


# ---------- 知识库 FAQ ----------
@router.post("/settings/faqs")
def create_faq(payload: dict, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    faq = KnowledgeItem(store_id=store.id, type=KnowledgeType.faq.value,
                        question=payload.get("question", ""),
                        answer=payload.get("answer", ""),
                        keywords=payload.get("keywords", ""))
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return _faq_dict(faq)


@router.put("/settings/faqs/{faq_id}")
def update_faq(faq_id: int, payload: dict, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    faq = db.get(KnowledgeItem, faq_id)
    if not faq or faq.store_id != store.id:
        raise HTTPException(404, "FAQ 不存在")
    if "question" in payload:
        faq.question = payload["question"]
    if "answer" in payload:
        faq.answer = payload["answer"]
    if "keywords" in payload:
        faq.keywords = payload["keywords"]
    db.commit()
    return {"ok": True}


@router.delete("/settings/faqs/{faq_id}")
def delete_faq(faq_id: int, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    faq = db.get(KnowledgeItem, faq_id)
    if not faq or faq.store_id != store.id:
        raise HTTPException(404, "FAQ 不存在")
    db.delete(faq)
    db.commit()
    return {"ok": True}


# ---------- 账号安全 ----------
@router.post("/settings/password")
def change_password(payload: dict, user: MerchantUser = Depends(require_merchant), db: Session = Depends(get_db)):
    old = payload.get("old_password", "")
    new = payload.get("new_password", "")
    if not verify_password(old, user.password_hash):
        raise HTTPException(400, "原密码错误")
    if len(new) < 6:
        raise HTTPException(400, "新密码至少 6 位")
    user.password_hash = hash_password(new)
    db.commit()
    return {"ok": True}
