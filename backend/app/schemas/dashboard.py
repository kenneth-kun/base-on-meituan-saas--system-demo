from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class KpiSummary(BaseModel):
    """看板顶部 KPI 汇总（今日 + 环比 7 天前）。"""
    date: date
    revenue: Decimal
    order_count: int
    valid_order_count: int
    avg_order_value: Decimal
    valid_rate: Decimal
    revenue_change_pct: Decimal | None = None
    order_count_change_pct: Decimal | None = None
    avg_order_value_change_pct: Decimal | None = None
