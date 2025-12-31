COMMON_DIALOG_QSS = """
    QDialog {
        background-color: #FFFFFF;
    }
    QLabel {
        color: #1D1D1F;
        font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
    }
    QGroupBox {
        border: 1px solid #E5E5EA;
        border-radius: 10px;
        margin-top: 12px;
        padding: 10px;
        font-family: "SF Pro Text", "-apple-system", "PingFang SC", "Microsoft YaHei";
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: #1D1D1F;
        font-weight: 600;
    }
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #FFFFFF;
        border: 1px solid #D2D2D7;
        border-radius: 8px;
        padding: 6px 10px;
    }
    QComboBox {
        background-color: #FFFFFF;
        border: 1px solid #D2D2D7;
        border-radius: 8px;
        padding: 6px 10px;
        min-width: 180px;
    }
    QPushButton {
        background-color: #FFFFFF;
        color: #1D1D1F;
        border: 1px solid #D2D2D7;
        border-radius: 8px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #F5F5F7;
    }
    QPushButton:pressed {
        background-color: #E5E5EA;
    }
    QPushButton[primary="true"] {
        background-color: #007AFF;
        color: #FFFFFF;
        border: none;
    }
    QPushButton[primary="true"]:hover {
        background-color: #0066D6;
    }
    QPushButton[primary="true"]:pressed {
        background-color: #0051A8;
    }
"""

