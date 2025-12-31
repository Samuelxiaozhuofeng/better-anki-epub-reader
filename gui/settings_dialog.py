from aqt.qt import *
from aqt import mw
from typing import Dict, Any, Optional
import json
import os
import asyncio
from ..utils.ai_factory import AIFactory
from ..utils.ai_client import AIClient
from ..utils.template_manager import TemplateManager

CONFIG_PATH = os.path.join(mw.pm.addonFolder(), "anki_reader", "config.json")

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

class ContextSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Context Settings")
        self.setMinimumWidth(400)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # AI上下文设置组
        self.ai_context_group = QGroupBox("AI Context Settings")
        ai_context_layout = QVBoxLayout()
        
        self.ai_context_type_label = QLabel("AI Context Range:")
        self.ai_context_type_combo = QComboBox()
        self.ai_context_type_combo.addItems([
            "Current Sentence Only",
            "Current Sentence with Adjacent (1 Sentence)"
        ])
        
        ai_context_layout.addWidget(self.ai_context_type_label)
        ai_context_layout.addWidget(self.ai_context_type_combo)
        self.ai_context_group.setLayout(ai_context_layout)
        
        # Anki上下文设置组
        self.anki_context_group = QGroupBox("Anki Context Settings")
        anki_context_layout = QVBoxLayout()
        
        self.anki_context_type_label = QLabel("Anki Context Range:")
        self.anki_context_type_combo = QComboBox()
        self.anki_context_type_combo.addItems([
            "Current Sentence Only",
            "Current Sentence with Adjacent (1 Sentence)"
        ])
        
        anki_context_layout.addWidget(self.anki_context_type_label)
        anki_context_layout.addWidget(self.anki_context_type_combo)
        self.anki_context_group.setLayout(anki_context_layout)
        
        # 添加设置组到主布局
        self.main_layout.addWidget(self.ai_context_group)
        self.main_layout.addWidget(self.anki_context_group)
        self.main_layout.addStretch()
        
        # 添加按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(button_box)
        
        # 加载配置
        self.load_config()
        
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 设置AI上下文类型
                    ai_context_type = config.get("ai_context_type", "Current Sentence Only")
                    index = self.ai_context_type_combo.findText(ai_context_type)
                    if index >= 0:
                        self.ai_context_type_combo.setCurrentIndex(index)
                        
                    # 设置Anki上下文类型
                    anki_context_type = config.get("anki_context_type", "Current Sentence Only")
                    index = self.anki_context_type_combo.findText(anki_context_type)
                    if index >= 0:
                        self.anki_context_type_combo.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load configuration: {str(e)}")
    
    def accept(self):
        """保存设置"""
        try:
            # 读取现有配置
            config = {}
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新上下文设置
            config["ai_context_type"] = self.ai_context_type_combo.currentText()
            config["anki_context_type"] = self.anki_context_type_combo.currentText()
            
            # 保存配置
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

class AIServiceSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Service Settings")
        self.setMinimumWidth(400)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 创建AI服务设置组
        self.service_group = QGroupBox("AI Service")
        service_layout = QVBoxLayout()
        
        # 服务类型选择
        self.service_type_label = QLabel("Service Type:")
        self.service_type_combo = QComboBox()
        self.service_type_combo.addItems(["OpenAI", "Custom Service"])
        self.service_type_combo.currentIndexChanged.connect(self.on_service_changed)
        
        service_layout.addWidget(self.service_type_label)
        service_layout.addWidget(self.service_type_combo)
        
        # OpenAI设置
        self.openai_group = QGroupBox("OpenAI Settings")
        openai_layout = QFormLayout()
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_base_edit = QLineEdit()
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-3.5-turbo", "gpt-4"])
        
        openai_layout.addRow("API Key:", self.api_key_edit)
        openai_layout.addRow("API Base:", self.api_base_edit)
        openai_layout.addRow("Model:", self.model_combo)
        self.openai_group.setLayout(openai_layout)
        
        # 自定义服务设置
        self.custom_group = QGroupBox("Custom Service Settings")
        custom_layout = QFormLayout()
        
        self.custom_api_key_edit = QLineEdit()
        self.custom_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.custom_base_edit = QLineEdit()
        self.custom_model_combo = QComboBox()
        self.custom_model_combo.setEditable(True)
        
        custom_layout.addRow("API Key:", self.custom_api_key_edit)
        custom_layout.addRow("API Base:", self.custom_base_edit)
        custom_layout.addRow("Model:", self.custom_model_combo)
        
        # 测试连接按钮
        self.test_button = QPushButton("Test Connection")
        custom_layout.addRow("", self.test_button)
        
        self.custom_group.setLayout(custom_layout)
        
        service_layout.addWidget(self.openai_group)
        service_layout.addWidget(self.custom_group)
        self.service_group.setLayout(service_layout)
        
        # 添加AI服务设置组到主布局
        self.main_layout.addWidget(self.service_group)
        self.main_layout.addStretch()
        
        # 添加按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(button_box)
        
        # 连接信号
        self.test_button.clicked.connect(self.test_connection)
        
        # 加载配置
        self.load_config()
        
        # 初始化UI状态
        self.on_service_changed(self.service_type_combo.currentIndex())
    
    def on_service_changed(self, index):
        """处理服务类型切换"""
        is_openai = index == 0
        self.openai_group.setVisible(is_openai)
        self.custom_group.setVisible(not is_openai)
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 设置服务类型
                    service_type = config.get("service_type", "OpenAI")
                    index = self.service_type_combo.findText(service_type)
                    if index >= 0:
                        self.service_type_combo.setCurrentIndex(index)
                    
                    # OpenAI设置
                    openai_config = config.get("openai", {})
                    self.api_key_edit.setText(openai_config.get("api_key", ""))
                    self.api_base_edit.setText(openai_config.get("api_base", ""))
                    model = openai_config.get("model", "gpt-3.5-turbo")
                    index = self.model_combo.findText(model)
                    if index >= 0:
                        self.model_combo.setCurrentIndex(index)
                    
                    # 自定义API设置
                    custom_config = config.get("custom", {})
                    self.custom_api_key_edit.setText(custom_config.get("api_key", ""))
                    self.custom_base_edit.setText(custom_config.get("api_base", ""))
                    model = custom_config.get("model", "gpt-3.5-turbo")
                    self.custom_model_combo.setCurrentText(model)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load configuration: {str(e)}")
    
    def get_current_config(self) -> Dict:
        """获取当前配置"""
        is_openai = self.service_type_combo.currentText() == "OpenAI"
        
        if is_openai:
            return {
                "api_key": self.api_key_edit.text(),
                "api_base": self.api_base_edit.text(),
                "model": self.model_combo.currentText()
            }
        else:
            return {
                "api_key": self.custom_api_key_edit.text(),
                "api_base": self.custom_base_edit.text(),
                "model": self.custom_model_combo.currentText()
            }
    
    def validate_config(self) -> bool:
        """验证配置"""
        is_openai = self.service_type_combo.currentText() == "OpenAI"
        
        if is_openai:
            if not self.api_key_edit.text().strip():
                QMessageBox.warning(self, "Error", "Please enter OpenAI API Key")
                return False
        else:
            if not self.custom_api_key_edit.text().strip():
                QMessageBox.warning(self, "Error", "Please enter API Key")
                return False
            if not self.custom_base_edit.text().strip():
                QMessageBox.warning(self, "Error", "Please enter API Base")
                return False
        
        return True
    
    def accept(self):
        """保存设置"""
        if not self.validate_config():
            return
            
        try:
            # 读取现有配置
            config = {}
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新AI服务设置
            config["service_type"] = self.service_type_combo.currentText()
            config["openai"] = {
                "api_key": self.api_key_edit.text(),
                "api_base": self.api_base_edit.text(),
                "model": self.model_combo.currentText()
            }
            config["custom"] = {
                "api_key": self.custom_api_key_edit.text(),
                "api_base": self.custom_base_edit.text(),
                "model": self.custom_model_combo.currentText()
            }
            
            # 保存配置
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def test_connection(self):
        """测试连接"""
        if not self.validate_config():
            return
        
        self.test_button.setEnabled(False)
        self.test_button.setText("Testing...")
        
        try:
            config = self.get_current_config()
            service_type = self.service_type_combo.currentText().lower().replace(" ", "")
            
            client = AIFactory.create_client(service_type, config)
            if not client:
                QMessageBox.warning(self, "Error", "Failed to create client, please check configuration")
                return
            
            try:
                response = run_async(client.translate("Hello, world!"))
                if response.error:
                    raise Exception(response.error)
                QMessageBox.information(self, "Success", "Connection test successful!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Connection test failed: {str(e)}")
        finally:
            self.test_button.setEnabled(True)
            self.test_button.setText("Test Connection")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(300)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 创建设置选项列表
        self.settings_list = QListWidget()
        self.settings_list.addItem("AI Service")
        self.settings_list.addItem("Context Settings")
        self.main_layout.addWidget(self.settings_list)
        
        # 添加按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(button_box)
        
        # 连接信号
        self.settings_list.itemDoubleClicked.connect(self.on_item_double_clicked)
    
    def on_item_double_clicked(self, item):
        """处理设置项双击事件"""
        if item.text() == "AI Service":
            dialog = AIServiceSettingsDialog(self)
            dialog.exec()
        elif item.text() == "Context Settings":
            dialog = ContextSettingsDialog(self)
            dialog.exec()