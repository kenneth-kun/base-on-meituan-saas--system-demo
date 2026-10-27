"""Embedding Provider —— 与 PlatformAdapter 同构的「可替换嵌入底座」。

骨架阶段默认 LocalEmbeddingProvider（离线、零依赖、jieba 分词 + 哈希词袋），
可直接跑通 RAG 检索；生产环境通过配置切换到 OpenAI 兼容的 embedding 接口。
业务层只依赖 EmbeddingProvider 接口，不关心底层是本地还是云端模型。
"""
from __future__ import annotations

import hashlib
import logging
import math
from abc import ABC, abstractmethod

import jieba

# 抑制 jieba 加载词典的 DEBUG 日志
try:
    jieba.setLogLevel(logging.INFO)
except Exception:  # pragma: no cover
    pass


class EmbeddingProvider(ABC):
    """统一嵌入接口，业务层只依赖它。"""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量将文本转为向量。"""

    @property
    def dim(self) -> int:
        return 0


class LocalEmbeddingProvider(EmbeddingProvider):
    """离线词袋嵌入：jieba 分词 + 字符 bigram，哈希到固定维度，TF 加权 + L2 归一。

    不依赖任何外部服务/模型，可在骨架阶段直接跑；对中文 FAQ/话术检索效果明显优于子串匹配
    （支持同词共现、字符重叠、词序无关），且是可平滑替换为真实 embedding 模型的 RAG 管线。
    """

    def __init__(self, dim: int = 1024) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    @staticmethod
    def _tokens(text: str) -> list[str]:
        text = (text or "").lower()
        # 1) jieba 中文分词
        tokens = list(jieba.cut(text))
        # 2) 字符 bigram：补充中文近义/错字/词序容错
        cleaned = "".join(ch for ch in text if not ch.isspace())
        for i in range(len(cleaned) - 1):
            tokens.append("##" + cleaned[i:i + 2])
        return [t for t in tokens if t.strip()]

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for tok in self._tokens(text):
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if (h & 1) == 0 else -1.0  # 带符号，区分词共现方向
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """生产用：调用 OpenAI 兼容 /v1/embeddings（如真实 embedding 模型）。

    需配置 EMBEDDING_BASE_URL / EMBEDDING_API_KEY / EMBEDDING_MODEL。
    """

    def __init__(self, base_url: str, api_key: str, model: str, dim: int = 1536) -> None:
        import httpx

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._dim = dim
        self._client = httpx.Client(timeout=30.0)

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "input": texts},
        )
        resp.raise_for_status()
        return [d["embedding"] for d in resp.json()["data"]]


def _build_provider() -> EmbeddingProvider:
    from ..config import settings

    if getattr(settings, "embedding_provider", "local") == "openai":
        return OpenAICompatibleEmbeddingProvider(
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key or "",
            model=settings.embedding_model,
            dim=settings.embedding_dim,
        )
    return LocalEmbeddingProvider(dim=getattr(settings, "embedding_dim", 1024))


# 单例：随配置切换，其余模块统一从本模块导入
embedding_provider = _build_provider()
