from aqt.qt import *
from ..utils.anki_handler import AnkiHandler
import json
import os
from ..utils.paths import note_config_path
from .dialog_styles import COMMON_DIALOG_QSS

DIALOG_QSS = COMMON_DIALOG_QSS

class NoteSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.anki_handler = AnkiHandler()
        self.config_path = note_config_path()
        self.setStyleSheet(DIALOG_QSS)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("笔记设置")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Create all components
        self.create_deck_group(layout)
        self.create_model_group(layout)
        self.create_field_group(layout)
        self.create_tag_group(layout)
        self.create_buttons(layout)
        
        self.setLayout(layout)
        
        # Load data
        self.load_decks()
        self.load_models()
        
        # Load data and then connect signals
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        
        # Trigger a model change event to load fields
        if self.model_combo.count() > 0:
            self.on_model_changed(0)
    
    def create_deck_group(self, layout):
        """Create deck selection group"""
        deck_group = QGroupBox("牌组")
        deck_layout = QFormLayout()
        self.deck_combo = QComboBox()
        deck_layout.addRow("选择牌组：", self.deck_combo)
        deck_group.setLayout(deck_layout)
        layout.addWidget(deck_group)
    
    def create_model_group(self, layout):
        """Create note type selection group"""
        model_group = QGroupBox("笔记类型")
        model_layout = QFormLayout()
        self.model_combo = QComboBox()
        model_layout.addRow("选择笔记类型：", self.model_combo)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
    
    def create_field_group(self, layout):
        """Create field mapping group"""
        field_group = QGroupBox("字段映射")
        field_layout = QFormLayout()
        
        # Word field
        self.word_field_combo = QComboBox()
        field_layout.addRow("单词字段：", self.word_field_combo)
        
        # Meaning field
        self.meaning_field_combo = QComboBox()
        field_layout.addRow("释义字段：", self.meaning_field_combo)
        
        # Context field
        self.context_field_combo = QComboBox()
        field_layout.addRow("上下文字段：", self.context_field_combo)
        
        field_group.setLayout(field_layout)
        layout.addWidget(field_group)
    
    def create_tag_group(self, layout):
        """Create tag settings group"""
        tag_group = QGroupBox("标签")
        tag_layout = QFormLayout()
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("多个标签用空格分隔")
        tag_layout.addRow("标签：", self.tag_edit)
        tag_group.setLayout(tag_layout)
        layout.addWidget(tag_group)
    
    def create_buttons(self, layout):
        """Create button group"""
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_decks(self):
        """Load deck list"""
        self.deck_combo.clear()
        decks = self.anki_handler.get_all_decks()
        self.deck_combo.addItems(decks)
    
    def load_models(self):
        """Load note type list"""
        self.model_combo.clear()
        models = self.anki_handler.get_all_models()
        self.model_combo.addItems(models)
    
    def on_model_changed(self, index):
        """Handle note type change"""
        if index < 0:
            return
            
        model_name = self.model_combo.currentText()
        fields = self.anki_handler.get_model_fields(model_name)
        
        # Update field selection dropdown
        for combo in [self.word_field_combo, self.meaning_field_combo, self.context_field_combo]:
            current_text = combo.currentText()
            combo.clear()
            combo.addItems(fields)
            # Try to restore previous selection
            index = combo.findText(current_text)
            if index >= 0:
                combo.setCurrentIndex(index)
    
    def load_settings(self):
        """Load settings"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # Set deck
                    deck_index = self.deck_combo.findText(config.get("deck_name", "Default"))
                    if deck_index >= 0:
                        self.deck_combo.setCurrentIndex(deck_index)
                    
                    # Set note type
                    model_index = self.model_combo.findText(config.get("model_name", "Basic"))
                    if model_index >= 0:
                        self.model_combo.setCurrentIndex(model_index)
                    
                    # Set field mapping
                    field_mapping = config.get("field_mapping", {})
                    if "word" in field_mapping:
                        index = self.word_field_combo.findText(field_mapping["word"])
                        if index >= 0:
                            self.word_field_combo.setCurrentIndex(index)
                    
                    if "meaning" in field_mapping:
                        index = self.meaning_field_combo.findText(field_mapping["meaning"])
                        if index >= 0:
                            self.meaning_field_combo.setCurrentIndex(index)
                    
                    if "context" in field_mapping:
                        index = self.context_field_combo.findText(field_mapping["context"])
                        if index >= 0:
                            self.context_field_combo.setCurrentIndex(index)
                    
                    # Set tags
                    self.tag_edit.setText(" ".join(config.get("tags", [])))
        except Exception as e:
            print(f"Failed to load note settings: {str(e)}")
    
    def save_settings(self):
        """Save settings"""
        try:
            config = {
                "deck_name": self.deck_combo.currentText(),
                "model_name": self.model_combo.currentText(),
                "field_mapping": {
                    "word": self.word_field_combo.currentText(),
                    "meaning": self.meaning_field_combo.currentText(),
                    "context": self.context_field_combo.currentText()
                },
                "tags": [tag.strip() for tag in self.tag_edit.text().split() if tag.strip()]
            }
            
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败：{str(e)}") 
