from aqt.qt import *
from ..utils.template_manager import TemplateManager
from .dialog_styles import COMMON_DIALOG_QSS

DIALOG_QSS = (
    COMMON_DIALOG_QSS
    + """
    QLineEdit, QTextEdit {
        font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
    }
    QListWidget {
        border: 1px solid #E5E5EA;
        border-radius: 10px;
        padding: 6px;
    }
    QPushButton {
        font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
    }
"""
)

class TemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("模板设置")
        self.setStyleSheet(DIALOG_QSS)
        
        # Initialize template manager
        self.template_manager = TemplateManager()
        
        # Get current template ID
        self.current_template_id = getattr(parent, 'current_template_id', None)
        
        # Setup UI
        self.setup_ui()
        
        # Load template list
        self.load_templates()
        
        # Update UI state
        self.update_ui_state()
    
    def setup_ui(self):
        """Initialize UI"""
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left template list panel
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        
        # Template list
        list_label = QLabel("模板列表")
        list_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #1D1D1F;
                margin-bottom: 10px;
            }
        """)
        list_layout.addWidget(list_label)
        
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        list_layout.addWidget(self.template_list)
        
        # Button group
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("新建模板")
        self.add_btn.clicked.connect(self.add_template)
        button_layout.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("删除模板")
        self.delete_btn.clicked.connect(self.delete_template)
        button_layout.addWidget(self.delete_btn)
        
        list_layout.addLayout(button_layout)
        
        # Right edit panel
        edit_panel = QWidget()
        edit_layout = QVBoxLayout(edit_panel)
        
        # Template name
        name_layout = QHBoxLayout()
        name_label = QLabel("模板名称：")
        self.name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        edit_layout.addLayout(name_layout)
        
        # Template content
        content_label = QLabel("模板内容：")
        content_label.setStyleSheet("""
            QLabel {
                margin-top: 10px;
            }
        """)
        edit_layout.addWidget(content_label)
        
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("""在这里输入模板内容...

可用占位符：
{word} - 当前选中的单词/文本

示例：
请解释单词「{word}」，要求：
1. 基本含义（简洁）
2. 词性
3. 常见搭配
4. 例句（可选）""")
        edit_layout.addWidget(self.content_edit)
        
        # Button layout
        buttons_layout = QHBoxLayout()
        
        # Save button
        self.save_btn = QPushButton("保存修改")
        self.save_btn.setProperty("primary", True)
        self.save_btn.clicked.connect(self.save_template)
        buttons_layout.addWidget(self.save_btn)
        
        # Use this template button
        self.use_btn = QPushButton("设为当前模板")
        self.use_btn.clicked.connect(self.use_template)
        buttons_layout.addWidget(self.use_btn)
        
        edit_layout.addLayout(buttons_layout)
        
        # Add panels to splitter
        splitter.addWidget(list_panel)
        splitter.addWidget(edit_panel)
        
        # Set initial sizes
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Dialog button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_templates(self):
        """Load template list"""
        self.template_list.clear()
        
        # Load all templates
        try:
            templates = self.template_manager.list_templates("word_definition")
            if isinstance(templates, dict):
                for template_id, template in templates.items():
                    # Create list item
                    name = template["name"]
                    if template_id == self.current_template_id:
                        name += "（当前）"
                    item = QListWidgetItem(name)
                    item.setData(Qt.ItemDataRole.UserRole, {
                        "id": template_id,
                        "is_default": template["is_default"]
                    })
                    self.template_list.addItem(item)
        except Exception as e:
            print(f"Failed to load template list: {str(e)}")
    
    def update_ui_state(self):
        """Update UI state"""
        current_item = self.template_list.currentItem()
        has_selection = current_item is not None
        is_default = has_selection and current_item.data(Qt.ItemDataRole.UserRole)["is_default"]
        
        self.delete_btn.setEnabled(has_selection and not is_default)
        self.save_btn.setEnabled(has_selection)
        self.name_edit.setEnabled(has_selection and not is_default)
        self.content_edit.setEnabled(has_selection)
        self.use_btn.setEnabled(has_selection)
    
    def use_template(self):
        """Use current selected template"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template_data = current_item.data(Qt.ItemDataRole.UserRole)
        template_id = template_data["id"]
        
        # Save current template ID
        if self.template_manager.set_current_template(template_id):
            # Update parent window's current template ID (if exists)
            if hasattr(self.parent(), 'current_template_id'):
                self.parent().current_template_id = template_id
            
            # Update current template ID
            self.current_template_id = template_id
            
            # Refresh list display
            self.load_templates()
            
            QMessageBox.information(self, "成功", "已设置为当前模板。")
        else:
            QMessageBox.warning(self, "错误", "设置当前模板失败。")
    
    def on_template_selected(self, current, previous):
        """Handle template selection change"""
        if not current:
            self.clear_editor()
            return
        
        try:
            template_data = current.data(Qt.ItemDataRole.UserRole)
            template = self.template_manager.get_template("word_definition", template_data["id"])
            
            # Remove current suffix from name
            name = current.text().replace("（当前）", "")
            self.name_edit.setText(name)
            self.content_edit.setText(template)
            
            self.update_ui_state()
        except Exception as e:
            print(f"Failed to load template content: {str(e)}")
            self.clear_editor()
    
    def clear_editor(self):
        """Clear editor"""
        self.name_edit.clear()
        self.content_edit.clear()
        self.update_ui_state()
    
    def add_template(self):
        """Add new template"""
        name = "新模板"
        template = "请解释单词「{word}」，尽量简洁。"
        
        if self.template_manager.add_template("word_definition", name, template):
            self.load_templates()
            # Select new added template
            self.template_list.setCurrentRow(self.template_list.count() - 1)
    
    def save_template(self):
        """Save template"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template_data = current_item.data(Qt.ItemDataRole.UserRole)
        name = self.name_edit.text()
        template = self.content_edit.toPlainText()
        
        if not name or not template:
            QMessageBox.warning(self, "错误", "模板名称和内容不能为空。")
            return
        
        # If default template, create a new custom template
        if template_data["is_default"]:
            template_id = "word_definition_default_custom"
            if self.template_manager.add_template("word_definition", name, template, template_id):
                # Add new template to list
                new_item = QListWidgetItem(name)
                new_item.setData(Qt.ItemDataRole.UserRole, {
                    "id": template_id,
                    "is_default": False
                })
                self.template_list.addItem(new_item)
                self.template_list.setCurrentItem(new_item)
                QMessageBox.information(self, "成功", "已创建新的自定义模板。")
        else:
            # Save existing custom template
            if self.template_manager.add_template("word_definition", name, template, template_data["id"]):
                current_item.setText(name)
                QMessageBox.information(self, "成功", "模板已保存。")
        
        # Reload template list to ensure latest state
        self.load_templates()
        
        # Notify parent window to accept changes
        self.accept()
    
    def delete_template(self):
        """Delete template"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template_data = current_item.data(Qt.ItemDataRole.UserRole)
        if template_data["is_default"]:
            QMessageBox.warning(self, "错误", "默认模板不能删除。")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个模板吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.template_manager.delete_template("word_definition", template_data["id"]):
                self.template_list.takeItem(self.template_list.row(current_item))
                self.clear_editor() 
