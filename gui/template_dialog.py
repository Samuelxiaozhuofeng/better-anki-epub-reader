from __future__ import annotations

from typing import Dict, List

from aqt.qt import *

from ..utils.lookup_preferences import (
    LANGUAGE_OPTIONS,
    PRESET_STYLE_OPTIONS,
    load_lookup_preferences,
    save_lookup_preferences,
)
from ..utils.paths import config_json_path
from .dialog_styles import COMMON_DIALOG_QSS


DIALOG_QSS = (
    COMMON_DIALOG_QSS
    + """
    QGroupBox {
        font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
    }
    QLabel, QCheckBox, QComboBox, QLineEdit, QTextEdit {
        font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
    }
"""
)


class TemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查词解释设置")
        self.setStyleSheet(DIALOG_QSS)
        self.setMinimumWidth(620)

        self._preferences = load_lookup_preferences()
        self._custom_styles: List[Dict[str, str]] = [
            dict(item) for item in self._preferences.get("lookup_custom_styles", [])
        ]

        self._build_ui()
        self._load_config_into_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        style_group = QGroupBox("1) 当前解释风格")
        style_layout = QVBoxLayout(style_group)
        self.style_combo = QComboBox()
        for style_id, label in PRESET_STYLE_OPTIONS:
            self.style_combo.addItem(label, style_id)
        self.style_combo.currentIndexChanged.connect(self._on_style_changed)
        style_layout.addWidget(self.style_combo)
        layout.addWidget(style_group)

        self.custom_group = QGroupBox("2) 自定义风格库")
        custom_layout = QVBoxLayout(self.custom_group)

        custom_selector_layout = QHBoxLayout()
        custom_selector_layout.addWidget(QLabel("已保存风格："))
        self.custom_style_combo = QComboBox()
        self.custom_style_combo.currentIndexChanged.connect(self._on_custom_style_selected)
        custom_selector_layout.addWidget(self.custom_style_combo, 1)
        custom_layout.addLayout(custom_selector_layout)

        custom_name_layout = QHBoxLayout()
        custom_name_layout.addWidget(QLabel("风格名称："))
        self.custom_name_edit = QLineEdit()
        self.custom_name_edit.setPlaceholderText("例如：三岁孩子也能听懂")
        custom_name_layout.addWidget(self.custom_name_edit, 1)
        custom_layout.addLayout(custom_name_layout)

        custom_layout.addWidget(QLabel("风格说明："))
        self.custom_instruction_edit = QTextEdit()
        self.custom_instruction_edit.setPlaceholderText(
            "例如：请像给三岁孩子解释一样，使用很短的句子、简单词汇，避免术语。"
        )
        self.custom_instruction_edit.setMinimumHeight(180)
        custom_layout.addWidget(self.custom_instruction_edit)

        custom_button_layout = QHBoxLayout()
        self.new_custom_button = QPushButton("新建风格")
        self.save_custom_button = QPushButton("保存当前风格")
        self.delete_custom_button = QPushButton("删除当前风格")
        self.new_custom_button.clicked.connect(self._create_new_custom_style)
        self.save_custom_button.clicked.connect(self._save_current_custom_style)
        self.delete_custom_button.clicked.connect(self._delete_current_custom_style)
        custom_button_layout.addWidget(self.new_custom_button)
        custom_button_layout.addWidget(self.save_custom_button)
        custom_button_layout.addWidget(self.delete_custom_button)
        custom_layout.addLayout(custom_button_layout)
        layout.addWidget(self.custom_group)

        language_group = QGroupBox("3) 解释语言")
        language_layout = QVBoxLayout(language_group)
        self.language_combo = QComboBox()
        for lang_id, label in LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, lang_id)
        language_layout.addWidget(self.language_combo)
        layout.addWidget(language_group)

        fields_group = QGroupBox("4) 展示字段")
        fields_layout = QVBoxLayout(fields_group)
        fields_layout.addWidget(QLabel("必选字段（固定）：word / basic_meaning / contextual_meaning"))
        self.pos_checkbox = QCheckBox("词性（pos）")
        self.ipa_checkbox = QCheckBox("音标（ipa）")
        self.examples_checkbox = QCheckBox("例句（examples）")
        fields_layout.addWidget(self.pos_checkbox)
        fields_layout.addWidget(self.ipa_checkbox)
        fields_layout.addWidget(self.examples_checkbox)
        layout.addWidget(fields_group)

        info = QLabel(
            "说明：\n"
            "- 这里只允许你定义“解释风格”，输出结构仍由系统后台固定约束为 JSON。\n"
            "- AI 会根据你的语言和风格要求组织内容，但不会改变字段格式。\n"
            "- 配置保存位置："
            f"{config_json_path()}"
        )
        info.setWordWrap(True)
        info.setStyleSheet("QLabel { color: #4A4A4A; }")
        layout.addWidget(info)

        buttons = QDialogButtonBox()
        self.apply_button = buttons.addButton("保存并关闭", QDialogButtonBox.ButtonRole.AcceptRole)
        self.close_button = buttons.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        self.apply_button.clicked.connect(self.save_settings)
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _load_config_into_ui(self) -> None:
        prefs = self._preferences
        style_mode = prefs.get("lookup_style_mode", "preset")
        preset_style = prefs.get("lookup_style_preset", "friendly")

        target_style = "custom" if style_mode == "custom" else preset_style
        for i in range(self.style_combo.count()):
            if self.style_combo.itemData(i) == target_style:
                self.style_combo.setCurrentIndex(i)
                break

        language = str(prefs.get("lookup_language", "zh"))
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == language:
                self.language_combo.setCurrentIndex(i)
                break

        fields = prefs.get("lookup_optional_fields", {})
        self.pos_checkbox.setChecked(bool(fields.get("pos", False)))
        self.ipa_checkbox.setChecked(bool(fields.get("ipa", False)))
        self.examples_checkbox.setChecked(bool(fields.get("examples", False)))

        self._refresh_custom_style_combo()
        self._set_selected_custom_style(prefs.get("lookup_active_custom_style_id", ""))
        self._sync_custom_group_enabled()

    def _refresh_custom_style_combo(self) -> None:
        current_id = self.custom_style_combo.currentData()
        self.custom_style_combo.blockSignals(True)
        self.custom_style_combo.clear()
        for item in self._custom_styles:
            self.custom_style_combo.addItem(item["name"], item["id"])
        self.custom_style_combo.blockSignals(False)

        if self.custom_style_combo.count() == 0:
            self.custom_name_edit.clear()
            self.custom_instruction_edit.clear()
            return

        if current_id:
            self._set_selected_custom_style(current_id)
        else:
            self.custom_style_combo.setCurrentIndex(0)
            self._load_selected_custom_style()

    def _set_selected_custom_style(self, style_id: str) -> None:
        for i in range(self.custom_style_combo.count()):
            if self.custom_style_combo.itemData(i) == style_id:
                self.custom_style_combo.setCurrentIndex(i)
                self._load_selected_custom_style()
                return
        if self.custom_style_combo.count() > 0:
            self.custom_style_combo.setCurrentIndex(0)
            self._load_selected_custom_style()
        else:
            self.custom_name_edit.clear()
            self.custom_instruction_edit.clear()

    def _load_selected_custom_style(self) -> None:
        style = self._get_selected_custom_style()
        if not style:
            self.custom_name_edit.clear()
            self.custom_instruction_edit.clear()
            return
        self.custom_name_edit.setText(style["name"])
        self.custom_instruction_edit.setPlainText(style["instruction"])

    def _on_style_changed(self) -> None:
        self._sync_custom_group_enabled()

    def _sync_custom_group_enabled(self) -> None:
        is_custom = self.style_combo.currentData() == "custom"
        self.custom_group.setEnabled(is_custom)
        if is_custom and not self._custom_styles:
            self._create_new_custom_style()

    def _on_custom_style_selected(self) -> None:
        self._load_selected_custom_style()

    def _get_selected_custom_style(self) -> Dict[str, str] | None:
        style_id = self.custom_style_combo.currentData()
        for item in self._custom_styles:
            if item["id"] == style_id:
                return item
        return None

    def _next_custom_style_id(self) -> str:
        used_ids = {item["id"] for item in self._custom_styles}
        index = 1
        while True:
            candidate = f"custom_{index}"
            if candidate not in used_ids:
                return candidate
            index += 1

    def _create_new_custom_style(self) -> None:
        new_style = {
            "id": self._next_custom_style_id(),
            "name": f"自定义风格 {len(self._custom_styles) + 1}",
            "instruction": "",
        }
        self._custom_styles.append(new_style)
        self._refresh_custom_style_combo()
        self._set_selected_custom_style(new_style["id"])
        self.custom_name_edit.selectAll()
        self.custom_name_edit.setFocus()

    def _save_current_custom_style(self) -> bool:
        style = self._get_selected_custom_style()
        if not style:
            QMessageBox.warning(self, "提示", "请先新建一个自定义风格。")
            return False

        name = self.custom_name_edit.text().strip()
        instruction = self.custom_instruction_edit.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请填写风格名称。")
            return False
        if not instruction:
            QMessageBox.warning(self, "提示", "请填写风格说明。")
            return False

        style["name"] = name
        style["instruction"] = instruction
        self._refresh_custom_style_combo()
        self._set_selected_custom_style(style["id"])
        return True

    def _delete_current_custom_style(self) -> None:
        style = self._get_selected_custom_style()
        if not style:
            return

        confirm = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除自定义风格“{style['name']}”吗？",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._custom_styles = [item for item in self._custom_styles if item["id"] != style["id"]]
        self._refresh_custom_style_combo()
        self._sync_custom_group_enabled()

    def save_settings(self) -> None:
        try:
            if self.style_combo.currentData() == "custom" and not self._save_current_custom_style():
                return

            preferences = {
                "lookup_language": self.language_combo.currentData(),
                "lookup_style_mode": "custom" if self.style_combo.currentData() == "custom" else "preset",
                "lookup_style_preset": self.style_combo.currentData()
                if self.style_combo.currentData() in {"friendly", "formal", "humorous"}
                else "friendly",
                "lookup_custom_styles": self._custom_styles,
                "lookup_active_custom_style_id": self.custom_style_combo.currentData() or "",
                "lookup_optional_fields": {
                    "pos": self.pos_checkbox.isChecked(),
                    "ipa": self.ipa_checkbox.isChecked(),
                    "examples": self.examples_checkbox.isChecked(),
                },
            }
            save_lookup_preferences(preferences)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存失败：{str(e)}")
