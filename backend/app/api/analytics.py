"""分析详情页接口：时段分布、评分分布、好评率趋势。"""
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_store, require_feature
from ..models import Order, Review, Store

router = APIRouter(dependencies=[Depends(require_feature("dashboard"))])


@router.get("/analytics/hourly")
def hourly(days: int = Query(30, ge=7, le=90), store: Store = Depends(get_current_store),
           db: Session = Depends(get_db)):
    """订单按小时分布（找高峰低谷）。"""
    start = datetime.combine(date.today() - timedelta(days=days - 1), time.min)
    rows = db.execute(
        select(func.strftime("%H", Order.placed_at), func.count(Order.id), func.sum(Order.total_amount))
        .where(Order.store_id == store.id, Order.placed_at >= start, Order.is_valid.is_(True))
        .group_by(func.strftime("%H", Order.placed_at))
    ).all()
    data = {int(h): {"count": c, "revenue": r or 0} for h, c, r in rows}
    return {"items": [
        {"hour": h, "order_count": data.get(h, {}).get("count", 0),
         "revenue": str(data.get(h, {}).get("revenue", 0))}
        for h in range(24)
    ]}


@router.get("/analytics/rating-distribution")
def rating_distribution(days: int = Query(30, ge=7, le=90), store: Store = Depends(get_current_store),
                        db: Session = Depends(get_db)):
    """1-5 星评价分布 + 平均分。"""
    start = datetime.combine(date.today() - timedelta(days=days - 1), time.min)
    rows = db.execute(
        select(Review.rating, func.count(Review.id))
        .where(Review.store_id == store.id, Review.created_at >= start)
        .group_by(Review.rating)
    ).all()
    counts = {r: c for r, c in rows}
    total = sum(counts.values())
    avg = sum(r * c for r, c in rows) / total if total else 0
    items = [{"rating": r, "count": counts.get(r, 0),
              "pct": round(counts.get(r, 0) / total * 100, 1) if total else 0}
             for r in range(1, 6)]
    return {"items": items, "total": total, "avg_rating": round(avg, 2)}


@router.get("/analytics/sentiment-trend")
def sentiment_trend(days: int = Query(30, ge=7, le=90), store: Store = Depends(get_current_store),
                    db: Session = Depends(get_db)):
    """好评率 / 差评率逐日趋势。"""
    start = datetime.combine(date.today() - timedelta(days=days - 1), time.min)
    rows = db.execute(
        select(func.date(Review.created_at), Review.rating, func.count(Review.id))
        .where(Review.store_id == store.id, Review.created_at >= start)
        .group_by(func.date(Review.created_at), Review.rating)
    ).all()
    per_day = defaultdict(lambda: {"good": 0, "bad": 0, "total": 0})
    for d, rating, c in rows:
        rec = per_day[d]
        rec["total"] += c
        if rating >= 4:
            rec["good"] += c
        elif rating <= 2:
            rec["bad"] += c
    items = []
    for d in sorted(per_day):
        rec = per_day[d]
        items.append({
            "date": d,
            "good_rate": round(rec["good"] / rec["total"] * 100, 1) if rec["total"] else 0,
            "bad_rate": round(rec["bad"] / rec["total"] * 100, 1) if rec["total"] else 0,
        })
    return {"items": items}
