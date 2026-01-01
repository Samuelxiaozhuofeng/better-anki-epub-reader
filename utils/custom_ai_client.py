import json
from typing import Dict, Any

from .vendor_path import vendored_sys_path

with vendored_sys_path():
    import aiohttp
from .ai_client import AIClient, AIResponse

class CustomAIClient(AIClient):
    """自定义API客户端 - 支持兼容 OpenAI 格式的 API（包括 Gemini、LMStudio 等）"""
    
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
        
        # 调试信息
        print(f"[CustomAIClient] 初始化配置:")
        print(f"  API Base: {self.api_base}")
        print(f"  Model: {self.model}")
        
    async def _make_request(self, messages: list) -> str:
        """发送请求到自定义API
        
        Args:
            messages: 消息列表
            
        Returns:
            str: API响应
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        # 只在有 API key 时添加 Authorization header
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # 构建请求数据 - 只包含必要的字段
        data = {
            "model": self.model,
            "messages": messages
        }
        
        # 只在非默认值时添加可选参数
        if self.temperature != 0.7:
            data["temperature"] = self.temperature
        if self.max_tokens != 2000:
            data["max_tokens"] = self.max_tokens
        
        # 构建完整的 API URL
        api_url = f"{self.api_base}/chat/completions"
        
        print(f"[CustomAIClient] 发送请求到: {api_url}")
        print(f"[CustomAIClient] 使用模型: {self.model}")
        
        try:
            # 设置合理的超时
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=data
                ) as response:
                    response_text = await response.text()
                    
                    # 详细的错误处理
                    if response.status != 200:
                        print(f"[CustomAIClient] API 返回错误状态: {response.status}")
                        print(f"[CustomAIClient] 错误响应: {response_text}")
                        raise Exception(f"API调用失败: {response_text}")
                    
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        print(f"[CustomAIClient] JSON 解析失败: {str(e)}")
                        print(f"[CustomAIClient] 原始响应: {response_text}")
                        raise Exception(f"API响应格式错误: {str(e)}")
                    
                    # 检查响应结构
                    if "choices" not in result or len(result["choices"]) == 0:
                        print(f"[CustomAIClient] 响应缺少 choices 字段: {result}")
                        raise Exception("API响应格式错误: 缺少 choices 字段")
                    
                    if "message" not in result["choices"][0]:
                        print(f"[CustomAIClient] 响应缺少 message 字段: {result}")
                        raise Exception("API响应格式错误: 缺少 message 字段")
                    
                    content = result["choices"][0]["message"]["content"]
                    print(f"[CustomAIClient] 成功获取响应 (长度: {len(content)})")
                    return content
                    
        except aiohttp.ClientConnectorError as e:
            print(f"[CustomAIClient] 连接错误: {str(e)}")
            raise Exception(f"无法连接到 API 服务器: {str(e)}")
        except aiohttp.ClientTimeout as e:
            print(f"[CustomAIClient] 请求超时: {str(e)}")
            raise Exception(f"API请求超时: {str(e)}")
        except Exception as e:
            # 如果已经是我们自己抛出的异常，直接传递
            if "API调用失败" in str(e) or "API响应格式错误" in str(e) or "无法连接" in str(e) or "请求超时" in str(e):
                raise
            # 否则包装为通用错误
            print(f"[CustomAIClient] 未知错误: {str(e)}")
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
            print(f"[CustomAIClient] 开始解释请求")
            response = await self._make_request(messages)
            return AIResponse(
                explanation=response,
                error=None
            )
        except Exception as e:
            error_msg = str(e)
            print(f"[CustomAIClient] 解释请求失败: {error_msg}")
            return AIResponse(
                explanation="",
                error=error_msg
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
