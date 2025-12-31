import re
from typing import Tuple, List

class TextContextExtractor:
    @staticmethod
    def get_sentence_boundaries(text: str, cursor_pos: int) -> Tuple[int, int]:
        """
        获取光标所在句子的边界
        
        Args:
            text: 完整文本
            cursor_pos: 光标位置
            
        Returns:
            Tuple[int, int]: 句子的开始和结束位置
        """
        # 使用正则表达式匹配句子边界
        sentence_endings = r'[.!?。！？]+'
        sentences = re.split(f'({sentence_endings}\\s*)', text)
        
        current_pos = 0
        for i in range(0, len(sentences), 2):
            # 计算当前句子的长度（包括句号和空白）
            sentence_length = len(sentences[i])
            if i + 1 < len(sentences):
                sentence_length += len(sentences[i + 1])
                
            if current_pos <= cursor_pos < current_pos + sentence_length:
                # 找到光标所在的句子
                start = current_pos
                end = current_pos + sentence_length
                return start, end
                
            current_pos += sentence_length
            
        return 0, len(text)
    
    @staticmethod
    def get_all_sentence_boundaries(text: str) -> List[Tuple[int, int]]:
        """
        获取文本中所有句子的边界
        
        Args:
            text: 完整文本
            
        Returns:
            List[Tuple[int, int]]: 所有句子的开始和结束位置列表
        """
        sentence_endings = r'[.!?。！？]+'
        sentences = re.split(f'({sentence_endings}\\s*)', text)
        
        boundaries = []
        current_pos = 0
        for i in range(0, len(sentences), 2):
            sentence_length = len(sentences[i])
            if i + 1 < len(sentences):
                sentence_length += len(sentences[i + 1])
            
            boundaries.append((current_pos, current_pos + sentence_length))
            current_pos += sentence_length
            
        return boundaries
    
    @staticmethod
    def get_context(text: str, cursor_pos: int, include_adjacent: bool = False, adjacent_count: int = 1) -> str:
        """
        获取上下文
        
        Args:
            text: 完整文本
            cursor_pos: 光标位置
            include_adjacent: 是否包含相邻句子
            adjacent_count: 需要包含的前后句子数量，默认为1（即前一句和后一句）
            
        Returns:
            str: 上下文文本
        """
        if not text:
            return ""
            
        # 获取所有句子边界
        all_boundaries = TextContextExtractor.get_all_sentence_boundaries(text)
        if not all_boundaries:
            return text.strip()
            
        # 找到当前句子的索引
        current_index = -1
        for i, (start, end) in enumerate(all_boundaries):
            if start <= cursor_pos < end:
                current_index = i
                break
                
        if current_index == -1:
            return text.strip()
            
        if not include_adjacent:
            # 只返回当前句子
            start, end = all_boundaries[current_index]
            context = text[start:end].strip()
            print(f"返回当前句子: {context}")
            return context
            
        # 获取前后句子
        start_index = max(0, current_index - adjacent_count)
        end_index = min(len(all_boundaries) - 1, current_index + adjacent_count)
        
        start = all_boundaries[start_index][0]
        end = all_boundaries[end_index][1]
        
        context = text[start:end].strip()
        print(f"返回{adjacent_count}句上下文: {context}")
        print(f"包含句子数量: 前{current_index - start_index}句 + 当前句 + 后{end_index - current_index}句")
        return context 