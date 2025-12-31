from typing import Dict, Optional
from .ai_client import AIClient, OpenAIClient, CustomAIClient

class AIFactory:
    @staticmethod
    def create_client(service_type: str, config: Dict) -> Optional[AIClient]:
        """创建AI客户端
        
        Args:
            service_type: 服务类型（openai/custom）
            config: 配置信息
            
        Returns:
            Optional[AIClient]: AI客户端实例
        """
        if service_type == "openai":
            return OpenAIClient(config)
        elif service_type == "custom":
            return CustomAIClient(config)
        return None