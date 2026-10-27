"""DeepSeek OpenAI 兼容客户端（带熔断）。

Key 读取顺序：DEEPSEEK_API_KEY -> ANTHROPIC_AUTH_TOKEN（用户环境已配置后者）。
"""
import os
import time

import httpx

from ..config import settings


class LLMError(Exception):
    """LLM 调用失败。"""


class LLMClient:
    # 熔断参数：连续失败 N 次后熔断，冷却结束后再试
    FAIL_THRESHOLD = 3
    COOLDOWN_SECONDS = 60

    def __init__(self) -> None:
        self.api_key = settings.deepseek_api_key or os.getenv("ANTHROPIC_AUTH_TOKEN")
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.model = settings.deepseek_model
        self._fail_count = 0
        self._circuit_open_until = 0.0

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _circuit_is_open(self) -> bool:
        return time.monotonic() < self._circuit_open_until

    def _record_failure(self) -> None:
        self._fail_count += 1
        if self._fail_count >= self.FAIL_THRESHOLD:
            self._circuit_open_until = time.monotonic() + self.COOLDOWN_SECONDS
            self._fail_count = 0  # 熔断后重置计数，冷却结束重新试

    def _record_success(self) -> None:
        self._fail_count = 0
        self._circuit_open_until = 0.0

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        json_mode: bool = False,
        max_tokens: int = 800,
    ) -> str:
        if not self.api_key:
            raise LLMError("未配置 DeepSeek API Key（DEEPSEEK_API_KEY / ANTHROPIC_AUTH_TOKEN）")
        if self._circuit_is_open():
            raise LLMError("LLM 熔断中，请稍后再试")

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            self._record_success()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            self._record_failure()
            detail = e.response.text[:200]
            raise LLMError(f"DeepSeek 调用失败 {e.response.status_code}: {detail}") from e
        except httpx.HTTPError as e:
            self._record_failure()
            raise LLMError(f"网络错误: {e}") from e


llm = LLMClient()
