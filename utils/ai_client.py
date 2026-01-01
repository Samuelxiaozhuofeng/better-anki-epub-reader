from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Dict, Optional

from .vendor_path import vendored_sys_path

with vendored_sys_path():
    import aiohttp

@dataclass
class AIResponse:
    explanation: str = ""
    error: Optional[str] = None

class AIClient:
    """AI客户端基类"""
    async def explain(self, prompt: str) -> AIResponse:
        """解释文本
        
        Args:
            prompt: 完整的提示词，包含单词和上下文
            
        Returns:
            AIResponse: 解释结果
        """
        raise NotImplementedError()

    async def explain_stream(
        self,
        prompt: str,
        *,
        cancel_cb: Optional[Callable[[], bool]] = None,
    ) -> AsyncIterator[str]:
        raise NotImplementedError()


def _should_cancel(cancel_cb: Optional[Callable[[], bool]]) -> bool:
    try:
        return bool(cancel_cb and cancel_cb())
    except Exception:
        return False


def _chat_completions_url(api_base: str) -> str:
    base = (api_base or "").strip().rstrip("/")
    if not base:
        base = "https://api.openai.com/v1"
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


async def _sse_stream_chat_completions(
    *,
    session: aiohttp.ClientSession,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    cancel_cb: Optional[Callable[[], bool]] = None,
) -> AsyncIterator[str]:
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status != 200:
            raise Exception(f"API调用失败: {await response.text()}")

        buffer = b""
        async for chunk in response.content.iter_chunked(1024):
            if _should_cancel(cancel_cb):
                raise asyncio.CancelledError()

            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                if not line.startswith(b"data:"):
                    continue
                data = line[len(b"data:") :].strip()
                if data == b"[DONE]":
                    return
                try:
                    obj = json.loads(data.decode("utf-8", errors="replace"))
                except Exception:
                    continue
                try:
                    delta = obj["choices"][0].get("delta", {})
                    text = delta.get("content")
                except Exception:
                    text = None
                if text:
                    yield str(text)

class OpenAIClient(AIClient):
    """OpenAI客户端"""
    def __init__(self, config: Dict):
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "")
        self.model = config.get("model", "gpt-3.5-turbo")
        
    async def explain(self, prompt: str) -> AIResponse:
        if not self.api_key:
            return AIResponse(error="请先配置OpenAI API Key")
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    _chat_completions_url(self.api_base),
                    headers=headers,
                    json=data,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return AIResponse(explanation=result["choices"][0]["message"]["content"])
                    error_msg = await response.text()
                    return AIResponse(error=f"API调用失败: {error_msg}")
                        
        except Exception as e:
            return AIResponse(error=f"请求失败: {str(e)}")

    async def explain_stream(
        self,
        prompt: str,
        *,
        cancel_cb: Optional[Callable[[], bool]] = None,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            raise Exception("请先配置OpenAI API Key")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
        }

        timeout = aiohttp.ClientTimeout(total=120, connect=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async for delta in _sse_stream_chat_completions(
                session=session,
                url=_chat_completions_url(self.api_base),
                headers=headers,
                payload=data,
                cancel_cb=cancel_cb,
            ):
                yield delta

class CustomAIClient(AIClient):
    """自定义AI服务客户端"""
    def __init__(self, config: Dict):
        self.api_base = config.get("api_base", "").rstrip("/")
        self.api_key = config.get("api_key", "")  # optional
        self.model = config.get("model", "")
        
    async def explain(self, prompt: str) -> AIResponse:
        if not self.api_base:
            return AIResponse(error="请先配置自定义API服务")
            
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            api_url = _chat_completions_url(self.api_base)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return AIResponse(
                            explanation=result["choices"][0]["message"]["content"]
                        )
                    else:
                        error_msg = await response.text()
                        return AIResponse(error=f"API调用失败: {error_msg}")
                        
        except Exception as e:
            return AIResponse(error=f"请求失败: {str(e)}")

    async def explain_stream(
        self,
        prompt: str,
        *,
        cancel_cb: Optional[Callable[[], bool]] = None,
    ) -> AsyncIterator[str]:
        if not self.api_base:
            raise Exception("请先配置自定义API服务")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = {
            "model": self.model,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
        }

        timeout = aiohttp.ClientTimeout(total=120, connect=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async for delta in _sse_stream_chat_completions(
                session=session,
                url=_chat_completions_url(self.api_base),
                headers=headers,
                payload=data,
                cancel_cb=cancel_cb,
            ):
                yield delta
