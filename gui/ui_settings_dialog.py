from aqt.qt import *

class Ui_SettingsDialog:
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        SettingsDialog.resize(500, 400)
        
        # 主布局
        self.verticalLayout = QVBoxLayout(SettingsDialog)
        
        # 创建标签页
        self.tabWidget = QTabWidget(SettingsDialog)
        self.verticalLayout.addWidget(self.tabWidget)
        
        # AI服务设置标签页
        self.aiServiceTab = QWidget()
        self.tabWidget.addTab(self.aiServiceTab, "AI服务设置")
        self.serviceLayout = QVBoxLayout(self.aiServiceTab)
        
        # AI服务类型选择
        self.serviceGroupBox = QGroupBox("AI服务类型", self.aiServiceTab)
        self.serviceTypeLayout = QVBoxLayout(self.serviceGroupBox)
        
        self.serviceTypeCombo = QComboBox(self.serviceGroupBox)
        self.serviceTypeCombo.addItem("OpenAI")
        self.serviceTypeCombo.addItem("自定义API")
        self.serviceTypeLayout.addWidget(self.serviceTypeCombo)
        
        # OpenAI设置
        self.openaiGroup = QGroupBox("OpenAI设置", self.serviceGroupBox)
        self.openaiLayout = QFormLayout(self.openaiGroup)
        
        self.apiKeyEdit = QLineEdit(self.openaiGroup)
        self.apiKeyEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.openaiLayout.addRow("API Key:", self.apiKeyEdit)
        
        self.modelCombo = QComboBox(self.openaiGroup)
        self.modelCombo.addItems(["gpt-3.5-turbo", "gpt-4"])
        self.openaiLayout.addRow("模型:", self.modelCombo)
        
        self.apiBaseEdit = QLineEdit(self.openaiGroup)
        self.apiBaseEdit.setPlaceholderText("https://api.openai.com/v1")
        self.openaiLayout.addRow("API地址:", self.apiBaseEdit)
        
        self.serviceTypeLayout.addWidget(self.openaiGroup)
        
        # 自定义API设置
        self.customGroup = QGroupBox("自定义API设置", self.serviceGroupBox)
        self.customLayout = QFormLayout(self.customGroup)
        
        self.customApiKeyEdit = QLineEdit(self.customGroup)
        self.customApiKeyEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.customLayout.addRow("API Key:", self.customApiKeyEdit)
        
        self.customModelCombo = QComboBox(self.customGroup)
        self.customModelCombo.setEditable(True)
        self.customModelCombo.addItems(["gpt-3.5-turbo", "gpt-4", "claude-2", "gemini-pro"])
        self.customLayout.addRow("AI模型:", self.customModelCombo)
        
        self.customBaseEdit = QLineEdit(self.customGroup)
        self.customBaseEdit.setPlaceholderText("https://api.example.com/v1")
        self.customLayout.addRow("API地址:", self.customBaseEdit)
        
        self.serviceTypeLayout.addWidget(self.customGroup)
        self.serviceLayout.addWidget(self.serviceGroupBox)
        
        # 测试连接按钮
        self.testButton = QPushButton("测试连接", self.aiServiceTab)
        self.serviceLayout.addWidget(self.testButton)
        
        # 模板管理标签页
        self.templateTab = QWidget()
        self.tabWidget.addTab(self.templateTab, "模板管理")
        self.templateLayout = QVBoxLayout(self.templateTab)
        
        # 模板类型选择
        self.templateTypeGroup = QGroupBox("模板类型", self.templateTab)
        self.templateTypeLayout = QVBoxLayout(self.templateTypeGroup)
        
        self.templateTypeCombo = QComboBox(self.templateTypeGroup)
        self.templateTypeCombo.addItems(["单词释义模板"])
        self.templateTypeLayout.addWidget(self.templateTypeCombo)
        self.templateLayout.addWidget(self.templateTypeGroup)
        
        # 模板列表
        self.templateListGroup = QGroupBox("模板列表", self.templateTab)
        self.templateListLayout = QVBoxLayout(self.templateListGroup)
        
        self.templateList = QListWidget(self.templateListGroup)
        self.templateListLayout.addWidget(self.templateList)
        
        # 模板操作按钮
        self.templateButtonLayout = QHBoxLayout()
        self.addTemplateButton = QPushButton("添加模板", self.templateListGroup)
        self.editTemplateButton = QPushButton("编辑模板", self.templateListGroup)
        self.deleteTemplateButton = QPushButton("删除模板", self.templateListGroup)
        
        self.templateButtonLayout.addWidget(self.addTemplateButton)
        self.templateButtonLayout.addWidget(self.editTemplateButton)
        self.templateButtonLayout.addWidget(self.deleteTemplateButton)
        self.templateListLayout.addLayout(self.templateButtonLayout)
        
        # 模板编辑区域
        self.templateEditGroup = QGroupBox("模板编辑", self.templateListGroup)
        self.templateEditLayout = QVBoxLayout(self.templateEditGroup)
        
        self.templateNameEdit = QLineEdit(self.templateEditGroup)
        self.templateNameEdit.setPlaceholderText("模板名称")
        self.templateEditLayout.addWidget(self.templateNameEdit)
        
        self.templateContentEdit = QTextEdit(self.templateEditGroup)
        self.templateContentEdit.setPlaceholderText("在此输入模板内容...\n可使用 {word} 作为占位符")
        self.templateEditLayout.addWidget(self.templateContentEdit)
        
        self.templateListLayout.addWidget(self.templateEditGroup)
        self.templateLayout.addWidget(self.templateListGroup)
        
        # 按钮框
        self.buttonBox = QDialogButtonBox(SettingsDialog)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
        
        self.retranslateUi(SettingsDialog)
        self.buttonBox.accepted.connect(SettingsDialog.accept)
        self.buttonBox.rejected.connect(SettingsDialog.reject)
        QMetaObject.connectSlotsByName(SettingsDialog)
    
    def retranslateUi(self, SettingsDialog):
        _translate = QCoreApplication.translate
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "设置")) 