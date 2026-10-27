from enum import Enum


class PlatformCode(str, Enum):
    meituan = "meituan"
    eleme = "eleme"
    douyin = "douyin"


class OrderStatus(str, Enum):
    pending = "pending"          # 待接单
    confirmed = "confirmed"      # 已接单/制作中
    delivering = "delivering"    # 配送中
    completed = "completed"      # 已完成
    cancelled = "cancelled"      # 已取消
    refunding = "refunding"      # 退款中


class ProductStatus(str, Enum):
    on = "on"
    off = "off"


class AlertLevel(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertStatus(str, Enum):
    open = "open"
    resolved = "resolved"


class MessageDirection(str, Enum):
    inbound = "inbound"    # 顾客 -> 商家
    outbound = "outbound"  # 商家 -> 顾客


class ReplyStatus(str, Enum):
    pending = "pending"    # 待确认（半自动草稿）
    sent = "sent"          # 已发送
    rejected = "rejected"  # 已驳回


class KnowledgeType(str, Enum):
    faq = "faq"
    rule = "rule"
    greeting = "greeting"
