from typing import Dict, Optional
import json
import os

from .paths import templates_path

class TemplateManager:
    def __init__(self, template_file: str = "templates.json"):
        """初始化模板管理器"""
        # 使用统一的配置文件
        self.config_file = templates_path()
        
        # 默认模板
        self.default_templates = {
            "word_definition": {
                "name": "基础释义模板",
                "template": "你是语言老师。请用中文、简洁输出，并结合上下文说明该词汇的语境义。",
                "is_default": True
            }
        }
        
        # 加载保存的模板
        self.templates = self._load_templates()
        
        # 加载当前使用的模板ID
        self.current_template_id = self._load_current_template_id()
    
    def _load_current_template_id(self) -> str:
        """加载当前使用的模板ID"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if isinstance(config, dict) and "word_definition" in config:
                        # 从配置中获取当前模板ID
                        return config.get("current_template_id", "default")
            return "default"
        except Exception:
            return "default"
    
    def _save_current_template_id(self, template_id: str) -> None:
        """保存当前使用的模板ID"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新当前模板ID
            config["current_template_id"] = template_id
            
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存当前模板ID失败: {str(e)}")
    
    def set_current_template(self, template_id: str) -> bool:
        """设置当前使用的模板"""
        try:
            self.current_template_id = template_id
            self._save_current_template_id(template_id)
            return True
        except Exception as e:
            print(f"设置当前模板失败: {str(e)}")
            return False
    
    def _load_templates(self) -> dict:
        """从文件加载模板"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if isinstance(config, dict) and "word_definition" in config:
                        return {"word_definition": config["word_definition"]}
            return {}
        except Exception:
            return {}
    
    def _save_templates(self) -> None:
        """保存模板到文件"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新模板数据
            config["word_definition"] = self.templates.get("word_definition", {})
            
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存模板失败: {str(e)}")
    
    def list_templates(self, template_type: str) -> dict:
        """列出指定类型的所有模板"""
        templates = {}
        
        # 添加默认模板
        if template_type in self.default_templates:
            templates["default"] = self.default_templates[template_type]
        
        # 添加自定义模板
        custom_templates = self.templates.get(template_type, {})
        if isinstance(custom_templates, dict):
            for template_id, template in custom_templates.items():
                if isinstance(template, str):
                    # 如果是旧格式（字符串），转换为新格式（字典）
                    templates[template_id] = {
                        "name": template_id.replace(f"{template_type}_", "模板 "),
                        "template": template,
                        "is_default": False
                    }
                else:
                    # 如果已经是字典格式，直接使用
                    templates[template_id] = template
        
        return templates
    
    def get_template(self, template_type: str, template_id: str = None) -> str:
        """获取模板内容"""
        try:
            # 如果没有指定模板ID，返回默认模板
            if template_id is None or template_id == "default":
                return self.default_templates[template_type]["template"]
            
            # 获取自定义模板
            if (template_type in self.templates and 
                template_id in self.templates[template_type]):
                template = self.templates[template_type][template_id]
                # 确保返回字符串类型
                if isinstance(template, dict) and "template" in template:
                    return template["template"]
                elif isinstance(template, str):
                    return template
            
            # 如果找不到指定模板，返回默认模板
            return self.default_templates[template_type]["template"]
        except Exception as e:
            print(f"获取模板失败: {str(e)}")
            return self.default_templates[template_type]["template"]
    
    def add_template(self, template_type: str, name: str, template: str, template_id: str = None) -> bool:
        """添加或更新模板"""
        try:
            if template_type not in self.templates:
                self.templates[template_type] = {}
            
            if template_id is None:
                # 生成新的唯一模板ID
                counter = 1
                while True:
                    new_id = f"{template_type}_{counter}"
                    if new_id not in self.templates[template_type]:
                        template_id = new_id
                        break
                    counter += 1
            
            # 保存模板为字典格式
            self.templates[template_type][template_id] = {
                "name": name,
                "template": template,
                "is_default": False
            }
            
            self._save_templates()
            return True
        except Exception as e:
            print(f"添加模板失败: {str(e)}")
            return False
    
    def delete_template(self, template_type: str, template_id: str) -> bool:
        """删除模板"""
        try:
            if (template_type in self.templates and 
                template_id in self.templates[template_type]):
                del self.templates[template_type][template_id]
                self._save_templates()
                return True
            return False
        except Exception as e:
            print(f"删除模板失败: {str(e)}")
            return False 
