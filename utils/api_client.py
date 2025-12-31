import json
import urllib.request
from ..config.config import Config

class OpenAIClient:
    """OpenAI API客户端"""
    
    @staticmethod
    async def translate_text(text):
        """翻译文本"""
        # TODO: 实现OpenAI API调用
        pass
    
    @staticmethod
    async def get_word_info(word):
        """获取单词信息"""
        # TODO: 实现单词信息查询
        pass

class AnkiConnectClient:
    """AnkiConnect API客户端"""
    
    @staticmethod
    def invoke(action, **params):
        """调用AnkiConnect API"""
        request = json.dumps({
            "action": action,
            "version": 6,
            "params": params
        }).encode('utf-8')
        
        response = json.load(urllib.request.urlopen(urllib.request.Request(
            f'http://localhost:{Config.ANKI_CONNECT_PORT}',
            request,
            headers={'Content-Type': 'application/json'}
        )))
        
        if len(response) != 2:
            raise Exception('response has an unexpected number of fields')
        
        if 'error' not in response:
            raise Exception('response is missing required error field')
        
        if 'result' not in response:
            raise Exception('response is missing required result field')
        
        if response['error'] is not None:
            raise Exception(response['error'])
        
        return response['result']
    
    @classmethod
    def create_note(cls, deck_name, model_name, fields):
        """创建Anki笔记"""
        return cls.invoke('addNote', note={
            'deckName': deck_name,
            'modelName': model_name,
            'fields': fields,
            'options': {
                'allowDuplicate': False
            },
            'tags': ['anki_reader']
        }) 