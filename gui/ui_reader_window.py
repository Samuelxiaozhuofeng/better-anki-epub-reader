from aqt.qt import *

class Ui_ReaderWindow(object):
    def setupUi(self, ReaderWindow):
        if not ReaderWindow.objectName():
            ReaderWindow.setObjectName("ReaderWindow")
        ReaderWindow.resize(1200, 800)
        
        # 设置窗口样式
        ReaderWindow.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QTextEdit {
                background-color: #FFFFFF;
                border: none;
                padding: 24px 32px;
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 16px;
                line-height: 1.6;
                selection-background-color: #CFE4FF;
                color: #1D1D1F;
            }
            QLabel {
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 14px;
                color: #1D1D1F;
                padding: 5px;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #1D1D1F;
                border: 1px solid #D2D2D7;
                padding: 6px 12px;
                border-radius: 6px;
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F5F5F7;
            }
            QPushButton:pressed {
                background-color: #E5E5EA;
            }
            QPushButton:disabled {
                color: #86868B;
                background-color: #F5F5F7;
            }
            QToolBar {
                background-color: #F5F5F7;
                border-bottom: 1px solid #D2D2D7;
                spacing: 8px;
                padding: 8px;
            }
            QComboBox {
                border: 1px solid #D2D2D7;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 200px;
                background-color: #FFFFFF;
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QMenuBar {
                background-color: #F5F5F7;
                border-bottom: 1px solid #D2D2D7;
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 13px;
            }
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #D2D2D7;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 24px;
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #007AFF;
                color: #FFFFFF;
            }
            QStatusBar {
                background-color: #F5F5F7;
                color: #86868B;
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 12px;
            }
            QSplitter::handle {
                background-color: #D2D2D7;
                width: 1px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F5F5F7;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #86868B;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #F5F5F7;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #86868B;
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # 创建中心部件
        self.centralwidget = QWidget(ReaderWindow)
        
        # 创建主布局
        self.main_layout = QHBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 创建阅读器容器
        self.reader_container = QWidget()
        self.reader_layout = QVBoxLayout(self.reader_container)
        self.reader_layout.setContentsMargins(20, 20, 20, 20)
        self.reader_layout.setSpacing(10)
        
        # 创建文本编辑器
        self.textEdit = QTextEdit()
        self.textEdit.setFrameShape(QFrame.Shape.NoFrame)
        self.textEdit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.reader_layout.addWidget(self.textEdit)
        
        # 创建右侧词汇信息面板
        self.word_panel = QWidget()
        self.word_panel.setStyleSheet("""
            QWidget {
                background-color: #F5F5F7;
                border-left: 1px solid #D2D2D7;
            }
        """)
        
        # 创建主布局
        self.word_main_layout = QVBoxLayout(self.word_panel)
        self.word_main_layout.setContentsMargins(16, 16, 16, 16)
        self.word_main_layout.setSpacing(12)
        
        # 单词标签
        self.wordLabel = QLabel()
        self.wordLabel.setStyleSheet("""
            QLabel {
                font-weight: 600;
                color: #1D1D1F;
                padding: 16px;
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E5E5EA;
            }
        """)
        self.wordLabel.setWordWrap(True)  # 允许标签文字换行
        self.wordLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 文字居中对齐
        self.word_main_layout.addWidget(self.wordLabel)
        
        # 创建滚动区域
        self.meaningScroll = QScrollArea()
        self.meaningScroll.setWidgetResizable(True)
        self.meaningScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.meaningScroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.meaningScroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # 创建内容容器
        self.meaningContainer = QWidget()
        self.meaningLayout = QVBoxLayout(self.meaningContainer)
        self.meaningLayout.setContentsMargins(0, 0, 0, 0)
        self.meaningLayout.setSpacing(0)
        
        # 释义文本框
        self.meaningText = QTextEdit()
        self.meaningText.setReadOnly(True)
        self.meaningText.setAcceptRichText(True)
        self.meaningText.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E5E5EA;
                padding: 16px;
                font-size: 14px;
                line-height: 1.5;
                font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
                color: #1D1D1F;
                letter-spacing: 0.01em;
                min-height: 200px;  /* 设置最小高度 */
            }
        """)
        self.meaningLayout.addWidget(self.meaningText, 1)  # 设置拉伸因子为1
        
        # 图片显示区域
        self.imageContainer = QWidget()
        self.imageLayout = QVBoxLayout(self.imageContainer)
        self.imageLayout.setContentsMargins(0, 0, 0, 0)
        self.imageLayout.setSpacing(10)
        
        # 图片导航按钮布局
        self.imageNavLayout = QHBoxLayout()
        self.prevImageButton = QPushButton("←")
        self.prevImageButton.setFixedWidth(40)
        self.prevImageButton.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                border: 1px solid #D2D2D7;
                border-radius: 4px;
                padding: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E5E5EA;
            }
        """)
        
        self.nextImageButton = QPushButton("→")
        self.nextImageButton.setFixedWidth(40)
        self.nextImageButton.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                border: 1px solid #D2D2D7;
                border-radius: 4px;
                padding: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E5E5EA;
            }
        """)
        
        self.imageCountLabel = QLabel("0/0")
        self.imageCountLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageCountLabel.setStyleSheet("""
            QLabel {
                color: #8E8E93;
                font-size: 12px;
            }
        """)
        
        self.imageNavLayout.addWidget(self.prevImageButton)
        self.imageNavLayout.addWidget(self.imageCountLabel)
        self.imageNavLayout.addWidget(self.nextImageButton)
        
        # 图片标签
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageLabel.setMinimumHeight(300)
        self.imageLabel.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E5E5EA;
                padding: 10px;
            }
        """)
        
        self.imageLayout.addWidget(self.imageLabel)
        self.imageLayout.addLayout(self.imageNavLayout)
        
        self.meaningLayout.addWidget(self.imageContainer)
        
        # 设置滚动区域的内容
        self.meaningScroll.setWidget(self.meaningContainer)
        self.word_main_layout.addWidget(self.meaningScroll, 1)
        
        # 操作按钮（取消 / 添加到 Anki）
        self.actionButtonsContainer = QWidget()
        self.actionButtonsLayout = QHBoxLayout(self.actionButtonsContainer)
        self.actionButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.actionButtonsLayout.setSpacing(10)

        self.cancelLookupButton = QPushButton("取消")
        self.cancelLookupButton.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                color: #1D1D1F;
                border: 1px solid #D2D2D7;
                padding: 10px 16px;
                border-radius: 6px;
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 14px;
                font-weight: 500;
                margin: 4px 0;
            }
            QPushButton:hover {
                background-color: #E5E5EA;
            }
            QPushButton:pressed {
                background-color: #D2D2D7;
            }
            QPushButton:disabled {
                background-color: #F5F5F7;
                color: #8E8E93;
            }
        """)

        self.addToAnkiButton = QPushButton("添加到 Anki")
        self.addToAnkiButton.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-family: "SF Pro Text", "-apple-system", "Microsoft YaHei";
                font-size: 14px;
                font-weight: 500;
                margin: 4px 0;
            }
            QPushButton:hover {
                background-color: #0066D6;
            }
            QPushButton:pressed {
                background-color: #0051A8;
            }
            QPushButton:disabled {
                background-color: #D2D2D7;
                color: #FFFFFF;
            }
        """)

        self.actionButtonsLayout.addWidget(self.cancelLookupButton)
        self.actionButtonsLayout.addWidget(self.addToAnkiButton, 1)
        self.word_main_layout.addWidget(self.actionButtonsContainer)
        
        # 添加到分割器
        self.splitter.addWidget(self.reader_container)
        self.splitter.addWidget(self.word_panel)
        
        # 设置分割器比例
        self.splitter.setStretchFactor(0, 6)  # 左侧占60%
        self.splitter.setStretchFactor(1, 4)  # 右侧占40%
        
        # 添加分割器到主布局
        self.main_layout.addWidget(self.splitter)
        
        # 创建菜单栏
        self.menubar = QMenuBar(ReaderWindow)
        self.menubar.setGeometry(QRect(0, 0, 1200, 22))
        
        # 文件菜单
        self.menuFile = QMenu("文件(&F)", self.menubar)
        self.actionOpen = QAction("打开(&O)", ReaderWindow)
        self.actionSave = QAction("保存(&S)", ReaderWindow)
        self.actionSaveAs = QAction("另存为(&A)", ReaderWindow)
        self.actionExit = QAction("退出(&X)", ReaderWindow)
        
        # 设置菜单栏
        ReaderWindow.setMenuBar(self.menubar)
        self.menubar.addMenu(self.menuFile)
        
        # 创建工具栏
        self.toolbar = QToolBar(ReaderWindow)
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setMovable(False)  # 禁止移动工具栏
        ReaderWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # 创建章节导航工具栏
        self.chapter_toolbar = QToolBar(ReaderWindow)
        self.chapter_toolbar.setMovable(False)  # 禁止移动工具栏
        ReaderWindow.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.chapter_toolbar)
        
        # 设置章节导航按钮样式
        nav_button_style = """
            QPushButton {
                background-color: #F8F9FA;
                color: #2C3E50;
                border: 1px solid #E0E0E0;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #E9ECEF;
            }
        """
        
        self.prev_chapter_btn = QPushButton("上一章")
        self.prev_chapter_btn.setStyleSheet(nav_button_style)
        self.chapter_combo = QComboBox()
        self.next_chapter_btn = QPushButton("下一章")
        self.next_chapter_btn.setStyleSheet(nav_button_style)
        
        self.chapter_toolbar.addWidget(self.prev_chapter_btn)
        self.chapter_toolbar.addWidget(self.chapter_combo)
        self.chapter_toolbar.addWidget(self.next_chapter_btn)
        
        # 设置中心部件
        ReaderWindow.setCentralWidget(self.centralwidget)
        
        # 设置快捷键
        self.actionOpen.setShortcut("Ctrl+O")
        self.actionSave.setShortcut("Ctrl+S")
        self.actionSaveAs.setShortcut("Ctrl+Shift+S")
        
        # 设置状态栏
        self.statusbar = QStatusBar(ReaderWindow)
        ReaderWindow.setStatusBar(self.statusbar)
        
        self.retranslateUi(ReaderWindow)
        QMetaObject.connectSlotsByName(ReaderWindow)
    
    def retranslateUi(self, ReaderWindow):
        ReaderWindow.setWindowTitle("阅读器")
        self.menuFile.setTitle("文件(&F)")
        self.actionOpen.setText("打开(&O)")
        self.actionSave.setText("保存(&S)")
        self.actionSaveAs.setText("另存为(&A)")
        self.actionExit.setText("退出(&X)")
