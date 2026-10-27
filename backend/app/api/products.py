from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_store, require_feature
from ..models import Category, Product, Store

router = APIRouter(dependencies=[Depends(require_feature("products"))])


def _ser(p: Product) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "app_food_code": p.app_food_code,
        "category_id": p.category_id,
        "category": p.category.name if p.category else None,
        "price": str(p.price),
        "stock": p.stock,
        "sales": p.sales,
        "status": p.status,
    }


@router.get("/categories")
def list_categories(store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    cats = db.scalars(
        select(Category).where(Category.store_id == store.id).order_by(Category.sort)
    ).all()
    return {"items": [{"id": c.id, "name": c.name} for c in cats]}


@router.get("/products")
def list_products(
    category_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    store: Store = Depends(get_current_store),
    db: Session = Depends(get_db),
):
    filters = [Product.store_id == store.id]
    if category_id:
        filters.append(Product.category_id == category_id)
    if status:
        filters.append(Product.status == status)
    if q:
        filters.append(Product.name.contains(q))
    rows = db.scalars(
        select(Product).where(*filters).options(selectinload(Product.category))
        .order_by(Product.sales.desc())
    ).all()
    return {"items": [_ser(p) for p in rows]}


@router.post("/products/batch")
def batch_update(payload: dict, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    """批量上下架 / 批量改价。action: on | off | price（price 时需传 price）。"""
    ids = payload.get("ids") or []
    action = payload.get("action")
    price = payload.get("price")
    updated = 0
    for pid in ids:
        p = db.get(Product, pid)
        if not p or p.store_id != store.id:
            continue
        if action == "on":
            p.status = "on"
        elif action == "off":
            p.status = "off"
        elif action == "price" and price is not None:
            p.price = Decimal(str(price))
        else:
            continue
        updated += 1
    db.commit()
    return {"updated": updated}
