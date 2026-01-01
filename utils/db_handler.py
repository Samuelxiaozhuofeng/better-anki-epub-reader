from typing import Dict, List, Optional
from aqt import mw
from aqt.utils import showWarning

class DBHandler:
    """数据库处理类"""
    
    def __init__(self):
        self._init_tables()
        
    def _init_tables(self):
        """初始化数据库表"""
        sql_create_books = """
        CREATE TABLE IF NOT EXISTS epub_books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            file_path TEXT NOT NULL,
            language TEXT,
            identifier TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        sql_create_chapters = """
        CREATE TABLE IF NOT EXISTS epub_chapters (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            chapter_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (book_id) REFERENCES epub_books (id)
        );
        """
        
        sql_create_bookmarks = """
        CREATE TABLE IF NOT EXISTS epub_bookmarks (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            chapter_index INTEGER NOT NULL,
            position INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES epub_books (id)
        );
        """
        
        try:
            mw.col.db.execute(sql_create_books)
            mw.col.db.execute(sql_create_chapters)
            mw.col.db.execute(sql_create_bookmarks)
        except Exception as e:
            showWarning(f"初始化数据库失败: {str(e)}")
            
    def add_book(self, metadata: Dict, file_path: str) -> Optional[int]:
        """添加书籍
        
        Args:
            metadata: 书籍元数据
            file_path: 文件路径
            
        Returns:
            Optional[int]: 书籍ID
        """
        try:
            # 开始事务
            mw.col.db.execute("BEGIN")
            
            # 检查文件是否已存在
            existing = mw.col.db.scalar(
                "SELECT id FROM epub_books WHERE file_path = ?",
                file_path
            )
            if existing:
                mw.col.db.execute("ROLLBACK")
                return existing
            
            # 添加新书籍
            book_id = mw.col.db.scalar(
                """
                INSERT INTO epub_books (title, author, file_path, language, identifier, description)
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                metadata.get('title', '未知标题'),
                metadata.get('creator', '未知作者'),
                file_path,
                metadata.get('language', 'zh'),
                metadata.get('identifier', ''),
                metadata.get('description', '')
            )
            
            # 提交事务
            mw.col.db.execute("COMMIT")
            return book_id
            
        except Exception as e:
            # 回滚事务
            mw.col.db.execute("ROLLBACK")
            showWarning(f"添加书籍失败: {str(e)}")
            return None

    def get_book_id_by_path(self, file_path: str) -> Optional[int]:
        """根据文件路径获取书籍ID"""
        try:
            return mw.col.db.scalar(
                "SELECT id FROM epub_books WHERE file_path = ?",
                file_path,
            )
        except Exception as e:
            showWarning(f"获取书籍ID失败: {str(e)}")
            return None
            
    def add_chapters(self, book_id: int, chapters: List[Dict]) -> bool:
        """添加章节
        
        Args:
            book_id: 书籍ID
            chapters: 章节列表
            
        Returns:
            bool: 是否成功
        """
        try:
            print(f"开始保存章节，书籍ID: {book_id}, 章节数量: {len(chapters)}")
            mw.col.db.execute("BEGIN")
            
            # 先删除已存在的章节
            mw.col.db.execute(
                "DELETE FROM epub_chapters WHERE book_id = ?",
                book_id
            )
            
            # 添加新章节
            for index, chapter in enumerate(chapters):
                print(f"保存章节 {index}: {chapter['name']}, 内容长度: {len(chapter['content'])}")
                mw.col.db.execute(
                    """
                    INSERT INTO epub_chapters (book_id, chapter_index, title, content)
                    VALUES (?, ?, ?, ?)
                    """,
                    book_id,
                    index,
                    chapter['name'],
                    chapter['content']
                )
            
            mw.col.db.execute("COMMIT")
            print(f"章节保存完成，共保存 {len(chapters)} 个章节")
            return True
            
        except Exception as e:
            mw.col.db.execute("ROLLBACK")
            print(f"添加章节失败: {str(e)}")
            return False
            
    def update_bookmark(self, book_id: int, chapter_index: int, position: int) -> bool:
        """更新阅读进度
        
        Args:
            book_id: 书籍ID
            chapter_index: 章节索引
            position: 阅读位置
            
        Returns:
            bool: 是否成功
        """
        try:
            # 该表目前未定义唯一约束，直接 INSERT 会导致多条记录堆积。
            # 这里保持“每本书仅保存一条最后进度”的语义。
            mw.col.db.execute("BEGIN")
            mw.col.db.execute(
                "DELETE FROM epub_bookmarks WHERE book_id = ?",
                book_id,
            )
            mw.col.db.execute(
                """
                INSERT INTO epub_bookmarks (book_id, chapter_index, position)
                VALUES (?, ?, ?)
                """,
                book_id,
                chapter_index,
                position,
            )
            mw.col.db.execute("COMMIT")
            return True
        except Exception as e:
            try:
                mw.col.db.execute("ROLLBACK")
            except Exception:
                pass
            showWarning(f"更新阅读进度失败: {str(e)}")
            return False
            
    def get_book_list(self) -> List[Dict]:
        """获取书籍列表
        
        Returns:
            List[Dict]: 书籍列表
        """
        try:
            return mw.col.db.all(
                """
                SELECT id, title, author, file_path, language, created_at
                FROM epub_books
                ORDER BY created_at DESC
                """
            )
        except Exception as e:
            showWarning(f"获取书籍列表失败: {str(e)}")
            return []
            
    def get_book_progress(self, book_id: int) -> Optional[Dict]:
        """获取阅读进度
        
        Args:
            book_id: 书籍ID
            
        Returns:
            Optional[Dict]: 阅读进度
        """
        try:
            result = mw.col.db.first(
                """
                SELECT chapter_index, position
                FROM epub_bookmarks
                WHERE book_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                book_id
            )
            if result:
                return {
                    'chapter_index': result[0],
                    'position': result[1]
                }
            return None
        except Exception as e:
            showWarning(f"获取阅读进度失败: {str(e)}")
            return None
            
    def get_chapter_content(self, book_id: int, chapter_index: int) -> Optional[str]:
        """获取章节内容"""
        try:
            print(f"获取章节内容，书籍ID: {book_id}, 章节索引: {chapter_index}")
            result = mw.col.db.first(
                """
                SELECT content, title
                FROM epub_chapters
                WHERE book_id = ? AND chapter_index = ?
                """,
                book_id,
                chapter_index
            )
            if result:
                print(f"找到章节: {result[1]}, 内容长度: {len(result[0])}")
                return result[0]
            else:
                print("未找到章节内容")
                return None
        except Exception as e:
            showWarning(f"获取章节内容失败: {str(e)}")
            return None
            
    def get_chapter_list(self, book_id: int) -> List[Dict]:
        """获取章节列表
        
        Args:
            book_id: 书籍ID
            
        Returns:
            List[Dict]: 章节列表，每个章节包含 index 和 title
        """
        try:
            print(f"获取章节列表，书籍ID: {book_id}")
            results = mw.col.db.all(
                """
                SELECT chapter_index, title
                FROM epub_chapters
                WHERE book_id = ?
                ORDER BY chapter_index ASC
                """,
                book_id
            )
            
            chapters = []
            for result in results:
                chapters.append({
                    'index': result[0],
                    'title': result[1]
                })
            
            print(f"找到 {len(chapters)} 个章节")
            return chapters
            
        except Exception as e:
            showWarning(f"获取章节列表失败: {str(e)}")
            return []
            
    def delete_book(self, book_id: int) -> bool:
        """删除书籍及其相关数据
        
        Args:
            book_id: 书籍ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            print(f"删除书籍，ID: {book_id}")
            mw.col.db.execute("BEGIN")
            
            # 删除书签
            mw.col.db.execute(
                "DELETE FROM epub_bookmarks WHERE book_id = ?",
                book_id
            )
            
            # 删除章节
            mw.col.db.execute(
                "DELETE FROM epub_chapters WHERE book_id = ?",
                book_id
            )
            
            # 删除书籍
            mw.col.db.execute(
                "DELETE FROM epub_books WHERE id = ?",
                book_id
            )
            
            mw.col.db.execute("COMMIT")
            print("书籍删除成功")
            return True
            
        except Exception as e:
            mw.col.db.execute("ROLLBACK")
            showWarning(f"删除书籍失败: {str(e)}")
            return False 
