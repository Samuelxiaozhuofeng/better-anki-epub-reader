from aqt.qt import *
from aqt import mw
from anki.notes import Note
import json
import os
from PyQt6.QtCore import QTimer, Qt, QSettings
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
from .settings_dialog import AIServiceSettingsDialog, ContextSettingsDialog
from .ui_reader_window import Ui_ReaderWindow
from .word_clickable_text_edit import WordClickableTextEdit
from .epub_manager_dialog import EPUBManagerDialog
from .reader_theme import get_reader_palette, word_label_font_size, word_label_font_size_compact
from ..utils.async_utils import run_async
from ..utils.paths import config_json_path, config_dir, reader_style_path
from .lookup_thread import LookupThread
from ..utils.lookup_json import (
    build_lookup_prompt,
    lookup_template_for_preferences,
    render_lookup_result_html,
    render_streaming_html,
)

class ReaderWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置UI
        self.ui = Ui_ReaderWindow()
        self.ui.setupUi(self)
        
        # 初始化模板管理器和加载上次使用的模板ID
        self.template_manager = TemplateManager()
        self.current_template_id = self.template_manager.current_template_id
        
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
        self.current_meaning = None

        self._ui_settings = QSettings()
        
        # 初始化图片相关变量
        self.current_images = []
        self.current_image_index = 0
        self._image_thread = None
        self._lookup_thread = None
        self._lookup_request_id = 0
        
        # 初始化处理器
        self.anki_handler = AnkiHandler()
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

        # 恢复窗口/分割器状态
        self._restore_ui_state()

        # 初始化词汇面板空状态
        self._set_word_panel_empty_state()
        
        # 设置窗口标题
        self.setWindowTitle("阅读器")
        
        # 不强制设置窗口大小；由 UI 默认值或持久化状态决定

    def create_actions(self):
        """创建动作"""
        # 文件菜单动作
        self.ui.actionOpen = QAction("打开(&O)", self)
        self.ui.actionSave = QAction("保存(&S)", self)
        self.ui.actionSaveAs = QAction("另存为(&A)", self)
        self.ui.actionExit = QAction("退出(&X)", self)
        
        # 设置菜单动作
        self.ui.actionAISettings = QAction("AI 服务设置(&A)", self)
        self.ui.actionContextSettings = QAction("上下文设置(&C)", self)
        self.ui.actionNoteSettings = QAction("笔记设置(&N)", self)
        self.ui.actionTemplateSettings = QAction("模板设置(&T)", self)
    
    def setup_toolbar(self):
        """设置工具栏"""
        # 字体大小调节
        font_size_label = QLabel("字体大小：")
        self.ui.toolbar.addWidget(font_size_label)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 32)
        self.font_size_spin.setValue(18)
        self.font_size_spin.valueChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.font_size_spin)
        
        self.ui.toolbar.addSeparator()
        
        # 行间距调节
        line_spacing_label = QLabel("行间距：")
        self.ui.toolbar.addWidget(line_spacing_label)
        
        self.line_spacing_spin = QDoubleSpinBox()
        self.line_spacing_spin.setRange(1.2, 3.0)
        self.line_spacing_spin.setSingleStep(0.1)
        self.line_spacing_spin.setValue(1.8)
        self.line_spacing_spin.valueChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.line_spacing_spin)
        
        self.ui.toolbar.addSeparator()
        
        # 段落间距调节
        paragraph_spacing_label = QLabel("段落间距：")
        self.ui.toolbar.addWidget(paragraph_spacing_label)
        
        self.paragraph_spacing_spin = QSpinBox()
        self.paragraph_spacing_spin.setRange(0, 40)
        self.paragraph_spacing_spin.setValue(20)
        self.paragraph_spacing_spin.valueChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.paragraph_spacing_spin)
        
        self.ui.toolbar.addSeparator()
        
        # 文本对齐方式
        align_label = QLabel("对齐方式：")
        self.ui.toolbar.addWidget(align_label)
        
        self.align_combo = QComboBox()
        self.align_combo.addItem("左对齐", "left")
        self.align_combo.addItem("两端对齐", "justify")
        self.align_combo.currentIndexChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.align_combo)
        
        self.ui.toolbar.addSeparator()
        
        # 背景颜色
        theme_label = QLabel("主题：")
        self.ui.toolbar.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("默认", "Default")
        self.theme_combo.addItem("护眼", "Eye Care")
        self.theme_combo.addItem("深色", "Dark")
        self.theme_combo.addItem("纸张", "Brown")
        self.theme_combo.currentIndexChanged.connect(self.update_text_style)
        self.ui.toolbar.addWidget(self.theme_combo)
        
        self.ui.toolbar.addSeparator()
        
        # 添加标记位置按钮
        self.mark_position_btn = QPushButton("标记位置")
        self.mark_position_btn.clicked.connect(self.mark_current_position)
        self.ui.toolbar.addWidget(self.mark_position_btn)
        
        self.ui.toolbar.addSeparator()
        
        # EPUB管理按钮
        self.manage_epub_btn = QPushButton("书籍管理")
        self.manage_epub_btn.clicked.connect(self.show_epub_manager)
        self.ui.toolbar.addWidget(self.manage_epub_btn)
        
        self.ui.toolbar.addSeparator()
        
        # 添加Bing Image按钮
        self.bing_image_btn = QPushButton("必应图片")
        self.bing_image_btn.clicked.connect(self.open_bing_image)
        self.ui.toolbar.addWidget(self.bing_image_btn)
        
        self.ui.toolbar.addSeparator()
        
        # 添加图片导航按钮
        self.prev_image_btn = QPushButton("上一张")
        self.prev_image_btn.clicked.connect(self.show_prev_image)
        self.ui.toolbar.addWidget(self.prev_image_btn)
        
        self.next_image_btn = QPushButton("下一张")
        self.next_image_btn.clicked.connect(self.show_next_image)
        self.ui.toolbar.addWidget(self.next_image_btn)
        
        self.image_count_label = QLabel("0/0")
        self.ui.toolbar.addWidget(self.image_count_label)
    
    def setup_connections(self):
        """设置信号连接"""
        # 文本选择变化时的处理
        self.textEdit.wordClicked.connect(self.on_word_clicked)
        if hasattr(self.ui, "cancelLookupButton"):
            self.ui.cancelLookupButton.clicked.connect(self.cancel_current_lookup)
        
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
            path = config_json_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
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
            self._cancel_active_lookup()
            self._lookup_request_id += 1
            request_id = self._lookup_request_id

            # 更新UI
            self.current_meaning = None
            self.current_word = word
            self.current_context = context
            self.ui.addToAnkiButton.setEnabled(False)
            if hasattr(self.ui, "cancelLookupButton"):
                self.ui.cancelLookupButton.setEnabled(True)

            font_size = word_label_font_size(word)

            palette = get_reader_palette(self._get_theme_id())
            text_color = palette["text_color"]
            card_bg = palette["card_bg"]
            border_color = palette["border_color"]
            
            # 设置字体大小和主题颜色
            self.ui.wordLabel.setStyleSheet(f"""
                QLabel {{
                    font-size: {font_size}px;
                    font-weight: 600;
                    color: {text_color};
                    padding: 16px;
                    background-color: {card_bg};
                    border-radius: 10px;
                    border: 1px solid {border_color};
                }}
            """)
            self.ui.wordLabel.setText(word)
            
            # 显示加载提示
            self.ui.meaningText.setHtml("<p style='color:#86868B;'>正在生成（流式）…</p>")
            self.ui.imageLabel.setText("正在加载图片...")
            
            # 同时触发 Bing 图片搜索
            self.open_bing_image()
            
            # 异步获取释义（流式 + JSON）
            self.start_lookup(request_id, word, context)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"处理文本失败：{str(e)}")

    def _load_lookup_optional_fields(self) -> dict:
        path = config_json_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                raw = config.get("lookup_optional_fields", {})
                if isinstance(raw, dict):
                    return {str(k): bool(v) for k, v in raw.items()}
            except Exception:
                pass
        return {"pos": False, "ipa": False, "examples": False}

    def _load_lookup_style_and_language(self) -> tuple[str, str]:
        path = config_json_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                style = str(config.get("lookup_style", "friendly"))
                language = str(config.get("lookup_language", "zh"))
                return style, language
            except Exception:
                pass
        return "friendly", "zh"

    def start_lookup(self, request_id: int, word: str, context: str) -> None:
        style, language = self._load_lookup_style_and_language()
        template_text = lookup_template_for_preferences(style=style, language=language)

        enabled_optional_fields = self._load_lookup_optional_fields()
        prompt = build_lookup_prompt(
            template_text=template_text,
            word=word,
            context=context or "",
            enabled_optional_fields=enabled_optional_fields,
            max_basic_meanings=3,
        )

        self._lookup_thread = LookupThread(
            request_id=request_id,
            ai_client=self.ai_client,
            prompt=prompt,
            enabled_optional_fields=enabled_optional_fields,
            max_basic_meanings=3,
            repair_attempts=1,
        )

        self._lookup_thread.partial.connect(self._on_lookup_partial)
        self._lookup_thread.finished.connect(self._on_lookup_finished)
        self._lookup_thread.failed.connect(self._on_lookup_failed)
        self._lookup_thread.cancelled.connect(self._on_lookup_cancelled)
        self._lookup_thread.start()

    def _cancel_active_lookup(self) -> None:
        t = self._lookup_thread
        if t and t.isRunning():
            try:
                t.cancel()
            except Exception:
                pass
        self._lookup_thread = None
        if hasattr(self.ui, "cancelLookupButton"):
            self.ui.cancelLookupButton.setEnabled(False)

    def cancel_current_lookup(self) -> None:
        self._cancel_active_lookup()
        self.ui.meaningText.setHtml("<p style='color:#86868B;'>已取消。</p>")
        self.ui.addToAnkiButton.setEnabled(False)

    def _on_lookup_partial(self, request_id: int, raw_text: str) -> None:
        if request_id != self._lookup_request_id:
            return
        self.ui.meaningText.setHtml(render_streaming_html(raw_text))

    def _on_lookup_finished(self, request_id: int, result_obj, raw_text: str) -> None:
        if request_id != self._lookup_request_id:
            return
        enabled_optional_fields = self._load_lookup_optional_fields()
        html = render_lookup_result_html(result_obj, enabled_optional_fields=enabled_optional_fields)
        self.current_meaning = html
        self.ui.meaningText.setHtml(html)
        self.ui.addToAnkiButton.setEnabled(True)
        if hasattr(self.ui, "cancelLookupButton"):
            self.ui.cancelLookupButton.setEnabled(False)

    def _on_lookup_failed(self, request_id: int, error_message: str) -> None:
        if request_id != self._lookup_request_id:
            return
        self.ui.meaningText.setHtml(f"<p style='color:#B00020;'>获取释义失败：{error_message}</p>")
        self.ui.addToAnkiButton.setEnabled(False)
        if hasattr(self.ui, "cancelLookupButton"):
            self.ui.cancelLookupButton.setEnabled(False)

    def _on_lookup_cancelled(self, request_id: int) -> None:
        if request_id != self._lookup_request_id:
            return
        self.ui.addToAnkiButton.setEnabled(False)
        if hasattr(self.ui, "cancelLookupButton"):
            self.ui.cancelLookupButton.setEnabled(False)
    
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
        file_name, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "文本文件 (*.txt);;所有文件 (*)")
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.textEdit.toPlainText())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件：{str(e)}")
    
    def show_ai_settings(self):
        """显示AI服务设置对话框"""
        dialog = AIServiceSettingsDialog(self)
        if dialog.exec():
            self.load_ai_client()
            
    def show_context_settings(self):
        """显示上下文设置对话框"""
        dialog = ContextSettingsDialog(self)
        dialog.exec()
    
    def update_text_style(self):
        """更新本样式"""
        palette = get_reader_palette(self._get_theme_id())
        bg_color = palette["bg_color"]
        text_color = palette["text_color"]
        selection_color = palette["selection_color"]
        panel_bg = palette["panel_bg"]
        card_bg = palette["card_bg"]
        border_color = palette["border_color"]
        control_bg = palette["control_bg"]
        control_hover_bg = palette["control_hover_bg"]
        
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

        self.ui.word_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {panel_bg};
                border-left: 1px solid {border_color};
            }}
        """)

        self.ui.meaningText.setStyleSheet(f"""
            QTextEdit {{
                background-color: {card_bg};
                color: {text_color};
                border-radius: 10px;
                border: 1px solid {border_color};
                padding: 16px;
                font-size: 14px;
                line-height: 1.5;
                font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
            }}
        """)

        self.ui.imageLabel.setStyleSheet(f"""
            QLabel {{
                background-color: {card_bg};
                border-radius: 10px;
                border: 1px solid {border_color};
                padding: 10px;
                color: {text_color};
            }}
        """)

        if hasattr(self.ui, "cancelLookupButton"):
            self.ui.cancelLookupButton.setStyleSheet(f"""
                QPushButton {{
                    background-color: {control_bg};
                    color: {text_color};
                    border: 1px solid {border_color};
                    padding: 10px 16px;
                    border-radius: 6px;
                    font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                    font-size: 14px;
                    font-weight: 500;
                    margin: 4px 0;
                }}
                QPushButton:hover {{
                    background-color: {control_hover_bg};
                }}
                QPushButton:pressed {{
                    background-color: {border_color};
                }}
                QPushButton:disabled {{
                    background-color: {panel_bg};
                    color: #8E8E93;
                }}
            """)

        toolbar_style = f"""
            QToolBar {{
                background-color: {panel_bg};
                border-bottom: 1px solid {border_color};
                spacing: 8px;
                padding: 8px;
            }}
            QToolBar QLabel {{
                color: {text_color};
            }}
            QToolBar QPushButton {{
                background-color: {control_bg};
                color: {text_color};
                border: 1px solid {border_color};
                padding: 6px 12px;
                border-radius: 6px;
            }}
            QToolBar QPushButton:hover {{
                background-color: {control_hover_bg};
            }}
            QToolBar QComboBox {{
                background-color: {control_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 120px;
            }}
        """
        self.ui.toolbar.setStyleSheet(toolbar_style)
        self.ui.chapter_toolbar.setStyleSheet(toolbar_style)
        self.ui.menubar.setStyleSheet(f"QMenuBar {{ background-color: {panel_bg}; color: {text_color}; border-bottom: 1px solid {border_color}; }}")

        label_text = self.current_word or "点击单词或选中文本查词"
        if self.current_word:
            label_font_size = word_label_font_size_compact(self.current_word)
        else:
            label_font_size = 14

        self.ui.wordLabel.setStyleSheet(f"""
            QLabel {{
                font-size: {label_font_size}px;
                font-weight: 600;
                color: {text_color};
                padding: 16px;
                background-color: {card_bg};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}
        """)
        self.ui.wordLabel.setText(label_text)
        
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
                                background-color: rgba(0, 122, 255, 0.08);
                                border-radius: 4px;
                            }}
                            code {{
                                font-family: "SF Mono", Menlo, Monaco, Consolas, monospace;
                                background-color: rgba(0, 0, 0, 0.06);
                                padding: 0.2em 0.4em;
                                border-radius: 3px;
                                font-size: 0.9em;
                            }}
                            pre {{
                                background-color: rgba(0, 0, 0, 0.04);
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
            QMessageBox.warning(self, "提示", "请先打开一本书。")
            return
            
        # 获取当前垂直滚动条位置
        position = self.textEdit.verticalScrollBar().value()
        
        # 保存到数据库
        if self.db_handler.update_bookmark(
            self.current_book_id,
            self.current_chapter_index,
            position
        ):
            QMessageBox.information(self, "成功", "已标记当前阅读位置。")
        else:
            QMessageBox.warning(self, "失败", "标记位置失败。")
    
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
                "text_align": self.align_combo.currentData() or "left",
                "theme": self._get_theme_id()
            }

            os.makedirs(config_dir(), exist_ok=True)
            path = reader_style_path()

            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存样式设置失败: {str(e)}")

    def load_style_settings(self):
        """加载样式设置"""
        try:
            path = reader_style_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                    # 设置字体大小
                    self.font_size_spin.setValue(config.get("font_size", 18))
                    
                    # 设置行间距
                    self.line_spacing_spin.setValue(config.get("line_spacing", 1.8))
                    
                    # 设置段落间距
                    self.paragraph_spacing_spin.setValue(config.get("paragraph_spacing", 20))
                    
                    # 设置对齐方式
                    self._set_align_from_config(config.get("text_align", "left"))
                    
                    # 设置主题
                    self._set_theme_from_config(config.get("theme", "Default"))
                    
                    # 立即应用样式
                    self.update_text_style()
                    
        except Exception as e:
            print(f"加载样式设置失败: {str(e)}")

    def _set_align_from_config(self, value: str) -> None:
        value = (value or "").strip()
        legacy_map = {
            "Left": "left",
            "Justify": "justify",
            "左对齐": "left",
            "两端对齐": "justify",
        }
        align = legacy_map.get(value, value)
        for i in range(self.align_combo.count()):
            if self.align_combo.itemData(i) == align:
                self.align_combo.setCurrentIndex(i)
                return
        self.align_combo.setCurrentIndex(0)

    def _set_theme_from_config(self, value: str) -> None:
        value = (value or "").strip()
        legacy_map = {
            "默认": "Default",
            "护眼": "Eye Care",
            "深色": "Dark",
            "纸张": "Brown",
        }
        theme = legacy_map.get(value, value)
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme:
                self.theme_combo.setCurrentIndex(i)
                return
        self.theme_combo.setCurrentIndex(0)

    def _get_theme_id(self) -> str:
        theme = self.theme_combo.currentData()
        if isinstance(theme, str) and theme:
            return theme
        current_text = self.theme_combo.currentText()
        fallback_map = {
            "默认": "Default",
            "护眼": "Eye Care",
            "深色": "Dark",
            "纸张": "Brown",
        }
        return fallback_map.get(current_text, "Default")

    def _set_word_panel_empty_state(self) -> None:
        self.current_word = None
        self.current_context = None
        self.current_meaning = None
        self.ui.wordLabel.setText("点击单词或选中文本查词")
        self.ui.meaningText.setHtml("<p style='color:#86868B;'>在左侧阅读区点击单词，或选中文本后右键选择“查词”。</p>")
        self.ui.addToAnkiButton.setEnabled(False)
        if hasattr(self.ui, "cancelLookupButton"):
            self.ui.cancelLookupButton.setEnabled(False)
        self.ui.imageLabel.setText("暂无图片")
        self.ui.imageCountLabel.setText("")

    def _restore_ui_state(self) -> None:
        self._ui_settings.beginGroup("anki_reader/reader_window")
        geometry = self._ui_settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        window_state = self._ui_settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
        splitter_sizes = self._ui_settings.value("splitterSizes")
        if splitter_sizes:
            try:
                sizes = [int(x) for x in splitter_sizes]
                self.ui.splitter.setSizes(sizes)
            except Exception:
                pass
        self._ui_settings.endGroup()

    def _save_ui_state(self) -> None:
        self._ui_settings.beginGroup("anki_reader/reader_window")
        self._ui_settings.setValue("geometry", self.saveGeometry())
        self._ui_settings.setValue("windowState", self.saveState())
        self._ui_settings.setValue("splitterSizes", self.ui.splitter.sizes())
        self._ui_settings.endGroup()

    def closeEvent(self, event):
        self._cancel_active_lookup()
        self._save_ui_state()
        super().closeEvent(event)

    def open_file(self):
        """打开文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "打开文件",
            "",
            "EPUB 文件 (*.epub);;文本文件 (*.txt);;所有文件 (*)"
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
        align = self.align_combo.currentData()
        if align in ("left", "justify"):
            return align
        return "left"

    def setup_menu(self):
        """设置菜单"""
        # 添加文件菜单项
        self.ui.menuFile.addAction(self.ui.actionOpen)
        self.ui.menuFile.addAction(self.ui.actionSave)
        self.ui.menuFile.addAction(self.ui.actionSaveAs)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionExit)
        
        # 设置菜单
        self.ui.menuSettings = QMenu("设置(&S)")
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
            self.ui.imageLabel.setText("暂无图片")
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
            text = f"{self.current_image_index + 1}/{len(self.current_images)}"
            self.ui.imageCountLabel.setText(text)
            self.image_count_label.setText(f"图片 {text}")
        else:
            self.ui.imageCountLabel.setText("")
            self.image_count_label.setText("")
    
    def on_image_error(self, error_message):
        """当图片搜索出错时的回调"""
        self.ui.imageLabel.setText(f"图片加载失败：{error_message}")
        self.current_images = []
        self.current_image_index = 0
        self.update_image_navigation()
