import re
from collections import Counter
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import jieba
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_store, require_feature
from ..models import Alert, DailyMetric, Product, Review, Store
from ..schemas.dashboard import KpiSummary

router = APIRouter(dependencies=[Depends(require_feature("dashboard"))])

# 词频统计的停用词（多字功能词/噪声词；单字由 len>=2 过滤）
STOPWORDS = {
    "我们", "你们", "他们", "这个", "那个", "就是", "还是", "但是", "而且",
    "因为", "所以", "比较", "有点", "感觉", "没有", "不是", "下次", "一点",
    "真的", "特别", "非常", "然后", "味道",
}


def _agg(db: Session, store_id: int, day: date):
    row = db.execute(
        select(
            func.coalesce(func.sum(DailyMetric.revenue), 0),
            func.coalesce(func.sum(DailyMetric.order_count), 0),
            func.coalesce(func.sum(DailyMetric.valid_order_count), 0),
        ).where(DailyMetric.store_id == store_id, DailyMetric.date == day)
    ).one()
    return Decimal(str(row[0] if row[0] else "0")), int(row[1]), int(row[2])


def _pct_change(cur: Decimal, prev: Decimal) -> Decimal | None:
    if not prev:
        return None
    return ((cur - prev) / prev * 100).quantize(Decimal("0.01"))


@router.get("/dashboard/summary", response_model=KpiSummary)
def dashboard_summary(store: Store = Depends(get_current_store), db: Session = Depends(get_db)) -> KpiSummary:
    today = date.today()
    revenue, order_count, valid = _agg(db, store.id, today)
    revenue_7, order_7, valid_7 = _agg(db, store.id, today - timedelta(days=7))

    avg = (revenue / valid).quantize(Decimal("0.01")) if valid else Decimal("0")
    avg_7 = (revenue_7 / valid_7).quantize(Decimal("0.01")) if valid_7 else Decimal("0")
    valid_rate = (Decimal(valid) / order_count * 100).quantize(Decimal("0.01")) if order_count else Decimal("0")

    return KpiSummary(
        date=today, revenue=revenue, order_count=order_count,
        valid_order_count=valid, avg_order_value=avg, valid_rate=valid_rate,
        revenue_change_pct=_pct_change(revenue, revenue_7),
        order_count_change_pct=_pct_change(Decimal(order_count), Decimal(order_7)),
        avg_order_value_change_pct=_pct_change(avg, avg_7),
    )


@router.get("/dashboard/trend")
def dashboard_trend(days: int = Query(30, ge=7, le=90), store: Store = Depends(get_current_store),
                    db: Session = Depends(get_db)):
    start = date.today() - timedelta(days=days - 1)
    rows = db.execute(
        select(DailyMetric.date, DailyMetric.revenue, DailyMetric.order_count)
        .where(DailyMetric.store_id == store.id, DailyMetric.date >= start)
        .order_by(DailyMetric.date)
    ).all()
    return {"days": days, "items": [
        {"date": d.isoformat(), "revenue": str(r), "order_count": o}
        for d, r, o in rows
    ]}


@router.get("/dashboard/products")
def dashboard_products(store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    products = db.scalars(
        select(Product).where(Product.store_id == store.id)
        .options(selectinload(Product.category))
    ).all()

    def _ser(p: Product):
        return {"id": p.id, "name": p.name,
                "category": p.category.name if p.category else None,
                "price": str(p.price), "sales": p.sales,
                "stock": p.stock, "status": p.status}

    hot = sorted(products, key=lambda p: p.sales, reverse=True)[:10]
    slow = sorted(products, key=lambda p: p.sales)[:10]
    sold_out = [p for p in products if p.stock == 0]
    return {"hot": [_ser(p) for p in hot],
            "slow": [_ser(p) for p in slow],
            "sold_out": [_ser(p) for p in sold_out]}


@router.get("/dashboard/alerts")
def dashboard_alerts(store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    alerts = db.scalars(
        select(Alert).where(Alert.store_id == store.id, Alert.status == "open")
        .order_by(Alert.triggered_at.desc())
    ).all()
    return {"items": [
        {"id": a.id, "rule": a.rule, "level": a.level, "payload": a.payload,
         "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None}
        for a in alerts
    ]}


@router.get("/dashboard/rating-trend")
def dashboard_rating_trend(days: int = Query(30, ge=7, le=90), store: Store = Depends(get_current_store),
                           db: Session = Depends(get_db)):
    start = datetime.combine(date.today() - timedelta(days=days - 1), time.min)
    rows = db.execute(
        select(func.date(Review.created_at), func.avg(Review.rating), func.count(Review.id))
        .where(Review.store_id == store.id, Review.created_at >= start)
        .group_by(func.date(Review.created_at))
        .order_by(func.date(Review.created_at))
    ).all()
    return {"items": [
        {"date": d, "avg_rating": round(float(a), 2), "count": c}
        for d, a, c in rows
    ]}


@router.get("/dashboard/word-frequency")
def dashboard_word_frequency(days: int = Query(30, ge=7, le=90), store: Store = Depends(get_current_store),
                             db: Session = Depends(get_db)):
    start = datetime.combine(date.today() - timedelta(days=days - 1), time.min)
    reviews = db.scalars(
        select(Review).where(Review.store_id == store.id, Review.created_at >= start)
    ).all()

    pos: Counter = Counter()
    neg: Counter = Counter()
    for r in reviews:
        if r.rating >= 4:
            target = pos
        elif r.rating <= 2:
            target = neg
        else:
            continue
        if r.tags:
            for t in r.tags.split(","):
                t = t.strip()
                if t:
                    target[t] += 1
        if r.content:
            for w in jieba.cut(r.content):
                w = w.strip()
                if len(w) >= 2 and w not in STOPWORDS and not w.isdigit() \
                        and not re.fullmatch(r"[\W_]+", w):
                    target[w] += 1

    def _ser(c: Counter, n: int = 10):
        return [{"word": w, "count": c} for w, c in c.most_common(n)]

    return {"positive": _ser(pos), "negative": _ser(neg)}
