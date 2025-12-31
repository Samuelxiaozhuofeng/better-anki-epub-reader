import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
import tempfile
import os
import time
from functools import lru_cache
from threading import Lock
import urllib.parse
import json

try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

try:
    import lxml
    BS4_PARSER = 'lxml'
except ImportError:
    BS4_PARSER = 'html.parser'

class ImageSearchThread(QThread):
    """异步图片搜索线程"""
    finished = pyqtSignal(list)  # 发送图片路径列表
    error = pyqtSignal(str)     # 发送错误信息
    
    # 类级别的缓存
    _url_cache = {}  # {word: (timestamp, urls)}
    _image_cache = {}  # {url: (timestamp, file_path)}
    CACHE_TIMEOUT = 3600  # 缓存过期时间（秒）
    _cache_lock = Lock()  # 缓存访问锁
    
    def __init__(self, word, max_images=2):
        super().__init__()
        self.word = word
        self.max_images = max_images
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self._loop = None
        self._session = None

    def _clean_old_cache(self):
        """清理过期的缓存"""
        with self._cache_lock:
            current_time = time.time()
            # 清理URL缓存
            expired_words = [word for word, (timestamp, _) in self._url_cache.items()
                            if current_time - timestamp > self.CACHE_TIMEOUT]
            for word in expired_words:
                del self._url_cache[word]
                
            # 清理图片文件缓存
            expired_urls = [url for url, (timestamp, path) in self._image_cache.items()
                        if current_time - timestamp > self.CACHE_TIMEOUT]
            for url in expired_urls:
                path = self._image_cache[url][1]
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass
                del self._image_cache[url]

    async def download_image(self, image_url):
        """异步下载单个图片"""
        # 检查缓存
        with self._cache_lock:
            if image_url in self._image_cache:
                timestamp, file_path = self._image_cache[image_url]
                if time.time() - timestamp <= self.CACHE_TIMEOUT and os.path.exists(file_path):
                    return file_path

        try:
            # 使用已存在的session
            async with self._session.get(image_url, timeout=10) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # 使用URL的最后部分作为文件名
                    url_path = urllib.parse.urlparse(image_url).path
                    file_name = os.path.basename(url_path)
                    if not file_name:
                        file_name = 'image.jpg'
                    elif not file_name.endswith(('.jpg', '.jpeg', '.png')):
                        file_name += '.jpg'
                        
                    # 创建临时文件
                    temp_dir = tempfile.gettempdir()
                    file_path = os.path.join(temp_dir, f"anki_reader_{int(time.time())}_{file_name}")
                    
                    # 根据是否有 aiofiles 选择文件写入方式
                    if HAS_AIOFILES:
                        async with aiofiles.open(file_path, 'wb') as f:
                            await f.write(content)
                    else:
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                    # 更新缓存
                    with self._cache_lock:
                        self._image_cache[image_url] = (time.time(), file_path)
                    return file_path
                    
        except Exception as e:
            print(f"Error downloading image {image_url}: {str(e)}")
        return None

    async def download_all_images(self, image_urls):
        """并发下载所有图片"""
        tasks = [self.download_image(url) for url in image_urls]
        results = await asyncio.gather(*tasks)
        return [path for path in results if path]

    async def fetch_image_urls(self):
        """异步获取图片URL列表"""
        search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(self.word)}&first=1"
        
        try:
            async with self._session.get(search_url, timeout=10) as response:
                if response.status != 200:
                    return []
                    
                html = await response.text()
                soup = BeautifulSoup(html, BS4_PARSER)  # 使用可用的最佳解析器
                image_elements = soup.find_all('a', class_='iusc')
                image_urls = []
                
                for element in image_elements:
                    if len(image_urls) >= self.max_images:
                        break
                        
                    if element and 'm' in element.attrs:
                        try:
                            image_data = json.loads(element['m'])  # 使用json.loads替代eval
                            image_urls.append(image_data['murl'])
                        except Exception as e:
                            print(f"Error parsing image data: {str(e)}")
                            continue
                
                # 确保只返回指定数量的URL
                image_urls = image_urls[:self.max_images]
                
                # 更新缓存
                if image_urls:
                    with self._cache_lock:
                        self._url_cache[self.word] = (time.time(), image_urls)
                
                return image_urls
        except Exception as e:
            print(f"Error fetching image URLs: {str(e)}")
            return []

    def _get_cached_urls(self):
        """获取缓存的URL列表"""
        with self._cache_lock:
            if self.word in self._url_cache:
                timestamp, urls = self._url_cache[self.word]
                if time.time() - timestamp <= self.CACHE_TIMEOUT:
                    return urls[:self.max_images]
        return None

    async def process_images(self):
        """处理图片搜索和下载的主要异步函数"""
        # 创建一个持久的aiohttp会话，配置更大的连接池
        connector = aiohttp.TCPConnector(limit=20, force_close=False, enable_cleanup_closed=True)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(headers=self.headers, connector=connector, timeout=timeout) as session:
            self._session = session
            
            # 尝试从缓存获取URL
            image_urls = self._get_cached_urls()
            
            # 如果缓存未命中，从Bing获取
            if not image_urls:
                image_urls = await self.fetch_image_urls()

            if not image_urls:
                return []

            # 下载所有图片
            return await self.download_all_images(image_urls)

    def run(self):
        try:
            # 清理过期缓存
            self._clean_old_cache()
            
            # 创建事件循环
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            try:
                # 执行异步操作
                image_paths = self._loop.run_until_complete(self.process_images())
                
                if image_paths:
                    self.finished.emit(image_paths)
                else:
                    self.error.emit("No images found")
                    
            finally:
                self._loop.close()
                self._loop = None
                
        except Exception as e:
            self.error.emit(str(e))

class ImageHandler:
    """处理图片搜索和显示的类"""
    
    @staticmethod
    def search_image(word, callback, error_callback, max_images=2):
        """
        搜索图片
        :param word: 要搜索的单词
        :param callback: 成功回调函数
        :param error_callback: 错误回调函数
        :param max_images: 最大图片数量
        """
        thread = ImageSearchThread(word, max_images)
        thread.finished.connect(callback)
        thread.error.connect(error_callback)
        thread.start()
        return thread  # 返回线程对象以保持引用

    @staticmethod
    def load_image(image_path, max_size=300):
        """
        加载图片并调整大小
        :param image_path: 图片路径
        :param max_size: 最大尺寸
        :return: QPixmap对象
        """
        pixmap = QPixmap(image_path)
        if pixmap.width() > max_size or pixmap.height() > max_size:
            pixmap = pixmap.scaled(
                max_size, 
                max_size, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        return pixmap
