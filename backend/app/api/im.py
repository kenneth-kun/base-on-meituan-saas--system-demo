from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_store, require_feature
from ..models import CustomerMessage, Store
from ..models import Session as ImSession

router = APIRouter(dependencies=[Depends(require_feature("service"))])


@router.get("/im/sessions")
def list_sessions(store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    sessions = db.scalars(
        select(ImSession).where(ImSession.store_id == store.id)
        .options(selectinload(ImSession.messages))
        .order_by(ImSession.updated_at.desc())
    ).all()
    items = []
    for s in sessions:
        msgs = sorted(s.messages, key=lambda m: m.created_at)
        last = msgs[-1].content if msgs else ""
        unhandled = sum(1 for m in msgs if m.is_urgent and not m.is_handled)
        items.append({
            "id": s.id,
            "customer_id": s.customer_id,
            "last_message": last,
            "message_count": len(msgs),
            "unhandled_count": unhandled,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })
    return {"items": items}


@router.get("/im/sessions/{session_id}/messages")
def list_messages(session_id: int, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    sess = db.get(ImSession, session_id)
    if not sess or sess.store_id != store.id:
        raise HTTPException(404, "会话不存在")
    msgs = db.scalars(
        select(CustomerMessage).where(CustomerMessage.session_id == session_id)
        .order_by(CustomerMessage.created_at)
    ).all()
    return {"items": [
        {"id": m.id, "content": m.content, "direction": m.direction,
         "msg_id": m.msg_id, "scene_tag": m.scene_tag, "wm_order_id": m.wm_order_id,
         "is_urgent": m.is_urgent, "is_handled": m.is_handled,
         "created_at": m.created_at.isoformat() if m.created_at else None}
        for m in msgs
    ]}


@router.post("/im/sessions/{session_id}/messages")
def add_message(session_id: int, payload: dict, store: Store = Depends(get_current_store),
                db: Session = Depends(get_db)):
    content = (payload.get("content") or "").strip()
    if not content:
        raise HTTPException(400, "内容不能为空")
    direction = payload.get("direction", "inbound")
    if direction not in ("inbound", "outbound"):
        direction = "inbound"
    sess = db.get(ImSession, session_id)
    if not sess or sess.store_id != store.id:
        raise HTTPException(404, "会话不存在")
    msg = CustomerMessage(session_id=session_id, store_id=sess.store_id,
                          content=content, direction=direction)
    db.add(msg)
    sess.updated_at = datetime.now()  # 会话按最新消息冒泡到列表顶部
    db.commit()
    return {"id": msg.id, "content": msg.content, "direction": msg.direction,
            "created_at": msg.created_at.isoformat() if msg.created_at else None}


@router.get("/im/urgent-messages")
def urgent_messages(store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    """未处理的紧急客服消息（首页实时提醒用）。"""
    msgs = db.scalars(
        select(CustomerMessage).where(
            CustomerMessage.store_id == store.id,
            CustomerMessage.is_urgent.is_(True),
            CustomerMessage.is_handled.is_(False),
        ).order_by(CustomerMessage.created_at.desc()).limit(20)
    ).all()
    return {"items": [
        {"id": m.id, "session_id": m.session_id, "content": m.content,
         "scene_tag": m.scene_tag,
         "created_at": m.created_at.isoformat() if m.created_at else None}
        for m in msgs
    ]}


@router.post("/im/messages/{message_id}/handle")
def handle_message(message_id: int, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    """标记紧急消息已处理。"""
    m = db.get(CustomerMessage, message_id)
    if not m or m.store_id != store.id:
        raise HTTPException(404, "消息不存在")
    m.is_handled = True
    db.commit()
    return {"ok": True}
