from aqt import mw
from anki.notes import Note
from typing import Optional, Dict, Any, List
from aqt.qt import QMessageBox
import os
import json

from .paths import note_config_path

class AnkiHandler:
    def __init__(self):
        self.collection = mw.col
        self.config_path = note_config_path()
    
    def get_note_config(self) -> Dict[str, Any]:
        """获取笔记配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            "deck_name": "Default",
            "model_name": "Basic",
            "field_mapping": {
                "word": "Front",
                "meaning": "Back",
                "context": "Back"
            },
            "tags": []
        }
    
    def get_model_fields(self, model_name: str) -> List[str]:
        """获取笔记类型的所有字段名称"""
        model = self.collection.models.by_name(model_name)
        if not model:
            return []
        return [field['name'] for field in model['flds']]
    
    def add_note(self, 
                word: str, 
                meaning: str, 
                context: Optional[str] = None, 
                deck_name: Optional[str] = None,
                model_name: Optional[str] = None,
                field_mapping: Optional[Dict[str, str]] = None,
                tags: Optional[list] = None) -> bool:
        """
        添加笔记到Anki
        
        Args:
            word: 单词
            meaning: 释义
            context: 上下文（可选）
            deck_name: 牌组名称（可选，如果不指定则使用配置）
            model_name: 卡片模板名称（可选，如果不指定则使用配置）
            field_mapping: 字段映射（可选，如果不指定则使用配置）
            tags: 标签列表（可选，如果不指定则使用配置）
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 获取配置
            config = self.get_note_config()
            
            # 使用参数值或配置值
            deck_name = deck_name or config["deck_name"]
            model_name = model_name or config["model_name"]
            field_mapping = field_mapping or config["field_mapping"]
            tags = tags or config.get("tags", [])
            
            # 获取或创建牌组
            deck_id = self.collection.decks.id(deck_name)
            self.collection.decks.select(deck_id)
            
            # 获取卡片模板
            model = self.collection.models.by_name(model_name)
            if not model:
                raise Exception(f"找不到卡片模板：{model_name}")
            
            # 创建新笔记
            note = Note(self.collection, model)
            
            # 设置字段内容
            fields = self.get_model_fields(model_name)
            for field in fields:
                note.fields[fields.index(field)] = ""  # 初始化所有字段为空
                
            # 设置单词
            if "word" in field_mapping and field_mapping["word"] in fields:
                note.fields[fields.index(field_mapping["word"])] = word
                
            # 设置释义和上下文
            meaning_content = meaning
            if context and "context" in field_mapping and field_mapping["context"] == field_mapping["meaning"]:
                meaning_content += f"\n\n上下文：\n{context}"
                
            if "meaning" in field_mapping and field_mapping["meaning"] in fields:
                note.fields[fields.index(field_mapping["meaning"])] = meaning_content
                
            # 如果上下文字段单独设置
            if context and "context" in field_mapping and field_mapping["context"] != field_mapping["meaning"]:
                if field_mapping["context"] in fields:
                    note.fields[fields.index(field_mapping["context"])] = context
            
            # 添加标签
            if tags:
                note.tags = tags
            
            # 添加笔记
            self.collection.add_note(note, deck_id)
            
            return True
            
        except Exception as e:
            QMessageBox.warning(None, "错误", f"添加笔记失败：{str(e)}")
            return False
    
    def get_all_decks(self) -> List[str]:
        """获取所有牌组名称"""
        decks = self.collection.decks.all_names_and_ids()
        return [deck.name for deck in decks]
    
    def get_all_models(self) -> List[str]:
        """获取所有卡片模板名称"""
        models = self.collection.models.all_names_and_ids()
        return [model.name for model in models] 
