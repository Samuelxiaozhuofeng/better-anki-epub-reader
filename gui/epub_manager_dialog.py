from aqt.qt import *


class EPUBManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.db_handler = parent.db_handler
        self.setup_ui()
        self.load_books()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("书籍管理")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["书名", "作者", "语言", "章节", "进度", "添加时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        layout.addWidget(self.table)

        button_layout = QHBoxLayout()

        self.open_btn = QPushButton("打开选中的书籍")
        self.open_btn.clicked.connect(self.open_selected_book)
        button_layout.addWidget(self.open_btn)

        self.import_btn = QPushButton("导入新书")
        self.import_btn.clicked.connect(self.import_new_book)
        button_layout.addWidget(self.import_btn)

        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_books(self):
        """加载书籍列表"""
        books = self.db_handler.get_book_list()
        self.table.setRowCount(len(books))

        for row, book in enumerate(books):
            title_item = QTableWidgetItem(book[1])
            title_item.setData(Qt.ItemDataRole.UserRole, book[0])
            self.table.setItem(row, 0, title_item)

            self.table.setItem(row, 1, QTableWidgetItem(book[2] or "未知"))
            self.table.setItem(row, 2, QTableWidgetItem(book[4] or "未知"))

            chapters = self.db_handler.get_chapter_list(book[0])
            chapter_count = len(chapters)
            self.table.setItem(row, 3, QTableWidgetItem(str(chapter_count)))

            progress = self.db_handler.get_book_progress(book[0])
            if progress:
                progress_text = f"{progress['chapter_index'] + 1}/{chapter_count}"
            else:
                progress_text = "未开始"
            self.table.setItem(row, 4, QTableWidgetItem(progress_text))

            self.table.setItem(row, 5, QTableWidgetItem(str(book[5])))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)

            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, book_id=book[0]: self.delete_book(book_id))
            btn_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 6, btn_widget)

    def open_selected_book(self):
        """打开选中的书籍"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择一本书。")
            return

        book_id = self.table.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if book_id:
            try:
                print(f"正在打开书籍ID: {book_id}")
                progress = self.db_handler.get_book_progress(book_id)
                print(f"获取到阅读进度: {progress}")

                self.parent.current_book_id = book_id

                print("刷新章节列表")
                self.parent.refresh_chapter_list(book_id)

                if progress:
                    self.parent.current_chapter_index = progress["chapter_index"]
                    print(f"设置章节索引为: {progress['chapter_index']}")
                else:
                    self.parent.current_chapter_index = 0
                    print("未找到阅读进度，从第一章开始")

                chapter_count = self.parent.ui.chapter_combo.count()
                if self.parent.current_chapter_index >= chapter_count:
                    print(f"章节索引 {self.parent.current_chapter_index} 超范围，重置为0")
                    self.parent.current_chapter_index = 0

                print(f"设置当前章节索引: {self.parent.current_chapter_index}")
                self.parent.ui.chapter_combo.blockSignals(True)
                self.parent.ui.chapter_combo.setCurrentIndex(self.parent.current_chapter_index)
                self.parent.ui.chapter_combo.blockSignals(False)

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
            "EPUB Files (*.epub)",
        )
        if file_name:
            self.parent.open_epub(file_name)
            self.load_books()

    def delete_book(self, book_id: int):
        """删除书籍"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这本书吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db_handler.delete_book(book_id):
                self.load_books()

                if self.parent.current_book_id == book_id:
                    self.parent.current_book_id = None
                    self.parent.current_chapter_index = 0
                    self.parent.textEdit.clear()
                    self.parent.ui.chapter_combo.clear()

