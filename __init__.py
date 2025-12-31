import os
import sys
from aqt.qt import *
from aqt import mw
from aqt.utils import showInfo, showWarning
import atexit

# 设置Qt高DPI缩放
if hasattr(Qt, 'AA_EnableHighDpiScaling'):  # 对于Qt5
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
elif hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):  # 对于Qt6
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

# 添加vendor目录到Python路径
vendor_dir = os.path.join(os.path.dirname(__file__), 'vendor')
sys.path.insert(0, vendor_dir)

try:
    # 导入事件循环处理模块
    from .event_loop_handler import cleanup_proactor_event_loop, setup_event_loop_policy, handle_event_loop_exception
    import asyncio
    
    # 设置事件循环策略
    setup_event_loop_policy()
    
    # 注册退出时的清理函数
    atexit.register(cleanup_proactor_event_loop)
    
    # 设置事件循环异常处理器
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_event_loop_exception)
    
    # 导入其他模块
    from .gui.reader_window import ReaderWindow

    def show_reader():
        """显示阅读器窗口"""
        # 创建阅读器窗口
        reader = ReaderWindow(mw)
        # 设置为Qt.WindowType.Window，使其成为独立窗口
        reader.setWindowFlags(Qt.WindowType.Window)
        # 显示窗口
        reader.show()
        # 保持窗口引用，防止被垃圾回收
        mw.anki_reader = reader

    # 创建菜单项
    action = QAction("阅读器", mw)
    action.triggered.connect(show_reader)
    mw.form.menuTools.addAction(action)
except ImportError as e:
    showWarning(f"加载阅读器插件失败：{str(e)}\n请确保所有依赖都已正确安装。") 