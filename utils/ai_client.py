from typing import Dict, Optional
from dataclasses import dataclass
import aiohttp

@dataclass
class AIResponse:
    explanation: str = ""
    error: str = ""

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

class OpenAIClient(AIClient):
    """OpenAI客户端"""
    def __init__(self, config: Dict):
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gpt-3.5-turbo")
        
    async def explain(self, prompt: str) -> AIResponse:
        if not self.api_key:
            return AIResponse(error="请先配置OpenAI API Key")
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
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

class CustomAIClient(AIClient):
    """自定义AI服务客户端"""
    def __init__(self, config: Dict):
        self.endpoint = config.get("endpoint", "").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "")
        
    async def explain(self, prompt: str) -> AIResponse:
        if not self.endpoint or not self.api_key:
            return AIResponse(error="请先配置自定义API服务")
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            api_url = f"{self.endpoint}/chat/completions"
            
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