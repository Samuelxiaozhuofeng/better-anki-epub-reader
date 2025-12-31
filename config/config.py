class Config:
    """插件配置类"""
    
    # OpenAI API配置
    OPENAI_API_KEY = ""
    OPENAI_MODEL = "gpt-3.5-turbo"
    
    # Anki Connect配置
    ANKI_CONNECT_PORT = 8765
    
    # UI配置
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    
    # 卡片模板配置
    DEFAULT_CARD_TEMPLATE = {
        "front": "{{Word}}",
        "back": """
            {{Translation}}<br>
            {{Example}}<br>
        """
    }
    
    @classmethod
    def load(cls):
        """加载配置"""
        # TODO: 从配置文件加载用户配置
        pass
    
    @classmethod
    def save(cls):
        """保存配置"""
        # TODO: 保存配置到文件
        pass 