from fastapi import APIRouter, Depends

from ..config import settings
from ..deps import require_merchant
from ..services.refresh import get_last_refresh_at, refresh_data

router = APIRouter()


@router.post("/refresh")
def manual_refresh(_user=Depends(require_merchant)):
    """手动触发一次数据刷新。"""
    return refresh_data()


@router.get("/refresh/status")
def refresh_status(_user=Depends(require_merchant)):
    last = get_last_refresh_at()
    return {
        "last_refresh_at": last.isoformat() if last else None,
        "interval_minutes": settings.refresh_interval_minutes,
    }
