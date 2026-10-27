from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_active_plan, get_current_store, require_feature, require_merchant
from ..models import CustomerMessage, KnowledgeItem, MerchantUser, Order, Plan, Store
from ..models import Session as ImSession
from ..services.ai import generate_review_reply, handle_im_message
from ..services.knowledge import retrieve_knowledge
from ..services.llm import LLMError
from ..services.quota import consume_quota
from .orders import STATUS_LABELS

router = APIRouter(dependencies=[Depends(require_feature("service"))])

# 自动回复置信度阈值：达到此值且是安全意图（auto）时，直接发送无需人工点击
AUTO_SEND_THRESHOLD = 0.85


def _consume_ai_quota(db: Session, user: MerchantUser, plan: Plan | None) -> None:
    limit = (plan.quotas or {}).get("ai_calls_monthly") if plan else None
    consume_quota(db, user.merchant_id, "ai_calls_monthly", limit)


@router.post("/ai/review-reply")
def ai_review_reply(payload: dict, user: MerchantUser = Depends(require_merchant),
                    plan: Plan | None = Depends(get_active_plan),
                    store: Store = Depends(get_current_store),
                    db: Session = Depends(get_db)):
    """给一条评价生成回复草稿（好评致谢 / 差评安抚并引用商家 SOP 话术）。
    generate_review_reply 内部已做 LLM 降级，不再裸抛 502。"""
    _consume_ai_quota(db, user, plan)
    # 拉取本店「rule」类知识作为 SOP 话术规范，供差评回复引用
    sop_items = db.scalars(
        select(KnowledgeItem).where(
            KnowledgeItem.store_id == store.id, KnowledgeItem.type == "rule"
        )
    ).all()
    sop_text = "\n".join(f"- {it.answer}" for it in sop_items)
    draft = generate_review_reply(int(payload.get("rating", 5)), payload.get("content") or "", sop_text=sop_text)
    return {"draft": draft}


@router.post("/ai/im-reply")
def ai_im_reply(payload: dict, user: MerchantUser = Depends(require_merchant),
                plan: Plan | None = Depends(get_active_plan),
                store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    """处理一条顾客消息，按混合模式返回意图 + 动作 + 回复。"""
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(400, "消息不能为空")
    _consume_ai_quota(db, user, plan)

    # RAG：向量召回与顾客消息最相关的 top-k 知识（faq/rule/greeting），而非全量塞入 prompt
    knowledge_items = retrieve_knowledge(
        db, store.id, message, top_k=3, types=["faq", "rule", "greeting"]
    )
    business = (
        f"店铺：{store.name}；营业时间：{store.business_hours or '未知'}；"
        f"地址：{store.address or '未知'}；电话：{store.phone or '未知'}"
    )

    # 半自动「催单」需要订单上下文；同时拼多轮历史给 LLM 做上下文
    order_info = None
    history: list[dict] = []
    session_id = payload.get("session_id")
    if session_id:
        sess = db.get(ImSession, session_id)
        if sess and sess.store_id == store.id:
            # 订单上下文（催单用）
            if sess.customer_id:
                recent = db.scalar(
                    select(Order).where(Order.customer_id == sess.customer_id)
                    .order_by(Order.placed_at.desc()).limit(1)
                )
                if recent:
                    order_info = f"{STATUS_LABELS.get(recent.status, recent.status)}（订单 {recent.order_no}）"
            # 多轮上下文：取最近 10 条消息，拼成 user/assistant 轮次给 LLM
            msgs = db.scalars(
                select(CustomerMessage)
                .where(CustomerMessage.session_id == session_id)
                .order_by(CustomerMessage.created_at.desc())
                .limit(10)
            ).all()
            # 取最近 10 条后反转为时间正序，作为多轮上下文喂给 LLM
            msgs = list(reversed(msgs))
            for m in msgs:
                if not m.content:
                    continue
                history.append({
                    "role": "assistant" if m.direction == "outbound" else "user",
                    "content": m.content,
                })

    try:
        result = handle_im_message(message, knowledge_items, business, order_info, history=history)
    except LLMError as e:
        raise HTTPException(502, str(e))

    # 紧急意图（售后/投诉/食品安全 → 转人工）标记为紧急消息，首页实时提醒
    if result["action"] == "manual" and session_id:
        recent_msg = db.scalar(
            select(CustomerMessage).where(
                CustomerMessage.session_id == session_id,
                CustomerMessage.direction == "inbound",
            ).order_by(CustomerMessage.created_at.desc()).limit(1)
        )
        if recent_msg:
            recent_msg.is_urgent = True
            db.commit()

    # 高置信度自动回复：auto 动作 + 置信度达标 + 有会话 → 直接落库发送，无需人工点击
    # 阈值和开关从门店设置读取（可在设置页调整）
    auto_sent = False
    st = store.settings or {}
    auto_enabled = st.get("ai_auto_send", True)
    threshold = st.get("ai_threshold", AUTO_SEND_THRESHOLD)
    if (auto_enabled and result["action"] == "auto"
            and result["confidence"] >= threshold and session_id):
        db.add(CustomerMessage(session_id=session_id, store_id=store.id,
                               content=result["reply"], direction="outbound"))
        db.commit()
        auto_sent = True
    result["auto_sent"] = auto_sent
    return result
