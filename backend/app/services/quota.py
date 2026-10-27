"""配额：AI 调用次数等用量限制。"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import QuotaUsage


def consume_quota(db: Session, merchant_id: int, quota_key: str, limit: int | None) -> None:
    """扣减配额。limit 为 None 表示不限量（跳过）；limit<=0 视为 0 配额，直接抛 429。"""
    if limit is None:
        return
    if limit <= 0:
        raise HTTPException(429, "本月配额已用尽，请升级套餐")
    period = date.today().strftime("%Y-%m")
    usage = db.scalar(select(QuotaUsage).where(
        QuotaUsage.merchant_id == merchant_id,
        QuotaUsage.quota_key == quota_key,
        QuotaUsage.period == period,
    ))
    if usage is None:
        usage = QuotaUsage(merchant_id=merchant_id, quota_key=quota_key,
                           period=period, used_count=0)
        db.add(usage)
    if usage.used_count >= limit:
        raise HTTPException(429, f"本月配额已用尽（{limit} 次），请升级套餐")
    usage.used_count += 1
    db.commit()
