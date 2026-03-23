import json
import os
from typing import Dict, Any, Optional

from aqt.qt import *
from ..utils.ai_factory import AIFactory
from ..utils.ai_client import AIClient, fetch_available_models
from ..utils.async_utils import run_async
from ..utils.paths import config_json_path
from .dialog_styles import COMMON_DIALOG_QSS

CONFIG_PATH = config_json_path()

DIALOG_QSS = COMMON_DIALOG_QSS
AI_CONTEXT_CURRENT_ONLY = "Current Sentence Only"
AI_CONTEXT_CUSTOM_ADJACENT = "Current Sentence with Adjacent (Custom)"
AI_CONTEXT_LEGACY_ADJACENT = "Current Sentence with Adjacent (1 Sentence)"

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
        ai_context_layout = QFormLayout()
        
        self.ai_context_type_label = QLabel("AI 上下文：")
        self.ai_context_type_combo = QComboBox()
        self.ai_context_type_combo.addItem("仅当前句子", AI_CONTEXT_CURRENT_ONLY)
        self.ai_context_type_combo.addItem("当前句子 + 前后各 N 句", AI_CONTEXT_CUSTOM_ADJACENT)
        self.ai_context_type_combo.currentIndexChanged.connect(self.on_ai_context_type_changed)

        self.ai_context_count_label = QLabel("前后句子数：")
        self.ai_context_count_spinbox = QSpinBox()
        self.ai_context_count_spinbox.setRange(1, 99)
        self.ai_context_count_spinbox.setValue(1)
        self.ai_context_count_spinbox.setSuffix(" 句")
        self.ai_context_count_spinbox.setToolTip("输入 N 后，将包含当前句子以及前后各 N 句")
        
        ai_context_layout.addRow(self.ai_context_type_label, self.ai_context_type_combo)
        ai_context_layout.addRow(self.ai_context_count_label, self.ai_context_count_spinbox)
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
        self.on_ai_context_type_changed(self.ai_context_type_combo.currentIndex())
        
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 设置AI上下文类型
                    ai_context_type = config.get("ai_context_type", AI_CONTEXT_CURRENT_ONLY)
                    if ai_context_type == AI_CONTEXT_LEGACY_ADJACENT:
                        ai_context_type = AI_CONTEXT_CUSTOM_ADJACENT
                        ai_context_count = 1
                    else:
                        ai_context_count = int(config.get("ai_context_adjacent_count", 1) or 1)

                    ai_context_count = max(1, ai_context_count)
                    self.ai_context_count_spinbox.setValue(ai_context_count)

                    for i in range(self.ai_context_type_combo.count()):
                        if self.ai_context_type_combo.itemData(i) == ai_context_type:
                            self.ai_context_type_combo.setCurrentIndex(i)
                            break
                        
                    # 设置Anki上下文类型
                    anki_context_type = config.get("anki_context_type", AI_CONTEXT_CURRENT_ONLY)
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

    def on_ai_context_type_changed(self, index):
        """根据 AI 上下文模式切换数量输入框状态"""
        use_adjacent = self.ai_context_type_combo.itemData(index) == AI_CONTEXT_CUSTOM_ADJACENT
        self.ai_context_count_label.setEnabled(use_adjacent)
        self.ai_context_count_spinbox.setEnabled(use_adjacent)
    
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
            config["ai_context_adjacent_count"] = self.ai_context_count_spinbox.value()
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
        self.fetch_openai_models_button = QPushButton("获取模型")

        openai_model_layout = QHBoxLayout()
        openai_model_layout.addWidget(self.model_combo)
        openai_model_layout.addWidget(self.fetch_openai_models_button)
        
        openai_layout.addRow("API Key：", self.api_key_edit)
        openai_layout.addRow("API Base：", self.api_base_edit)
        openai_layout.addRow("模型：", openai_model_layout)
        self.openai_group.setLayout(openai_layout)
        
        # 自定义服务设置
        self.custom_group = QGroupBox("自定义服务设置")
        custom_layout = QFormLayout()
        
        self.custom_api_key_edit = QLineEdit()
        self.custom_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.custom_base_edit = QLineEdit()
        self.custom_model_combo = QComboBox()
        self.fetch_custom_models_button = QPushButton("获取模型")

        custom_model_layout = QHBoxLayout()
        custom_model_layout.addWidget(self.custom_model_combo)
        custom_model_layout.addWidget(self.fetch_custom_models_button)
        
        custom_layout.addRow("API Key：", self.custom_api_key_edit)
        custom_layout.addRow("API Base：", self.custom_base_edit)
        custom_layout.addRow("模型：", custom_model_layout)
        
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
        self.fetch_openai_models_button.clicked.connect(
            lambda: self.fetch_models_for_service("openai")
        )
        self.fetch_custom_models_button.clicked.connect(
            lambda: self.fetch_models_for_service("custom")
        )
        
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
                    self.set_combo_items(self.model_combo, [model], selected=model)
                    
                    # 自定义API设置
                    custom_config = config.get("custom", {})
                    self.custom_api_key_edit.setText(custom_config.get("api_key", ""))
                    self.custom_base_edit.setText(custom_config.get("api_base", ""))
                    model = custom_config.get("model", "gpt-3.5-turbo")
                    self.set_combo_items(self.custom_model_combo, [model], selected=model)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置失败：{str(e)}")

    def set_combo_items(self, combo: QComboBox, items, selected: str = ""):
        """更新模型下拉框，并尽量保留当前选择"""
        normalized_items = []
        for item in items:
            item_text = str(item).strip()
            if item_text and item_text not in normalized_items:
                normalized_items.append(item_text)

        combo.blockSignals(True)
        combo.clear()
        combo.addItems(normalized_items)

        target = (selected or combo.currentText()).strip()
        if target:
            index = combo.findText(target)
            if index < 0:
                combo.addItem(target)
                index = combo.findText(target)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)
    
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
            if not self.model_combo.currentText().strip():
                QMessageBox.warning(self, "错误", "请先获取并选择模型。")
                return False
        else:
            if not self.custom_api_key_edit.text().strip():
                QMessageBox.warning(self, "错误", "请输入 API Key。")
                return False
            if not self.custom_base_edit.text().strip():
                QMessageBox.warning(self, "错误", "请输入 API Base。")
                return False
            if not self.custom_model_combo.currentText().strip():
                QMessageBox.warning(self, "错误", "请先获取并选择模型。")
                return False
        
        return True

    def get_service_credentials(self, service_type: str) -> Dict[str, str]:
        """读取指定服务当前输入的鉴权信息"""
        if service_type == "openai":
            return {
                "api_key": self.api_key_edit.text().strip(),
                "api_base": self.api_base_edit.text().strip(),
            }
        return {
            "api_key": self.custom_api_key_edit.text().strip(),
            "api_base": self.custom_base_edit.text().strip(),
        }

    def set_fetch_button_state(self, service_type: str, loading: bool):
        """更新获取模型按钮状态"""
        button = (
            self.fetch_openai_models_button
            if service_type == "openai"
            else self.fetch_custom_models_button
        )
        button.setEnabled(not loading)
        button.setText("获取中..." if loading else "获取模型")

    def fetch_models_for_service(self, service_type: str):
        """根据 API Base 拉取可用模型"""
        credentials = self.get_service_credentials(service_type)
        api_key = credentials["api_key"]
        api_base = credentials["api_base"]

        if service_type == "openai" and not api_key:
            QMessageBox.warning(self, "错误", "请先输入 OpenAI API Key。")
            return
        if service_type == "custom":
            if not api_key:
                QMessageBox.warning(self, "错误", "请先输入 API Key。")
                return
            if not api_base:
                QMessageBox.warning(self, "错误", "请先输入 API Base。")
                return

        combo = self.model_combo if service_type == "openai" else self.custom_model_combo
        current_model = combo.currentText().strip()

        self.set_fetch_button_state(service_type, True)
        try:
            models = run_async(fetch_available_models(api_base=api_base, api_key=api_key))
            selected_model = current_model if current_model in models else (models[0] if models else "")
            self.set_combo_items(combo, models, selected=selected_model)
            QMessageBox.information(self, "成功", f"已获取 {len(models)} 个模型。")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取模型失败：{str(e)}")
        finally:
            self.set_fetch_button_state(service_type, False)
    
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
