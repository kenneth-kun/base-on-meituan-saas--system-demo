from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_store, require_feature
from ..models import Alert, Store
from ..models.enums import AlertStatus

router = APIRouter(dependencies=[Depends(require_feature("alerts"))])


def _ser(a: Alert) -> dict:
    return {
        "id": a.id,
        "rule": a.rule,
        "level": a.level,
        "status": a.status,
        "payload": a.payload,
        "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
    }


@router.get("/alerts")
def list_alerts(store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Alert).where(Alert.store_id == store.id).order_by(Alert.triggered_at.desc())
    ).all()
    return {"items": [_ser(a) for a in rows]}


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, store: Store = Depends(get_current_store), db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a or a.store_id != store.id:
        raise HTTPException(404, "预警不存在")
    a.status = AlertStatus.resolved.value
    a.resolved_at = datetime.now()
    db.commit()
    return {"ok": True}
