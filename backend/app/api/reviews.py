from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_store, require_feature
from ..models import Review, Store

router = APIRouter(dependencies=[Depends(require_feature("reviews"))])


def _ser(r: Review) -> dict:
    return {
        "id": r.id,
        "rating": r.rating,
        "accurate_star": r.accurate_star,
        "consume_amount": str(r.consume_amount) if r.consume_amount is not None else None,
        "content": r.content,
        "tags": r.tags,
        "reply": r.reply,
        "replied_at": r.replied_at.isoformat() if r.replied_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "order_no": r.order.order_no if r.order else None,
    }


@router.get("/reviews")
def list_reviews(
    rating: int | None = None,
    replied: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
):
    filters = [Review.store_id == store.id]
    if rating:
        filters.append(Review.rating == rating)
    if replied is not None:
        if replied:
            filters.append(Review.reply.isnot(None))
        else:
            filters.append(Review.reply.is_(None))

    total = db.scalar(select(func.count(Review.id)).where(*filters))
    rows = db.scalars(
        select(Review).where(*filters).options(selectinload(Review.order))
        .order_by(Review.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"total": total, "items": [_ser(r) for r in rows]}


@router.post("/reviews/{review_id}/reply")
def reply_review(review_id: int, payload: dict, store: Store = Depends(get_current_store),
                 db: Session = Depends(get_db)):
    r = db.get(Review, review_id)
    if not r or r.store_id != store.id:
        raise HTTPException(404, "评价不存在")
    r.reply = payload.get("content")
    r.replied_at = datetime.now()
    db.commit()
    return {"ok": True}
