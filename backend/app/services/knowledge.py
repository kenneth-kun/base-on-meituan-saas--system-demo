"""知识库检索（RAG 核心）：向量召回 top-k 相关知识条目。

与 PlatformAdapter / EmbeddingProvider 同一设计哲学——业务层只调用 retrieve_knowledge，
底层向量来自可替换的 embedding_provider，不耦合具体模型。
"""
from __future__ import annotations

import hashlib
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import KnowledgeItem
from .embeddings import embedding_provider

# 简单内存缓存：避免同一知识条目在多次请求中重复计算向量（key=内容哈希）
_vec_cache: dict[str, list[float]] = {}


def _cache_key(text: str) -> str:
    return hashlib.md5((text or "").encode("utf-8")).hexdigest()


def _embed_cached(text: str) -> list[float]:
    key = _cache_key(text)
    v = _vec_cache.get(key)
    if v is None:
        v = embedding_provider.embed([text])[0]
        _vec_cache[key] = v
    return v


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def retrieve_knowledge(
    db: Session,
    store_id: int,
    query: str,
    top_k: int = 3,
    types: list[str] | None = None,
) -> list[dict]:
    """从知识库向量召回与 query 最相关的 top_k 条，返回带 score 的 dict 列表。

    types: 限定检索的知识类型（faq/rule/greeting）；None 表示全部。
    """
    stmt = select(KnowledgeItem).where(KnowledgeItem.store_id == store_id)
    if types:
        stmt = stmt.where(KnowledgeItem.type.in_(types))
    items = db.scalars(stmt).all()
    if not items:
        return []

    q_vec = _embed_cached(query)
    scored: list[dict] = []
    for it in items:
        text = f"{it.question or ''}\n{it.answer or ''}"
        it_vec = _embed_cached(text)
        score = _cosine(q_vec, it_vec)
        scored.append({
            "id": it.id,
            "type": it.type,
            "question": it.question,
            "answer": it.answer,
            "keywords": it.keywords,
            "score": round(score, 4),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
