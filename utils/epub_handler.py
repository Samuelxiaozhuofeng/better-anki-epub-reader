import os
import sys
from typing import Dict, List, Optional
import zipfile
import xml.etree.ElementTree as ET
from aqt import mw

from .vendor_path import vendored_sys_path

with vendored_sys_path():
    from bs4 import BeautifulSoup

class EPUBHandler:
    def __init__(self):
        self.current_book = None
        self.chapters = []
        self.metadata = {}
        
    def load_book(self, file_path: str) -> bool:
        """加载EPUB文件
        
        Args:
            file_path: EPUB文件路径
            
        Returns:
            bool: 是否成功加载
        """
        try:
            self.current_book = zipfile.ZipFile(file_path)
            self._extract_metadata()
            self._extract_chapters()
            return True
        except Exception as e:
            print(f"加载EPUB文件失败: {str(e)}")
            return False
            
    def _extract_metadata(self) -> None:
        """提取书籍元数据"""
        if not self.current_book:
            return
            
        try:
            # 读取container.xml找到content.opf
            container = self.current_book.read('META-INF/container.xml')
            container_tree = ET.fromstring(container)
            rootfile = container_tree.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
            content_path = rootfile.get('full-path')
            
            # 读取content.opf
            content = self.current_book.read(content_path)
            content_tree = ET.fromstring(content)
            
            # 定义命名空间
            namespaces = {
                'dc': 'http://purl.org/dc/elements/1.1/',
                'opf': 'http://www.idpf.org/2007/opf'
            }
            
            # 提取元数据
            metadata = content_tree.find('.//{http://www.idpf.org/2007/opf}metadata')
            if metadata is not None:
                # 获取标题
                title = metadata.find('.//dc:title', namespaces)
                title_text = title.text if title is not None else '未知标题'
                
                # 获取作者
                creator = metadata.find('.//dc:creator', namespaces)
                creator_text = creator.text if creator is not None else '未知作者'
                
                # 获取语言
                language = metadata.find('.//dc:language', namespaces)
                language_text = language.text if language is not None else 'zh'
                
                # 获取标识符
                identifier = metadata.find('.//dc:identifier', namespaces)
                identifier_text = identifier.text if identifier is not None else ''
                
                # 获取描述
                description = metadata.find('.//dc:description', namespaces)
                description_text = description.text if description is not None else ''
                
                self.metadata = {
                    'title': title_text,
                    'creator': creator_text,
                    'language': language_text,
                    'identifier': identifier_text,
                    'description': description_text
                }
                
                print(f"提取到的元数据: {self.metadata}")
            else:
                print("未找到metadata元素")
                self.metadata = {
                    'title': '未知标题',
                    'creator': '未知作者',
                    'language': 'zh',
                    'identifier': '',
                    'description': ''
                }
                
        except Exception as e:
            print(f"提取元数据失败: {str(e)}")
            self.metadata = {
                'title': '未知标题',
                'creator': '未知作者',
                'language': 'zh',
                'identifier': '',
                'description': ''
            }
            
    def _get_metadata_text(self, tree: ET.Element, tag: str) -> str:
        """获取元数据文本
        
        Args:
            tree: XML元素树
            tag: 标签名
            
        Returns:
            str: 元数据文本
        """
        namespaces = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf'
        }
        
        try:
            # 首先尝试使用命名空间查找
            elem = tree.find(f'.//dc:{tag}', namespaces)
            if elem is not None:
                return elem.text or ''
                
            # 如果找不到，尝试不使用命名空间
            elem = tree.find(f'.//{{{http://purl.org/dc/elements/1.1/}}}{tag}')
            if elem is not None:
                return elem.text or ''
                
            return ''
        except Exception as e:
            print(f"获取元数据 {tag} 失败: {str(e)}")
            return ''
            
    def _extract_chapters(self) -> None:
        """提取章节内容"""
        if not self.current_book:
            return
            
        try:
            print("开始提取章节...")
            # 读取content.opf找到spine和manifest
            container = self.current_book.read('META-INF/container.xml')
            container_tree = ET.fromstring(container)
            rootfile = container_tree.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
            content_path = rootfile.get('full-path')
            content_dir = os.path.dirname(content_path)
            print(f"content.opf路径: {content_path}")
            
            content = self.current_book.read(content_path)
            content_tree = ET.fromstring(content)
            
            # 定义命名空间
            namespaces = {
                'dc': 'http://purl.org/dc/elements/1.1/',
                'opf': 'http://www.idpf.org/2007/opf'
            }
            
            # 获取spine顺序
            spine = content_tree.find('.//{http://www.idpf.org/2007/opf}spine')
            manifest = content_tree.find('.//{http://www.idpf.org/2007/opf}manifest')
            
            if spine is None or manifest is None:
                print("未找到spine或manifest元素")
                return
            
            # 清空现有章节列表
            self.chapters = []
                
            # 按spine顺序提取章节
            for itemref in spine.findall('.//{http://www.idpf.org/2007/opf}itemref'):
                idref = itemref.get('idref')
                item = manifest.find(f'.//*[@id="{idref}"]')
                if item is not None:
                    href = item.get('href')
                    file_path = os.path.join(content_dir, href).replace('\\', '/')
                    try:
                        print(f"正在提取章节: {file_path}")
                        chapter_content = self.current_book.read(file_path).decode('utf-8')
                        
                        # 解析HTML以获取章节标题
                        soup = BeautifulSoup(chapter_content, 'html.parser')
                        chapter_title = None
                        
                        # 尝试从h1-h6标签获取标题
                        for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                            if h.text.strip():
                                chapter_title = h.text.strip()
                                break
                        
                        # 如果没有找到标题，尝试从title标签获取
                        if not chapter_title:
                            title_tag = soup.find('title')
                            if title_tag and title_tag.text.strip():
                                chapter_title = title_tag.text.strip()
                        
                        # 如果还是没有找到标题，使用文件名
                        if not chapter_title:
                            chapter_title = os.path.splitext(os.path.basename(href))[0]
                            # 美化文件名（去除数字前缀等）
                            chapter_title = chapter_title.replace('_', ' ').replace('-', ' ')
                            chapter_title = ' '.join(word.capitalize() for word in chapter_title.split())
                        
                        cleaned_content = self._clean_html(chapter_content)
                        if not cleaned_content.strip():
                            print(f"警告：章节内容为空: {file_path}")
                            continue
                            
                        self.chapters.append({
                            'id': idref,
                            'name': chapter_title,
                            'content': cleaned_content
                        })
                        print(f"成功提取章节: {chapter_title}, 内容长度: {len(cleaned_content)}")
                    except Exception as e:
                        print(f"提取章节失败 {href}: {str(e)}")
                        
        except Exception as e:
            print(f"提取章节失败: {str(e)}")
                
    def _clean_html(self, html_content: str) -> str:
        """清理HTML内容，保留格式
        
        Args:
            html_content: HTML内容
            
        Returns:
            str: 清理后的HTML
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 只移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()
                
            # 添加基本的CSS样式
            style_tag = soup.new_tag('style')
            style_tag.string = """
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 1em;
                    color: #333;
                }
                p {
                    margin: 0.8em 0;
                }
                h1, h2, h3, h4, h5, h6 {
                    margin: 1em 0 0.5em;
                    color: #222;
                }
                img {
                    max-width: 100%;
                    height: auto;
                }
            """
            
            # 如果没有head标签，创建一个
            if not soup.head:
                head = soup.new_tag('head')
                soup.html.insert(0, head)
            
            # 添加样式标签到head中
            soup.head.append(style_tag)
            
            # 确保有body标签
            if not soup.body:
                content = soup.find('body')
                if not content:
                    content = soup
                new_body = soup.new_tag('body')
                for tag in content.contents:
                    new_body.append(tag)
                if soup.html:
                    soup.html.append(new_body)
                else:
                    html = soup.new_tag('html')
                    html.append(new_body)
                    soup.append(html)
            
            # 返回格式化的HTML
            return str(soup)
            
        except Exception as e:
            print(f"清理HTML内容失败: {str(e)}")
            return html_content  # 如果处理失败，返回原始内容
        
    def get_chapter_count(self) -> int:
        """获取章节数量"""
        return len(self.chapters)
        
    def get_chapter_content(self, index: int) -> Optional[str]:
        """获取指定章节的内容
        
        Args:
            index: 章节索引
            
        Returns:
            Optional[str]: 章节内容
        """
        if 0 <= index < len(self.chapters):
            return self.chapters[index]['content']
        return None
        
    def get_metadata(self) -> Dict:
        """获取书籍元数据
        
        Returns:
            Dict: 元数据字典
        """
        return self.metadata
        
    def get_chapter_titles(self) -> List[str]:
        """获取所有章节标题
        
        Returns:
            List[str]: 章节标题列表
        """
        return [chapter['name'] for chapter in self.chapters] 
