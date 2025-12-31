import json
from typing import Dict, Any, Optional
import sys
import os

# 添加vendor目录到Python路径
vendor_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor")
if vendor_dir not in sys.path:
    sys.path.insert(0, vendor_dir)

import aiohttp
from .ai_client import AIClient, AIResponse

class OpenAIClient(AIClient):
    """OpenAI API客户端"""
    
    def __init__(self, config: Dict):
        """初始化OpenAI客户端
        
        Args:
            config: 配置信息
        """
        if aiohttp is None:
            raise ImportError("未能加载aiohttp模块。请确保已正确安装所有依赖。")
            
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        
    async def _make_request(self, messages: list) -> str:
        """发送请求到OpenAI API
        
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
                    "https://api.openai.com/v1/chat/completions",
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
            
    async def translate(self, text: str) -> AIResponse:
        """翻译文本"""
        messages = [
            {"role": "system", "content": "你是一个专业的翻译助手。请将给定的英文文本翻译成中文，保原文的意思和语气。"},
            {"role": "user", "content": f"请翻译以下文本：\n{text}"}
        ]
        
        try:
            response = await self._make_request(messages)
            return AIResponse(
                translation=response,
                explanation="",
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
    
    async def generate_example(self, word: str) -> AIResponse:
        """生成例句"""
        messages = [
            {"role": "system", "content": "你是一个专业的英语教师。请为给定的英文单词生成一个自然、实用的例句，并提供中文翻译。"},
            {"role": "user", "content": f"请为单词 '{word}' 生成一个例句并翻译："}
        ]
        
        try:
            response = await self._make_request(messages)
            return AIResponse(
                translation="",
                explanation="",
                example=response,
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
        if "model" in config:
            self.model = config["model"]
        if "temperature" in config:
            self.temperature = config["temperature"]
        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]