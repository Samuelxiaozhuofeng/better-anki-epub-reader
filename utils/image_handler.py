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
import html
import re

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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.bing.com/",
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
                    content_type = (response.headers.get("Content-Type") or "").lower()
                    if content_type and not content_type.startswith("image/"):
                        return None
                    content = await response.read()
                    if not content or len(content) < 128:
                        return None
                    
                    # 使用URL的最后部分作为文件名
                    url_path = urllib.parse.urlparse(image_url).path
                    file_name = os.path.basename(url_path)
                    if not file_name:
                        file_name = 'image.jpg'
                    elif not file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
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
        # Prefer stable JSON sources first (Wikimedia/Wikipedia). Fall back to Bing HTML only if needed.
        wikimedia_urls = await self.fetch_wikimedia_image_urls()
        if wikimedia_urls:
            with self._cache_lock:
                self._url_cache[self.word] = (time.time(), wikimedia_urls[: self.max_images])
            return wikimedia_urls[:self.max_images]

        search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(self.word)}&first=1"
        
        try:
            async with self._session.get(search_url, timeout=10) as response:
                if response.status != 200:
                    return []
                    
                html = await response.text()
                soup = BeautifulSoup(html, BS4_PARSER)  # 使用可用的最佳解析器

                image_urls = []

                # Strategy 1: parse anchors with embedded JSON metadata (legacy Bing layout)
                image_elements = soup.find_all("a", class_="iusc")
                for element in image_elements:
                    if element and "m" in element.attrs:
                        try:
                            raw = html.unescape(element["m"])
                            image_data = json.loads(raw)
                            url = image_data.get("murl")
                            if isinstance(url, str) and url.startswith(("http://", "https://")):
                                image_urls.append(url)
                        except Exception as e:
                            print(f"Error parsing image data: {str(e)}")

                # Strategy 2: regex fallback for `"murl":"..."` (more robust to minor markup changes)
                if not image_urls:
                    for match in re.finditer(r'"murl"\s*:\s*"([^"]+)"', html):
                        url = match.group(1)
                        if isinstance(url, str) and url.startswith(("http://", "https://")):
                            image_urls.append(url)

                # Strategy 3: img tags with direct src/data-src (fallback)
                if not image_urls:
                    for img in soup.find_all("img"):
                        for attr in ("data-src", "data-original", "src"):
                            url = img.get(attr)
                            if isinstance(url, str) and url.startswith(("http://", "https://")):
                                image_urls.append(url)
                                break

                # Deduplicate while preserving order, then cap
                deduped = []
                seen = set()
                for url in image_urls:
                    if url not in seen:
                        seen.add(url)
                        deduped.append(url)
                    if len(deduped) >= self.max_images:
                        break
                image_urls = deduped
                
                # 更新缓存
                if image_urls:
                    with self._cache_lock:
                        self._url_cache[self.word] = (time.time(), image_urls)
                
                return image_urls
        except Exception as e:
            print(f"Error fetching image URLs: {str(e)}")
            return []

    async def fetch_wikimedia_image_urls(self):
        """Fetch image candidate URLs from Wikimedia/Wikipedia via MediaWiki APIs (stable JSON)."""
        urls = []
        urls.extend(await self._fetch_commons_file_urls(self.word, self.max_images * 4))
        if len(urls) < self.max_images:
            urls.extend(await self._fetch_wikipedia_pageimage_urls(self.word, "zh", self.max_images * 4))
        if len(urls) < self.max_images:
            urls.extend(await self._fetch_wikipedia_pageimage_urls(self.word, "en", self.max_images * 4))

        deduped = []
        seen = set()
        for url in urls:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
            if len(deduped) >= self.max_images:
                break
        return deduped

    async def _fetch_json(self, url: str) -> dict:
        try:
            async with self._session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {}
                return await response.json(content_type=None)
        except Exception as e:
            print(f"Error fetching JSON: {str(e)}")
            return {}

    async def _fetch_commons_file_urls(self, query: str, limit: int) -> list[str]:
        # Search file namespace (6) on Commons and return thumb URLs.
        api = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": "6",
            "gsrlimit": str(max(1, min(limit, 50))),
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": "600",
            "origin": "*",
        }
        url = f"{api}?{urllib.parse.urlencode(params)}"
        data = await self._fetch_json(url)
        pages = (data.get("query") or {}).get("pages") or {}

        urls = []
        for page in pages.values():
            infos = page.get("imageinfo") or []
            if not infos:
                continue
            info = infos[0] or {}
            candidate = info.get("thumburl") or info.get("url")
            if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                urls.append(candidate)
                if len(urls) >= limit:
                    break
        return urls

    async def _fetch_wikipedia_pageimage_urls(self, query: str, lang: str, limit: int) -> list[str]:
        # Search pages on Wikipedia and return page thumbnail URLs (pageimages).
        api = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": str(max(1, min(limit, 50))),
            "prop": "pageimages",
            "piprop": "thumbnail",
            "pithumbsize": "600",
            "origin": "*",
        }
        url = f"{api}?{urllib.parse.urlencode(params)}"
        data = await self._fetch_json(url)
        pages = (data.get("query") or {}).get("pages") or {}

        urls = []
        for page in pages.values():
            thumb = page.get("thumbnail") or {}
            candidate = thumb.get("source")
            if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                urls.append(candidate)
                if len(urls) >= limit:
                    break
        return urls

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
        if pixmap.isNull():
            return None
        if pixmap.width() > max_size or pixmap.height() > max_size:
            pixmap = pixmap.scaled(
                max_size, 
                max_size, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        return pixmap
