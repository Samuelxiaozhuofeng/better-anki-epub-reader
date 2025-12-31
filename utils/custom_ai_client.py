import json
from typing import Dict, Any
import aiohttp
from .ai_client import AIClient, AIResponse

class CustomAIClient(AIClient):
    """自定义API客户端"""
    
    def __init__(self, config: Dict):
        """初始化自定义API客户端
        
        Args:
            config: 配置信息
        """
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "").rstrip('/')
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        
    async def _make_request(self, messages: list) -> str:
        """发送请求到自定义API
        
        Args:
            messages: 消息列表
            
        Returns:
            str: API响应
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {error_text}")
                        
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                    
        except Exception as e:
            raise Exception(f"API请求失败: {str(e)}")
    
    async def explain(self, prompt: str) -> AIResponse:
        """解释单词
        
        Args:
            prompt: 完整的提示词，包含单词和上下文
        """
        messages = [
            {"role": "system", "content": "You are a professional Language teacher. Please explain the word strictly according to the user's prompt."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self._make_request(messages)
            return AIResponse(
                translation="",
                explanation=response,
                example="",
                error=None
            )
        except Exception as e:
            return AIResponse(
                translation="",
                explanation="",
                example="",
                error=str(e)
            )
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新配置"""
        if "api_key" in config:
            self.api_key = config["api_key"]
        if "api_base" in config:
            self.api_base = config["api_base"].rstrip('/')
        if "model" in config:
            self.model = config["model"]
        if "temperature" in config:
            self.temperature = config["temperature"]
        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]