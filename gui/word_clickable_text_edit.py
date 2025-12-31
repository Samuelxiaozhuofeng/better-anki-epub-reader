import json
import os

from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor

from .settings_dialog import CONFIG_PATH
from ..utils.text_utils import TextContextExtractor


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

        self.selecting_text = False
        self.last_click_pos = None
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.handle_click)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_click_pos = event.pos()
            self.click_timer.start(200)  # 200ms延迟
            self.selecting_text = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.selecting_text:
                self.click_timer.stop()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.last_click_pos and (event.pos() - self.last_click_pos).manhattanLength() > 5:
            self.selecting_text = True
            self.click_timer.stop()

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
                context = self.lookup_word(word, cursor.position(), for_ai=True)
                self.wordClicked.emit(word, context)

        self.last_click_pos = None
        self.selecting_text = False

    def show_context_menu(self, position):
        menu = self.createStandardContextMenu()

        cursor = self.textCursor()
        selected_text = cursor.selectedText().strip()

        if selected_text:
            lookup_action = menu.addAction("查词")
            menu.insertAction(menu.actions()[0], lookup_action)
            menu.insertSeparator(menu.actions()[1])
            lookup_action.triggered.connect(lambda: self.lookup_and_emit(selected_text, cursor.position()))

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
        include_adjacent = True
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as file:
                config = json.load(file)
                context_type = config.get(
                    "ai_context_type" if for_ai else "anki_context_type",
                    "Current Sentence Only",
                )
                include_adjacent = context_type == "Current Sentence with Adjacent (1 Sentence)"

        text = self.toPlainText()
        return self.context_extractor.get_context(text, cursor_pos, include_adjacent)

