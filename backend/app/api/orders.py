from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_store, require_feature
from ..models import Order, OrderItem, Store
from ..models.enums import OrderStatus

router = APIRouter(dependencies=[Depends(require_feature("orders"))])

STATUS_LABELS = {
    "pending": "待接单",
    "confirmed": "制作中",
    "delivering": "配送中",
    "completed": "已完成",
    "cancelled": "已取消",
    "refunding": "退款中",
}


def _ser(o: Order) -> dict:
    return {
        "id": o.id,
        "order_no": o.order_no,
        "wm_order_id_view": o.wm_order_id_view,
        "status": o.status,
        "status_label": STATUS_LABELS.get(o.status, o.status),
        "total_amount": str(o.total_amount),
        "placed_at": o.placed_at.isoformat(),
        "is_valid": o.is_valid,
        "item_count": len(o.items) if o.items is not None else 0,
        "review_id": o.review.id if o.review else None,
        "review_rating": o.review.rating if o.review else None,
    }


@router.get("/orders")
def list_orders(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
):
    statuses = [{"value": k, "label": v} for k, v in STATUS_LABELS.items()]
    filters = [Order.store_id == store.id]
    if status:
        filters.append(Order.status == status)

    total = db.scalar(select(func.count(Order.id)).where(*filters))
    rows = db.scalars(
        select(Order).where(*filters)
        .options(selectinload(Order.items), selectinload(Order.review))
        .order_by(Order.placed_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"total": total, "items": [_ser(o) for o in rows], "statuses": statuses}


@router.get("/orders/{order_id}")
def get_order(order_id: int, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    """订单详情：金额明细 + 商品明细 + 关联评价。"""
    o = db.scalar(
        select(Order).where(Order.id == order_id, Order.store_id == store.id)
        .options(selectinload(Order.items).selectinload(OrderItem.product),
                 selectinload(Order.review))
    )
    if not o:
        raise HTTPException(404, "订单不存在")

    items = []
    for it in o.items:
        items.append({
            "product_name": it.product.name if it.product else "未知商品",
            "qty": it.qty,
            "unit_price": str(it.unit_price),
            "subtotal": str(it.unit_price * it.qty),
        })

    review = None
    if o.review:
        review = {
            "id": o.review.id,
            "rating": o.review.rating,
            "content": o.review.content,
            "tags": o.review.tags,
            "reply": o.review.reply,
            "replied_at": o.review.replied_at.isoformat() if o.review.replied_at else None,
        }

    return {
        "id": o.id,
        "order_no": o.order_no,
        "wm_order_id_view": o.wm_order_id_view,
        "status": o.status,
        "status_label": STATUS_LABELS.get(o.status, o.status),
        "total_amount": str(o.total_amount),
        "original_price": str(o.original_price),
        "commission": str(o.commission),
        "subsidy": str(o.subsidy),
        "delivery_fee": str(o.delivery_fee),
        "recipient_name": o.recipient_name,
        "recipient_phone": o.recipient_phone,
        "recipient_address": o.recipient_address,
        "placed_at": o.placed_at.isoformat(),
        "is_valid": o.is_valid,
        "items": items,
        "review": review,
    }


@router.post("/orders/batch-confirm")
def batch_confirm(payload: dict, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    """一键接单：把选中的待接单订单批量改为制作中。"""
    ids = payload.get("ids") or []
    updated = 0
    for oid in ids:
        o = db.get(Order, oid)
        if o and o.store_id == store.id and o.status == OrderStatus.pending.value:
            o.status = OrderStatus.confirmed.value
            updated += 1
    db.commit()
    return {"updated": updated}
