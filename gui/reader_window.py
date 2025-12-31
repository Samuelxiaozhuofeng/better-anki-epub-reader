from aqt.qt import *
from aqt import mw
from anki.notes import Note
import json
import os
import asyncio
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QSplitter
from ..utils.ai_factory import AIFactory
from ..utils.ai_client import AIClient, AIResponse
from ..utils.epub_handler import EPUBHandler
from ..utils.db_handler import DBHandler
from ..utils.template_manager import TemplateManager
from ..utils.anki_handler import AnkiHandler
from ..utils.image_handler import ImageHandler
from .note_settings_dialog import NoteSettingsDialog
from .template_dialog import TemplateDialog
from .settings_dialog import SettingsDialog, ContextSettingsDialog, CONFIG_PATH
from .ui_reader_window import Ui_ReaderWindow
from ..utils.text_utils import TextContextExtractor

def run_async(coro):
    """运行异步函数"""
    try:
        # 尝试获取已存在的事件循环
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # 如果没有事件循环，创建一个新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        # 运行协程
        return loop.run_until_complete(coro)
    except Exception as e:
        print(f"Async operation failed: {str(e)}")
        raise

class WordClickableTextEdit(QTextEdit):
    """支持单词点击的文本编辑器"""
    wordClicked = pyqtSignal(str, str)  # 单词和上下文
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        self.context_extractor = TextContextExtractor()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # 添加选择模式标志
        self.selecting_text = False
        self.last_click_pos = None
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.handle_click)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录点击位置
            self.last_click_pos = event.pos()
            # 启动定时器以区分点击和拖动选择
            self.click_timer.start(200)  # 200ms延迟
            self.selecting_text = False
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 如果正在选择文本不触发查词
            if self.selecting_text:
                self.click_timer.stop()
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        # 如果鼠标移动超过阈值，标记为正在选择文本
        if self.last_click_pos and (event.pos() - self.last_click_pos).manhattanLength() > 5:
            self.selecting_text = True
            self.click_timer.stop()
        
        # 处理鼠标悬停
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        if cursor.selectedText().strip():
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        
        super().mouseMoveEvent(event)
    
    def handle_click(self):
        """处理单击事件"""
        if not self.selecting_text and self.last_click_pos:
            cursor = self.cursorForPosition(self.last_click_pos)
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText().strip()
            if word:
                # 获取AI上下文并发送信号
                context = self.lookup_word(word, cursor.position(), for_ai=True)
                self.wordClicked.emit(word, context)
        
        self.last_click_pos = None
        self.selecting_text = False
    
    def show_context_menu(self, position):
        menu = self.createStandardContextMenu()
        
        # 获取选中的文本
        cursor = self.textCursor()
        selected_text = cursor.selectedText().strip()
        
        if selected_text:
            # 在菜单顶部添加查词选项
            lookup_action = menu.addAction("查词")
            menu.insertAction(menu.actions()[0], lookup_action)  # 插入到第一个位置
            menu.insertSeparator(menu.actions()[1])  # 添加分隔符
            
            # 连接查词动作
            lookup_action.triggered.connect(lambda: self.lookup_and_emit(selected_text, cursor.position()))
        
        # 显示菜单
        menu.exec(self.viewport().mapToGlobal(position))
    
    def lookup_and_emit(self, word: str, cursor_pos: int):
        """查词并发送信号"""
        context = self.lookup_word(word, cursor_pos, for_ai=True)
        self.wordClicked.emit(word, context)
    
    def lookup_word(self, word: str, cursor_pos: int, for_ai: bool = True):
        """处理查词请求
        
        Args:
            word: 选中的单词
            cursor_pos: 光标位置
            for_ai: 是否是发送给AI的场景（True）还是添加到Anki的场景（False）
            
        Returns:
            str: 上下文文本
        """
        # 从配置中获取上下文设置
        include_adjacent = True
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                context_type = config.get("ai_context_type" if for_ai else "anki_context_type", "Current Sentence Only")
                include_adjacent = context_type == "Current Sentence with Adjacent (1 Sentence)"
        
        # 获取上下文
        text = self.toPlainText()
        context = self.context_extractor.get_context(text, cursor_pos, include_adjacent)
        return context

class ReaderWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置UI
        self.ui = Ui_ReaderWindow()
        self.ui.setupUi(self)
        
        # 初始化模板管理器和加载上次使用的模板ID
        self.template_manager = TemplateManager()
        self.current_template_id = self.template_manager._load_current_template_id()
        
        # 替换普通QTextEdit为WordClickableTextEdit
        self.reader_container = self.ui.reader_container
        self.reader_layout = self.ui.reader_layout
        self.textEdit = WordClickableTextEdit()
        self.reader_layout.replaceWidget(self.ui.textEdit, self.textEdit)
        self.ui.textEdit.deleteLater()
        
        # 初始化其他组件
        self.current_book_id = None
        self.current_chapter_index = 0
        self.current_word = None
        self.current_context = None
        
        # 初始化图片相关变量
        self.current_images = []
        self.current_image_index = 0
        self._image_thread = None
        
        # 初始化处理器
        self.anki_handler = AnkiHandler()
        self.template_manager = TemplateManager()
        self.ai_client = None
        self.epub_handler = EPUBHandler()
        self.db_handler = DBHandler()
        self.image_handler = ImageHandler()
        
        # 创建动作和菜单
        self.create_actions()
        self.setup_menu()
        
        # 设置工具栏
        self.setup_toolbar()
        
        # 连接信号和槽
        self.setup_connections()
        
        # 加载AI客户端
        self.load_ai_client()
        
        # 加载样式设置
        self.load_style_settings()
        
        # 设置窗口标题
        self.setWindowTitle("Anki Reader")
        
        # 设置窗口大小
        self.resize(1200, 800)

    def create_actions(self):
        """创建动作"""
        # 文件菜单动作
        self.ui.actionOpen = QAction("打开(&O)", self)
        self.ui.actionSave = QAction("保存(&S)", self)
        self.ui.actionSaveAs = QAction("另存为(&A)", self)
        self.ui.actionExit = QAction("退出(&X)", self)
        
        # 设置菜单动作
        self.ui.actionAISettings = QAction("AI Service Settings(&A)", self)
        self.ui.actionContextSettings = QAction("Context Settings(&C)", self)
        self.ui.actionNoteSettings = QAction("Note Settings(&N)", self)
        self.ui.actionTemplateSettings = QAction("Template Settings(&T)", self)
    
    def setup_toolbar(self):
        """设置工具栏"""
        # 字体大小调节
        font_size_label = QLabel("Font Size：")
        self.ui.toolbar.addWidget(font_size_label)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 32)
        self.font_size_spin.setValue(18)
        self.font_size_spin.valueChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.font_size_spin)
        
        self.ui.toolbar.addSeparator()
        
        # 行间距调节
        line_spacing_label = QLabel("Line Spacing")
        self.ui.toolbar.addWidget(line_spacing_label)
        
        self.line_spacing_spin = QDoubleSpinBox()
        self.line_spacing_spin.setRange(1.2, 3.0)
        self.line_spacing_spin.setSingleStep(0.1)
        self.line_spacing_spin.setValue(1.8)
        self.line_spacing_spin.valueChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.line_spacing_spin)
        
        self.ui.toolbar.addSeparator()
        
        # 段落间距调节
        paragraph_spacing_label = QLabel("Paragraph Spacing")
        self.ui.toolbar.addWidget(paragraph_spacing_label)
        
        self.paragraph_spacing_spin = QSpinBox()
        self.paragraph_spacing_spin.setRange(0, 40)
        self.paragraph_spacing_spin.setValue(20)
        self.paragraph_spacing_spin.valueChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.paragraph_spacing_spin)
        
        self.ui.toolbar.addSeparator()
        
        # 文本对齐方式
        align_label = QLabel("Text Alignment:")
        self.ui.toolbar.addWidget(align_label)
        
        self.align_combo = QComboBox()
        self.align_combo.addItems(["Left", "Justify"])
        self.align_combo.currentIndexChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.align_combo)
        
        self.ui.toolbar.addSeparator()
        
        # 背景颜色
        theme_label = QLabel("Theme:")
        self.ui.toolbar.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Eye Care", "Dark", "Brown"])
        self.theme_combo.currentIndexChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.theme_combo)
        
        self.ui.toolbar.addSeparator()
        
        # 添加标记位置按钮
        self.mark_position_btn = QPushButton("Mark Position")
        self.mark_position_btn.clicked.connect(self.mark_current_position)
        self.ui.toolbar.addWidget(self.mark_position_btn)
        
        self.ui.toolbar.addSeparator()
        
        # EPUB管理按钮
        self.manage_epub_btn = QPushButton("Book Manager")
        self.manage_epub_btn.clicked.connect(self.show_epub_manager)
        self.ui.toolbar.addWidget(self.manage_epub_btn)
        
        self.ui.toolbar.addSeparator()
        
        # 添加Bing Image按钮
        self.bing_image_btn = QPushButton("Bing Image")
        self.bing_image_btn.clicked.connect(self.open_bing_image)
        self.ui.toolbar.addWidget(self.bing_image_btn)
        
        self.ui.toolbar.addSeparator()
        
        # 添加图片导航按钮
        self.prev_image_btn = QPushButton("Prev Image")
        self.prev_image_btn.clicked.connect(self.show_prev_image)
        self.ui.toolbar.addWidget(self.prev_image_btn)
        
        self.next_image_btn = QPushButton("Next Image")
        self.next_image_btn.clicked.connect(self.show_next_image)
        self.ui.toolbar.addWidget(self.next_image_btn)
        
        self.image_count_label = QLabel("0/0")
        self.ui.toolbar.addWidget(self.image_count_label)
    
    def setup_connections(self):
        """设置信号连接"""
        # 文本选择变化时的处理
        self.textEdit.wordClicked.connect(self.on_word_clicked)
        
        # 添加到Anki按钮事件
        self.ui.addToAnkiButton.clicked.connect(self.add_to_anki)
        
        # 菜单动作连接
        self.ui.actionOpen.triggered.connect(self.open_file)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSaveAs.triggered.connect(self.save_file)  # 暂时使用相同的处理函数
        self.ui.actionExit.triggered.connect(self.close)
        
        # 设置菜单动作连接
        self.ui.actionAISettings.triggered.connect(self.show_ai_settings)
        self.ui.actionContextSettings.triggered.connect(self.show_context_settings)
        self.ui.actionNoteSettings.triggered.connect(self.show_note_settings)
        self.ui.actionTemplateSettings.triggered.connect(self.show_template_settings)

        # 章节导航按钮连接
        self.ui.prev_chapter_btn.clicked.connect(self.on_prev_chapter)
        self.ui.next_chapter_btn.clicked.connect(self.on_next_chapter)
        self.ui.chapter_combo.currentIndexChanged.connect(self.on_chapter_changed)
    
    def load_ai_client(self):
        """加载AI客户端"""
        try:
            config_path = os.path.join(mw.pm.addonFolder(), "anki_reader", "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    service_type = config["service_type"].lower().replace(" ", "")
                    if service_type == "openai":
                        client_config = config["openai"]
                    else:
                        client_config = config["custom"]
                    
                    self.ai_client = AIFactory.create_client(service_type, client_config)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"载AI客户端失败：{str(e)}")
    
    def on_word_clicked(self, word: str, context: str):
        """处理单词点击事件"""
        if not self.ai_client:
            QMessageBox.warning(self, "错误", "请先在设置中配置AI服务")
            return
        
        try:
            # 更新UI
            self.current_word = word
            self.current_context = context
            
            # 根据单词长度设置字体大小
            word_length = len(word.split())
            if word_length <= 3:  # 短词组
                font_size = 28
            elif word_length <= 6:  # 中等长度
                font_size = 24
            elif word_length <= 10:  # 较长词组
                font_size = 20
            else:  # 很长的词组
                font_size = 16
                
            # 获取当前主题颜色
            theme_colors = {
                "Default": ("#FAF3E0", "#333333", "#F7F7F7"),  # 纯白背景，黑色文字，浅灰色选中
                "Eye Care": ("#F6F5F1", "#2C3E50", "#E8E7E3"),  # 米白背景，深蓝灰文字，浅灰选中
                "Dark": ("#1C1C1E", "#E5E5E7", "#2C2C2E"),  # iOS暗色模式
                "Brown": ("#FAF6F1", "#3A3A3C", "#F0EBE6")   # 温暖纸张色
            }
            current_theme = self.theme_combo.currentText()
            bg_color, text_color, _ = theme_colors.get(current_theme, ("#FFFFFF", "#000000", "#F7F7F7"))
            
            # 设置字体大小和主题颜色
            self.ui.wordLabel.setStyleSheet(f"""
                QLabel {{
                    font-size: {font_size}px;
                    font-weight: 600;
                    color: {text_color};
                    padding: 16px;
                    background-color: {bg_color};
                    border-radius: 8px;
                    border: 1px solid #D2D2D7;
                }}
            """)
            self.ui.wordLabel.setText(word)
            
            # 显示加载提示
            self.ui.meaningText.setHtml("正在加载释义...")
            
            # 同时触发 Bing 图片搜索
            self.open_bing_image()
            
            # 异步获取释义
            self.get_word_info(word, context)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"处理文本失败：{str(e)}")
    
    def get_word_info(self, word: str, context: str):
        """获取单词信息"""
        try:
            # 获取当前使用的模板
            template = self.template_manager.get_template("word_definition", self.current_template_id)
            # 替换模板中的占位符
            prompt = template.format(word=word)
            if context:
                prompt += f"\n\n上下文：\n{context}"
            
            # 获取释义
            explanation_response = run_async(self.ai_client.explain(prompt))
            if explanation_response.error:
                raise Exception(explanation_response.error)
            
            # 更新UI
            self.current_meaning = explanation_response.explanation
            self.ui.meaningText.setHtml(self.current_meaning)
            
        except Exception as e:
            self.ui.meaningText.setHtml(f"获取释义失败：{str(e)}")
    
    def add_to_anki(self):
        """添加当前单词到Anki"""
        if not all([self.current_word, self.current_meaning]):
            return
            
        # 重新获取Anki所需的上下文
        cursor = self.textEdit.textCursor()
        anki_context = self.textEdit.lookup_word(self.current_word, cursor.position(), for_ai=False)
            
        if self.anki_handler.add_note(
            word=self.current_word,
            meaning=self.current_meaning,
            context=anki_context
        ):
            QMessageBox.information(self, "成功", "已添加到Anki")
    
    def save_file(self):
        """保存文件"""
        file_name, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.textEdit.toPlainText())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件：{str(e)}")
    
    def show_ai_settings(self):
        """显示AI服务设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.load_ai_client()
            
    def show_context_settings(self):
        """显示上下文设置对话框"""
        dialog = ContextSettingsDialog(self)
        dialog.exec()
    
    def update_text_style(self):
        """更新本样式"""
        # 获取主颜色
        theme_colors = {
            "Default": ("#FAF3E0", "#333333", "#F7F7F7"),  # 纯白背景，黑色文字，浅灰色选中
            "Eye Care": ("#F6F5F1", "#2C3E50", "#E8E7E3"),  # 米白背景，深蓝灰文字，浅灰选中
            "Dark": ("#1C1C1E", "#E5E5E7", "#2C2C2E"),  # iOS暗色模式
            "Brown": ("#FAF6F1", "#3A3A3C", "#F0EBE6")   # 温暖纸张色
        }
        
        current_theme = self.theme_combo.currentText()
        bg_color, text_color, selection_color = theme_colors.get(current_theme, ("#FFFFFF", "#000000", "#F7F7F7"))
        
        # 应用主题样式到整个阅读器界面
        self.reader_container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QTextEdit::selection {{
                background: {selection_color};
            }}
        """)
        
        # 设置文本编辑器的样式
        self.textEdit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: 20px 40px;
                font-family: "SF Pro Text", "PingFang SC", -apple-system, "Helvetica Neue", sans-serif;
                font-size: {self.font_size_spin.value()}px;
                line-height: {self.line_spacing_spin.value()};
            }}
        """)
        
        # 如果当前有内容，重新应用样式
        if self.current_book_id:
            content = self.db_handler.get_chapter_content(
                self.current_book_id,
                self.current_chapter_index
            )
            if content:
                html_content = f"""
                    <html>
                    <head>
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600&display=swap');
                            
                            body {{
                                font-family: "SF Pro Text", "PingFang SC", -apple-system, "Helvetica Neue", sans-serif;
                                font-size: {self.font_size_spin.value()}px;
                                line-height: {self.line_spacing_spin.value()};
                                color: {text_color};
                                background-color: {bg_color};
                                text-rendering: optimizeLegibility;
                                -webkit-font-smoothing: antialiased;
                                -moz-osx-font-smoothing: grayscale;
                                max-width: 800px;
                                margin: 0 auto;
                            }}
                            p {{
                                margin-bottom: {self.paragraph_spacing_spin.value()}px;
                                text-align: {self.get_current_text_align()};
                                letter-spacing: 0.01em;
                                word-spacing: 0.05em;
                                text-wrap: balance;
                            }}
                            img {{
                                max-width: 100%;
                                height: auto;
                                display: block;
                                margin: 2em auto;
                                border-radius: 4px;
                                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                            }}
                            h1, h2, h3, h4, h5, h6 {{
                                font-family: "SF Pro Display", "PingFang SC", -apple-system, "Helvetica Neue", sans-serif;
                                color: {text_color};
                                margin: 1.5em 0 0.8em;
                                line-height: 1.3;
                                font-weight: 500;
                                letter-spacing: -0.02em;
                            }}
                            h1 {{ font-size: 2em; }}
                            h2 {{ font-size: 1.7em; }}
                            h3 {{ font-size: 1.4em; }}
                            h4 {{ font-size: 1.2em; }}
                            h5, h6 {{ font-size: 1.1em; }}
                            a {{
                                color: #007AFF;
                                text-decoration: none;
                                transition: color 0.2s ease;
                            }}
                            a:hover {{
                                color: #0056b3;
                            }}
                            blockquote {{
                                margin: 1.5em 0;
                                padding: 0.8em 1.2em;
                                border-left: 3px solid #007AFF;
                                background-color: {selection_color};
                                border-radius: 4px;
                            }}
                            code {{
                                font-family: "SF Mono", Menlo, Monaco, Consolas, monospace;
                                background-color: {selection_color};
                                padding: 0.2em 0.4em;
                                border-radius: 3px;
                                font-size: 0.9em;
                            }}
                            pre {{
                                background-color: {selection_color};
                                padding: 1em;
                                border-radius: 4px;
                                overflow-x: auto;
                            }}
                            pre code {{
                                background-color: transparent;
                                padding: 0;
                            }}
                            ul, ol {{
                                padding-left: 1.5em;
                                margin: 1em 0;
                            }}
                            li {{
                                margin: 0.5em 0;
                            }}
                            hr {{
                                border: none;
                                border-top: 1px solid {selection_color};
                                margin: 2em 0;
                            }}
                            ::selection {{
                                background-color: {selection_color};
                            }}
                        </style>
                    </head>
                    <body>
                        {content}
                    </body>
                    </html>
                """
                self.textEdit.setHtml(html_content)
    
        # 保存样式设置
        self.save_style_settings()
    
    def show_epub_manager(self):
        """显示EPUB管理对话框"""
        dialog = EPUBManagerDialog(self)
        dialog.exec()
    
    def show_note_settings(self):
        """显示笔记设置对话框"""
        dialog = NoteSettingsDialog(self)
        dialog.exec()
    
    def show_template_settings(self):
        """显示模板设置对话框"""
        dialog = TemplateDialog(self)
        if dialog.exec():
            # 重新加载模板管理器
            self.template_manager = TemplateManager()
            self.current_template_id = self.template_manager._load_current_template_id()
    
    def mark_current_position(self):
        """标记当前阅读位置（带提示）"""
        if not self.current_book_id:
            QMessageBox.warning(self, "Warning", "Please open a book first")
            return
            
        # 获取当前垂直滚动条位置
        position = self.textEdit.verticalScrollBar().value()
        
        # 保存到数据库
        if self.db_handler.update_bookmark(
            self.current_book_id,
            self.current_chapter_index,
            position
        ):
            QMessageBox.information(self, "Success", "Marked current position")
        else:
            QMessageBox.warning(self, "Failed", "Marked current position failed")
    
    def save_current_position(self):
        """静默保存当前阅读位置"""
        if not self.current_book_id:
            return False
            
        # 获取当前垂直滚动条位置
        position = self.textEdit.verticalScrollBar().value()
        
        # 保存到数据库
        return self.db_handler.update_bookmark(
            self.current_book_id,
            self.current_chapter_index,
            position
        )
    
    def save_style_settings(self):
        """保存样式设置"""
        try:
            config = {
                "font_size": self.font_size_spin.value(),
                "line_spacing": self.line_spacing_spin.value(),
                "paragraph_spacing": self.paragraph_spacing_spin.value(),
                "text_align": self.align_combo.currentText(),
                "theme": self.theme_combo.currentText()
            }
            
            config_dir = os.path.join(mw.pm.addonFolder(), "anki_reader", "config")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "reader_style.json")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存样式设置失败: {str(e)}")

    def load_style_settings(self):
        """加载样式设置"""
        try:
            config_path = os.path.join(mw.pm.addonFolder(), "anki_reader", "config", "reader_style.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 设置字体大小
                    self.font_size_spin.setValue(config.get("font_size", 18))
                    
                    # 设置行间距
                    self.line_spacing_spin.setValue(config.get("line_spacing", 1.8))
                    
                    # 设置段落间距
                    self.paragraph_spacing_spin.setValue(config.get("paragraph_spacing", 20))
                    
                    # 设置对齐方式
                    align_index = self.align_combo.findText(config.get("text_align", "左对齐"))
                    if align_index >= 0:
                        self.align_combo.setCurrentIndex(align_index)
                    
                    # 设置主题
                    theme_index = self.theme_combo.findText(config.get("theme", "默认"))
                    if theme_index >= 0:
                        self.theme_combo.setCurrentIndex(theme_index)
                    
                    # 立即应用样式
                    self.update_text_style()
                    
        except Exception as e:
            print(f"���载样式设置失败: {str(e)}")

    def open_file(self):
        """打开文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "打开文件",
            "",
            "EPUB Files (*.epub);;Text Files (*.txt);;All Files (*)"
        )
        if file_name:
            try:
                if file_name.lower().endswith('.epub'):
                    self.open_epub(file_name)
                else:
                    with open(file_name, 'r', encoding='utf-8') as f:
                        self.textEdit.setText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件：{str(e)}")
    
    def open_epub(self, file_path: str):
        """打开EPUB文件"""
        try:
            # 加载EPUB
            if not self.epub_handler.load_book(file_path):
                raise Exception("无法加载EPUB文件")
                
            # 获取元数据
            metadata = self.epub_handler.get_metadata()
            
            # 保存到数据库
            book_id = self.db_handler.add_book(metadata, file_path)
            if not book_id:
                raise Exception("无法保存书籍信息")
                
            # 保存章节
            if not self.db_handler.add_chapters(book_id, self.epub_handler.chapters):
                raise Exception("无法保存章节信息")
                
            # 设置为当前书籍
            self.current_book_id = book_id
            
            # 获取阅读进度
            progress = self.db_handler.get_book_progress(book_id)
            if progress:
                self.current_chapter_index = progress['chapter_index']
            else:
                self.current_chapter_index = 0
            
            # 刷新章��列表
            self.refresh_chapter_list(book_id)
            self.ui.chapter_combo.setCurrentIndex(self.current_chapter_index)
            
            # 加载章节
            self.load_chapter()
            
            QMessageBox.information(self, "成功", "图书导入成功！")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开EPUB文件：{str(e)}")
    
    def refresh_chapter_list(self, book_id: int):
        """刷新章节列表"""
        try:
            print(f"刷新章节列表，书籍ID: {book_id}")
            # 获取阅读进度
            progress = self.db_handler.get_book_progress(book_id)
            print(f"获取到读进度: {progress}")
            
            self.ui.chapter_combo.blockSignals(True)  # 暂时阻止信号触发
            self.ui.chapter_combo.clear()
            
            # 从数据库获取章节列表
            chapters = self.db_handler.get_chapter_list(book_id)
            if chapters:
                for chapter in chapters:
                    self.ui.chapter_combo.addItem(chapter['title'], chapter['index'])
                print(f"加载了 {len(chapters)} 个章节")
            else:
                print("未找到章节")
                
            self.ui.chapter_combo.blockSignals(False)  # 恢复信号
                
        except Exception as e:
            print(f"刷新章节列表失败: {str(e)}")
            self.ui.chapter_combo.blockSignals(False)  # 确保信号被恢复
    
    def load_chapter(self):
        """加载当前章节"""
        if not self.current_book_id:
            print("没有当前书籍ID")
            return
            
        print(f"开始加载章节，书ID: {self.current_book_id}, 章节索引: {self.current_chapter_index}")
        content = self.db_handler.get_chapter_content(
            self.current_book_id,
            self.current_chapter_index
        )
        
        if content:
            print(f"成功获取章节内容，长度: {len(content)}")
            # 使用当前样式设置应用内容
            self.update_text_style()
            
            # 获取上次阅读位置
            progress = self.db_handler.get_book_progress(self.current_book_id)
            if progress and progress['chapter_index'] == self.current_chapter_index:
                print(f"找到阅读进度，章节: {progress['chapter_index']}, 位置: {progress['position']}")
                # 使用更长的延时确保内容完全载
                QTimer.singleShot(500, lambda pos=progress['position']: self._restore_position(pos))
            else:
                print("未找到当前章节的阅读进度，从头开始阅读")
                # 更新阅读进度，从头开始
                self.db_handler.update_bookmark(
                    self.current_book_id,
                    self.current_chapter_index,
                    0
                )
        else:
            print("未获取到章节内容")
            self.textEdit.setPlainText("无法加载章节内容")
    
    def _restore_position(self, position: int):
        """恢复阅读位置"""
        print(f"正在恢复阅读位置: {position}")
        scrollbar = self.textEdit.verticalScrollBar()
        current_pos = scrollbar.value()
        print(f"当前位置: {current_pos}, 目��位置: {position}")
        scrollbar.setValue(position)
        print(f"设置后的位置: {scrollbar.value()}")
    
    def get_current_text_align(self):
        """取前文本对齐方式"""
        return "left" if self.align_combo.currentText() == "左对齐" else "justify"

    def setup_menu(self):
        """设置菜单"""
        # 添加文件菜单项
        self.ui.menuFile.addAction(self.ui.actionOpen)
        self.ui.menuFile.addAction(self.ui.actionSave)
        self.ui.menuFile.addAction(self.ui.actionSaveAs)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionExit)
        
        # 设置菜单
        self.ui.menuSettings = QMenu("Settings(&S)")
        self.ui.menubar.addMenu(self.ui.menuSettings)
        
        # 添加设置菜单项
        self.ui.menuSettings.addAction(self.ui.actionAISettings)
        self.ui.menuSettings.addAction(self.ui.actionContextSettings)
        self.ui.menuSettings.addAction(self.ui.actionNoteSettings)
        self.ui.menuSettings.addAction(self.ui.actionTemplateSettings)

    def on_prev_chapter(self):
        """处理上一章按钮点击事件"""
        if not self.current_book_id:
            return
            
        if self.current_chapter_index > 0:
            # 保存当前阅读位置
            self.save_current_position()
            
            # 切换到上一章
            self.current_chapter_index -= 1
            self.ui.chapter_combo.setCurrentIndex(self.current_chapter_index)
            self.load_chapter()
            
    def on_next_chapter(self):
        """处理下一章按钮点击事件"""
        if not self.current_book_id:
            return
            
        chapter_count = self.ui.chapter_combo.count()
        if self.current_chapter_index < chapter_count - 1:
            # 保存当前阅读位置
            self.save_current_position()
            
            # 切换到下一章
            self.current_chapter_index += 1
            self.ui.chapter_combo.setCurrentIndex(self.current_chapter_index)
            self.load_chapter()
            
    def on_chapter_changed(self, index: int):
        """处理章节选择改变事件"""
        if index >= 0 and self.current_book_id:
            # 保存当前阅读位置
            self.save_current_position()
            
            # 更新当前章节索引
            self.current_chapter_index = index
            self.load_chapter()

    def open_bing_image(self):
        """在界面中显示Bing图片搜索结果"""
        if not self.current_word:
            return
            
        # 清除当前图片
        self.current_images = []
        self.current_image_index = 0
        self.update_image_navigation()
        
        # 开始搜索图片
        self._image_thread = ImageHandler.search_image(
            self.current_word,
            self.on_images_found,
            self.on_image_error,
            max_images=5  # 获取5张图片
        )
    
    def on_images_found(self, image_paths):
        """当找到图片时的回调"""
        self.current_images = image_paths
        self.current_image_index = 0
        self.show_current_image()
        self.update_image_navigation()
    
    def show_current_image(self):
        """显示当前索引的图片"""
        if not self.current_images:
            self.ui.imageLabel.setText("No image available")
            return
            
        current_path = self.current_images[self.current_image_index]
        pixmap = ImageHandler.load_image(current_path)
        self.ui.imageLabel.setPixmap(pixmap)
    
    def show_prev_image(self):
        """显示上一张图片"""
        if self.current_images and self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_current_image()
            self.update_image_navigation()
    
    def show_next_image(self):
        """显示下一���图片"""
        if self.current_images and self.current_image_index < len(self.current_images) - 1:
            self.current_image_index += 1
            self.show_current_image()
            self.update_image_navigation()
    
    def update_image_navigation(self):
        """更新图片导航按钮状态和计数器"""
        has_images = bool(self.current_images)
        self.ui.prevImageButton.setEnabled(has_images and self.current_image_index > 0)
        self.ui.nextImageButton.setEnabled(has_images and self.current_image_index < len(self.current_images) - 1)
        
        if has_images:
            self.ui.imageCountLabel.setText(f"Image {self.current_image_index + 1} of {len(self.current_images)}")
        else:
            self.ui.imageCountLabel.setText("")
    
    def on_image_error(self, error_message):
        """当图片搜索出错时的回调"""
        self.ui.imageLabel.setText(f"Error: {error_message}")
        self.current_images = []
        self.current_image_index = 0
        self.update_image_navigation()


class EPUBManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.db_handler = parent.db_handler
        self.setup_ui()
        self.load_books()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("EPUB Manager")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        
        # 创建主布局
        layout = QVBoxLayout()
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)  # 增加了章节数和阅读进度列
        self.table.setHorizontalHeaderLabels(["Title", "Author", "Language", "Chapters", "Progress", "Added Time", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        # 允选择整行
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.table)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 添加打开按钮
        self.open_btn = QPushButton("Open Selected Book")
        self.open_btn.clicked.connect(self.open_selected_book)
        button_layout.addWidget(self.open_btn)
        
        # 添加导入按钮
        self.import_btn = QPushButton("Import New Book")
        self.import_btn.clicked.connect(self.import_new_book)
        button_layout.addWidget(self.import_btn)
        
        button_layout.addStretch()
        
        # 添加关闭按钮
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def load_books(self):
        """加载书籍列表"""
        books = self.db_handler.get_book_list()
        self.table.setRowCount(len(books))
        
        for row, book in enumerate(books):
            # 标题
            title_item = QTableWidgetItem(book[1])
            title_item.setData(Qt.ItemDataRole.UserRole, book[0])  # 存储书籍ID
            self.table.setItem(row, 0, title_item)
            
            # 作者
            self.table.setItem(row, 1, QTableWidgetItem(book[2] or "未知"))
            
            # 语言
            self.table.setItem(row, 2, QTableWidgetItem(book[4] or "未知"))
            
            # 获取章节数
            chapters = self.db_handler.get_chapter_list(book[0])
            chapter_count = len(chapters)
            self.table.setItem(row, 3, QTableWidgetItem(str(chapter_count)))
            
            # 获取阅读进度
            progress = self.db_handler.get_book_progress(book[0])
            if progress:
                progress_text = f"{progress['chapter_index'] + 1}/{chapter_count}"
            else:
                progress_text = "未开始"
            self.table.setItem(row, 4, QTableWidgetItem(progress_text))
            
            # 添加时间
            self.table.setItem(row, 5, QTableWidgetItem(str(book[5])))
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            # 删除按钮
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, book_id=book[0]: self.delete_book(book_id))
            btn_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 6, btn_widget)
    
    def open_selected_book(self):
        """Open Selected Book"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a book to open.")
            return
            
        book_id = self.table.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if book_id:
            try:
                print(f"正在打开书籍ID: {book_id}")
                # 获取阅读进度
                progress = self.db_handler.get_book_progress(book_id)
                print(f"获取到阅读进度: {progress}")
                
                # 设置父窗口的当前书籍
                self.parent.current_book_id = book_id
                
                # 先刷新章节列表
                print("刷新章节列表")
                self.parent.refresh_chapter_list(book_id)
                
                # 设置章节索引
                if progress:
                    self.parent.current_chapter_index = progress['chapter_index']
                    print(f"设置章节索引为: {progress['chapter_index']}")
                else:
                    self.parent.current_chapter_index = 0
                    print("未找到阅读进度，从第一章开始")
                
                # 确保章节索引在有效范围内
                chapter_count = self.parent.ui.chapter_combo.count()
                if self.parent.current_chapter_index >= chapter_count:
                    print(f"章节索引 {self.parent.current_chapter_index} 超范围，重置为0")
                    self.parent.current_chapter_index = 0
                
                # 设置当前章节
                print(f"设置当前章节索引: {self.parent.current_chapter_index}")
                self.parent.ui.chapter_combo.blockSignals(True)  # 暂时阻止信号触发
                self.parent.ui.chapter_combo.setCurrentIndex(self.parent.current_chapter_index)
                self.parent.ui.chapter_combo.blockSignals(False)  # 恢复信号
                
                # 加载章节内容
                print("开始加载章节内容")
                self.parent.load_chapter()
                
                self.accept()
                
            except Exception as e:
                print(f"打开书时出错: {str(e)}")
                QMessageBox.critical(self, "错误", f"打开书籍失败：{str(e)}")
    
    def import_new_book(self):
        """导入新图书"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择EPUB文件",
            "",
            "EPUB Files (*.epub)"
        )
        if file_name:
            self.parent.open_epub(file_name)
            self.load_books()  # 重新加载书籍列表
            
    def delete_book(self, book_id: int):
        """Delete Book"""
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this book?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_handler.delete_book(book_id):
                self.load_books()  # 重新加载书籍列表
                
                # 如果删除的是当前打开的书籍，清空示
                if self.parent.current_book_id == book_id:
                    self.parent.current_book_id = None
                    self.parent.current_chapter_index = 0
                    self.parent.textEdit.clear()
                    self.parent.ui.chapter_combo.clear()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # 服务类型选择
        service_group = QGroupBox("AI Service")
        service_layout = QVBoxLayout()
        
        self.service_combo = QComboBox()
        self.service_combo.addItems(["OpenAI", "Custom"])
        service_layout.addWidget(self.service_combo)
        
        # OpenAI设置
        self.openai_group = QGroupBox("OpenAI")
        openai_layout = QFormLayout()
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        openai_layout.addRow("API:", self.api_key_edit)
        
        self.model_edit = QLineEdit()
        self.model_edit.setText("gpt-3.5-turbo")
        openai_layout.addRow("AI Model:", self.model_edit)
        
        self.openai_group.setLayout(openai_layout)
        
        # 自定义服务设置
        self.custom_group = QGroupBox("Custom")
        custom_layout = QFormLayout()
        
        self.custom_key_edit = QLineEdit()
        self.custom_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        custom_layout.addRow("API:", self.custom_key_edit)
        
        self.endpoint_edit = QLineEdit()
        custom_layout.addRow("API endpoint:", self.endpoint_edit)
        
        self.custom_model_edit = QLineEdit()
        self.custom_model_edit.setPlaceholderText("例如: gpt-3.5-turbo")
        custom_layout.addRow("AI model:", self.custom_model_edit)
        
        # 添加测试连接按钮
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        custom_layout.addRow("", self.test_btn)
        
        self.custom_group.setLayout(custom_layout)
        
        # 添��所有组件到主布局
        service_group.setLayout(service_layout)
        layout.addWidget(service_group)
        layout.addWidget(self.openai_group)
        layout.addWidget(self.custom_group)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # 连接信号
        self.service_combo.currentIndexChanged.connect(self.on_service_changed)
        self.on_service_changed(0)
        
    def test_connection(self):
        """测试自定义服务连接"""
        try:
            # 禁测试按钮
            self.test_btn.setEnabled(False)
            self.test_btn.setText("测试中...")
            
            # 创建临时配置
            config = {
                "api_key": self.custom_key_edit.text(),
                "endpoint": self.endpoint_edit.text(),
                "model": self.custom_model_edit.text()
            }
            
            # 创建临时客户端
            client = AIFactory.create_client("custom", config)
            
            # 运行测试
            response = run_async(client.explain("Test Connection"))
            
            if response.error:
                raise Exception(response.error)
                
            QMessageBox.information(self, "Success", "Connection test success！")
            
        except Exception as e:
            QMessageBox.critical(self, "Failed", f"Connection test failed：{str(e)}")
            
        finally:
            # 恢复测试按钮
            self.test_btn.setEnabled(True)
            self.test_btn.setText("Test Connection")
        
    def on_service_changed(self, index):
        """理服务类型切换"""
        is_openai = index == 0
        self.openai_group.setVisible(is_openai)
        self.custom_group.setVisible(not is_openai)
        
    def load_settings(self):
        """加载设置"""
        try:
            config_path = os.path.join(mw.pm.addonFolder(), "anki_reader", "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 设置服务类型
                    service_type = config.get("service_type", "openai").lower()
                    self.service_combo.setCurrentIndex(0 if service_type == "openai" else 1)
                    
                    # 设置OpenAI配置
                    if "openai" in config:
                        self.api_key_edit.setText(config["openai"].get("api_key", ""))
                        self.model_edit.setText(config["openai"].get("model", "gpt-3.5-turbo"))
                    
                    # 设置自定义服务配置
                    if "custom" in config:
                        self.custom_key_edit.setText(config["custom"].get("api_key", ""))
                        self.endpoint_edit.setText(config["custom"].get("endpoint", ""))
                        self.custom_model_edit.setText(config["custom"].get("model", ""))
        except Exception as e:
            print(f"加载设置失败: {str(e)}")
            
    def accept(self):
        """保存设置"""
        try:
            config = {
                "service_type": "openai" if self.service_combo.currentIndex() == 0 else "custom",
                "openai": {
                    "api_key": self.api_key_edit.text(),
                    "model": self.model_edit.text()
                },
                "custom": {
                    "api_key": self.custom_key_edit.text(),
                    "endpoint": self.endpoint_edit.text(),
                    "model": self.custom_model_edit.text()
                }
            }
            
            config_path = os.path.join(mw.pm.addonFolder(), "anki_reader", "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")