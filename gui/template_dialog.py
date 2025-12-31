from __future__ import annotations

import json
import os
from typing import Dict

from aqt.qt import *

from ..utils.paths import config_json_path, addon_data_root
from .dialog_styles import COMMON_DIALOG_QSS


DIALOG_QSS = (
    COMMON_DIALOG_QSS
    + """
    QGroupBox {
        font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
    }
    QLabel, QCheckBox, QComboBox {
        font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
    }
"""
)


STYLE_PRESETS = [
    ("formal", "正式学术"),
    ("friendly", "友好讲解"),
    ("humorous", "轻松幽默"),
]

LANGUAGE_PRESETS = [
    ("zh", "中文"),
    ("en", "English"),
    ("es", "Español"),
]


class TemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查词解释设置")
        self.setStyleSheet(DIALOG_QSS)
        self.setMinimumWidth(520)

        self._build_ui()
        self._load_config_into_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        style_group = QGroupBox("1) 解释风格")
        style_layout = QVBoxLayout(style_group)
        self.style_combo = QComboBox()
        for style_id, label in STYLE_PRESETS:
            self.style_combo.addItem(label, style_id)
        style_layout.addWidget(self.style_combo)
        layout.addWidget(style_group)

        language_group = QGroupBox("2) 解释语言")
        language_layout = QVBoxLayout(language_group)
        self.language_combo = QComboBox()
        for lang_id, label in LANGUAGE_PRESETS:
            self.language_combo.addItem(label, lang_id)
        language_layout.addWidget(self.language_combo)
        layout.addWidget(language_group)

        fields_group = QGroupBox("3) 展示字段")
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
            "- 这里的选择会影响模型输出内容与查词面板展示。\n"
            "- 系统会自动强制模型只输出 JSON，不需要手写 prompt。\n"
            f"- 配置保存位置：{config_json_path()}"
        )
        info.setWordWrap(True)
        info.setStyleSheet("QLabel { color: #4A4A4A; }")
        layout.addWidget(info)

        buttons = QDialogButtonBox()
        self.apply_button = buttons.addButton("保存", QDialogButtonBox.ButtonRole.ApplyRole)
        self.close_button = buttons.addButton("关闭", QDialogButtonBox.ButtonRole.RejectRole)
        self.apply_button.clicked.connect(self.save_settings)
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _load_config(self) -> Dict:
        path = config_json_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if isinstance(cfg, dict):
                    return cfg
            except Exception:
                pass
        return {}

    def _save_config(self, cfg: Dict) -> None:
        os.makedirs(addon_data_root(), exist_ok=True)
        with open(config_json_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)

    def _load_config_into_ui(self) -> None:
        cfg = self._load_config()
        style_id = str(cfg.get("lookup_style", "friendly"))
        lang_id = str(cfg.get("lookup_language", "zh"))

        for i in range(self.style_combo.count()):
            if self.style_combo.itemData(i) == style_id:
                self.style_combo.setCurrentIndex(i)
                break

        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == lang_id:
                self.language_combo.setCurrentIndex(i)
                break

        fields = cfg.get("lookup_optional_fields", {})
        if isinstance(fields, dict):
            self.pos_checkbox.setChecked(bool(fields.get("pos", False)))
            self.ipa_checkbox.setChecked(bool(fields.get("ipa", False)))
            self.examples_checkbox.setChecked(bool(fields.get("examples", False)))

    def save_settings(self) -> None:
        try:
            cfg = self._load_config()
            cfg["lookup_style"] = self.style_combo.currentData()
            cfg["lookup_language"] = self.language_combo.currentData()
            cfg["lookup_optional_fields"] = {
                "pos": self.pos_checkbox.isChecked(),
                "ipa": self.ipa_checkbox.isChecked(),
                "examples": self.examples_checkbox.isChecked(),
            }
            self._save_config(cfg)
            QMessageBox.information(self, "成功", "设置已保存。")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存失败：{str(e)}")

