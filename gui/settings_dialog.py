from aqt.qt import *
from typing import Dict, Any, Optional
import json
from ..utils.ai_factory import AIFactory
from ..utils.ai_client import AIClient
from ..utils.template_manager import TemplateManager
from ..utils.async_utils import run_async
from ..utils.paths import config_json_path
from .dialog_styles import COMMON_DIALOG_QSS

CONFIG_PATH = config_json_path()

DIALOG_QSS = COMMON_DIALOG_QSS

class ContextSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("上下文设置")
        self.setMinimumWidth(400)
        self.setStyleSheet(DIALOG_QSS)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # AI上下文设置组
        self.ai_context_group = QGroupBox("AI 上下文范围")
        ai_context_layout = QVBoxLayout()
        
        self.ai_context_type_label = QLabel("AI 上下文：")
        self.ai_context_type_combo = QComboBox()
        self.ai_context_type_combo.addItem("仅当前句子", "Current Sentence Only")
        self.ai_context_type_combo.addItem("当前句子 + 前后各 1 句", "Current Sentence with Adjacent (1 Sentence)")
        
        ai_context_layout.addWidget(self.ai_context_type_label)
        ai_context_layout.addWidget(self.ai_context_type_combo)
        self.ai_context_group.setLayout(ai_context_layout)
        
        # Anki上下文设置组
        self.anki_context_group = QGroupBox("Anki 上下文范围")
        anki_context_layout = QVBoxLayout()
        
        self.anki_context_type_label = QLabel("Anki 上下文：")
        self.anki_context_type_combo = QComboBox()
        self.anki_context_type_combo.addItem("仅当前句子", "Current Sentence Only")
        self.anki_context_type_combo.addItem("当前句子 + 前后各 1 句", "Current Sentence with Adjacent (1 Sentence)")
        
        anki_context_layout.addWidget(self.anki_context_type_label)
        anki_context_layout.addWidget(self.anki_context_type_combo)
        self.anki_context_group.setLayout(anki_context_layout)

        # 查词面板字段设置组
        self.lookup_fields_group = QGroupBox("查词面板字段（可选）")
        lookup_fields_layout = QVBoxLayout()
        self.lookup_pos_checkbox = QCheckBox("词性（pos）")
        self.lookup_ipa_checkbox = QCheckBox("音标（ipa）")
        self.lookup_examples_checkbox = QCheckBox("例句（examples）")
        lookup_fields_layout.addWidget(self.lookup_pos_checkbox)
        lookup_fields_layout.addWidget(self.lookup_ipa_checkbox)
        lookup_fields_layout.addWidget(self.lookup_examples_checkbox)
        self.lookup_fields_group.setLayout(lookup_fields_layout)
        
        # 添加设置组到主布局
        self.main_layout.addWidget(self.ai_context_group)
        self.main_layout.addWidget(self.anki_context_group)
        self.main_layout.addWidget(self.lookup_fields_group)
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
                    for i in range(self.ai_context_type_combo.count()):
                        if self.ai_context_type_combo.itemData(i) == ai_context_type:
                            self.ai_context_type_combo.setCurrentIndex(i)
                            break
                        
                    # 设置Anki上下文类型
                    anki_context_type = config.get("anki_context_type", "Current Sentence Only")
                    for i in range(self.anki_context_type_combo.count()):
                        if self.anki_context_type_combo.itemData(i) == anki_context_type:
                            self.anki_context_type_combo.setCurrentIndex(i)
                            break

                    lookup_optional = config.get("lookup_optional_fields", {})
                    if isinstance(lookup_optional, dict):
                        self.lookup_pos_checkbox.setChecked(bool(lookup_optional.get("pos", False)))
                        self.lookup_ipa_checkbox.setChecked(bool(lookup_optional.get("ipa", False)))
                        self.lookup_examples_checkbox.setChecked(bool(lookup_optional.get("examples", False)))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置失败：{str(e)}")
    
    def accept(self):
        """保存设置"""
        try:
            # 读取现有配置
            config = {}
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新上下文设置
            config["ai_context_type"] = self.ai_context_type_combo.currentData()
            config["anki_context_type"] = self.anki_context_type_combo.currentData()
            config["lookup_optional_fields"] = {
                "pos": self.lookup_pos_checkbox.isChecked(),
                "ipa": self.lookup_ipa_checkbox.isChecked(),
                "examples": self.lookup_examples_checkbox.isChecked(),
            }
            
            # 保存配置
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败：{str(e)}")

class AIServiceSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 服务设置")
        self.setMinimumWidth(400)
        self.setStyleSheet(DIALOG_QSS)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 创建AI服务设置组
        self.service_group = QGroupBox("AI 服务")
        service_layout = QVBoxLayout()
        
        # 服务类型选择
        self.service_type_label = QLabel("服务类型：")
        self.service_type_combo = QComboBox()
        self.service_type_combo.addItem("OpenAI", "openai")
        self.service_type_combo.addItem("自定义", "custom")
        self.service_type_combo.currentIndexChanged.connect(self.on_service_changed)
        
        service_layout.addWidget(self.service_type_label)
        service_layout.addWidget(self.service_type_combo)
        
        # OpenAI设置
        self.openai_group = QGroupBox("OpenAI 设置")
        openai_layout = QFormLayout()
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_base_edit = QLineEdit()
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-3.5-turbo", "gpt-4"])
        
        openai_layout.addRow("API Key：", self.api_key_edit)
        openai_layout.addRow("API Base：", self.api_base_edit)
        openai_layout.addRow("模型：", self.model_combo)
        self.openai_group.setLayout(openai_layout)
        
        # 自定义服务设置
        self.custom_group = QGroupBox("自定义服务设置")
        custom_layout = QFormLayout()
        
        self.custom_api_key_edit = QLineEdit()
        self.custom_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.custom_base_edit = QLineEdit()
        self.custom_model_combo = QComboBox()
        self.custom_model_combo.setEditable(True)
        
        custom_layout.addRow("API Key：", self.custom_api_key_edit)
        custom_layout.addRow("API Base：", self.custom_base_edit)
        custom_layout.addRow("模型：", self.custom_model_combo)
        
        # 测试连接按钮
        self.test_button = QPushButton("测试连接")
        self.test_button.setProperty("primary", True)
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
        is_openai = self.service_type_combo.itemData(index) == "openai"
        self.openai_group.setVisible(is_openai)
        self.custom_group.setVisible(not is_openai)
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 设置服务类型
                    service_type_raw = str(config.get("service_type", "openai"))
                    service_type_norm = service_type_raw.lower().replace(" ", "")
                    if "openai" in service_type_norm:
                        service_type = "openai"
                    elif "custom" in service_type_norm:
                        service_type = "custom"
                    else:
                        service_type = "openai"

                    for i in range(self.service_type_combo.count()):
                        if self.service_type_combo.itemData(i) == service_type:
                            self.service_type_combo.setCurrentIndex(i)
                            break
                    
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
            QMessageBox.warning(self, "错误", f"加载配置失败：{str(e)}")
    
    def get_current_config(self) -> Dict:
        """获取当前配置"""
        is_openai = self.service_type_combo.currentData() == "openai"
        
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
        is_openai = self.service_type_combo.currentData() == "openai"
        
        if is_openai:
            if not self.api_key_edit.text().strip():
                QMessageBox.warning(self, "错误", "请输入 OpenAI API Key。")
                return False
        else:
            if not self.custom_api_key_edit.text().strip():
                QMessageBox.warning(self, "错误", "请输入 API Key。")
                return False
            if not self.custom_base_edit.text().strip():
                QMessageBox.warning(self, "错误", "请输入 API Base。")
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
            config["service_type"] = self.service_type_combo.currentData()
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
            QMessageBox.critical(self, "错误", f"保存设置失败：{str(e)}")
    
    def test_connection(self):
        """测试连接"""
        if not self.validate_config():
            return
        
        self.test_button.setEnabled(False)
        self.test_button.setText("测试中...")
        
        try:
            config = self.get_current_config()
            service_type = self.service_type_combo.currentData()
            
            client = AIFactory.create_client(service_type, config)
            if not client:
                QMessageBox.warning(self, "错误", "无法创建客户端，请检查配置。")
                return
            
            try:
                response = run_async(client.explain("测试连接"))
                if response.error:
                    raise Exception(response.error)
                QMessageBox.information(self, "成功", "连接测试成功！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"连接测试失败：{str(e)}")
        finally:
            self.test_button.setEnabled(True)
            self.test_button.setText("测试连接")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(300)
        self.setStyleSheet(DIALOG_QSS)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 创建设置选项列表
        self.settings_list = QListWidget()
        self.settings_list.addItem("AI 服务")
        self.settings_list.addItem("上下文设置")
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
        if item.text() == "AI 服务":
            dialog = AIServiceSettingsDialog(self)
            dialog.exec()
        elif item.text() == "上下文设置":
            dialog = ContextSettingsDialog(self)
            dialog.exec()
