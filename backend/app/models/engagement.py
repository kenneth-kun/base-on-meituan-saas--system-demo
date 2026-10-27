"""互动数据：预警、IM 会话、顾客消息、AI 回复记录、知识库。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, now
from .enums import AlertLevel, AlertStatus, KnowledgeType, MessageDirection, ReplyStatus


class Alert(Base):
    __tablename__ = "alert"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"), index=True)
    rule: Mapped[str] = mapped_column(String(100))
    level: Mapped[str] = mapped_column(String(20), default=AlertLevel.warning.value)
    status: Mapped[str] = mapped_column(String(20), default=AlertStatus.open.value)
    payload: Mapped[str | None] = mapped_column(Text)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)


class Session(Base):
    __tablename__ = "session"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("order.id"))
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    messages: Mapped[list["CustomerMessage"]] = relationship(back_populates="session")


class CustomerMessage(Base):
    __tablename__ = "customer_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("session.id"))
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("order.id"))
    content: Mapped[str] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(String(10), default=MessageDirection.inbound.value)
    msg_id: Mapped[str | None] = mapped_column(String(40))  # 美团消息ID
    scene_tag: Mapped[str | None] = mapped_column(String(20))  # 场景标签
    wm_order_id: Mapped[str | None] = mapped_column(String(30))  # 关联美团订单号
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)  # 紧急消息
    is_handled: Mapped[bool] = mapped_column(Boolean, default=False)  # 已处理
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    session: Mapped["Session"] = relationship(back_populates="messages")


class ReplyRecord(Base):
    __tablename__ = "reply_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("customer_message.id"))
    intent: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[float | None] = mapped_column(Float)
    ai_content: Mapped[str] = mapped_column(Text)
    edited_content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=ReplyStatus.pending.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.id"), index=True)
    type: Mapped[str] = mapped_column(String(20), default=KnowledgeType.faq.value)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text)  # 逗号分隔
