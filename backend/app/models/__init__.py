"""导入所有模型，确保 Base.metadata 注册完整。"""
from .base import Base
from .core import Category, Customer, Merchant, Platform, Product, Store
from .engagement import (Alert, CustomerMessage, KnowledgeItem, ReplyRecord,
                         Session)
from .management import (FEATURES, AdminUser, MerchantUser, Plan, QuotaUsage,
                         Subscription)
from .trade import DailyMetric, Order, OrderItem, Review

__all__ = [
    "Base",
    "Platform", "Merchant", "Store", "Category", "Product", "Customer",
    "Order", "OrderItem", "Review", "DailyMetric",
    "Alert", "Session", "CustomerMessage", "ReplyRecord", "KnowledgeItem",
    "AdminUser", "MerchantUser", "Plan", "Subscription", "QuotaUsage", "FEATURES",
]
