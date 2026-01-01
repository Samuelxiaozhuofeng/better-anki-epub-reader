import os
import sys
from aqt.qt import *
from aqt import mw
from aqt.utils import showInfo, showWarning
import atexit

from .utils.vendor_path import vendored_sys_path


def _patch_ankimorphs_settings_dialog_close() -> None:
    """Avoid Anki shutdown being blocked by AnkiMorphs settings dialog init race.

    AnkiMorphs creates SettingsDialog, then initializes it asynchronously via QueryOp.
    If Anki closes before _init_ui() runs, closeWithCallback() can raise because
    am_extra_settings is not set yet.
    """

    try:
        import sys as _sys
        import aqt as _aqt

        module_name = "472573498.settings.settings_dialog"
        mod = _sys.modules.get(module_name)
        if not mod:
            return

        settings_dialog_cls = getattr(mod, "SettingsDialog", None)
        if not settings_dialog_cls:
            return

        original = getattr(settings_dialog_cls, "closeWithCallback", None)
        if not callable(original) or getattr(original, "_epub_reader_safe_patched", False):
            return

        def _safe_close_with_callback(self, callback):  # type: ignore[no-untyped-def]
            am_extra_settings = getattr(self, "am_extra_settings", None)
            if am_extra_settings is not None:
                try:
                    am_extra_settings.save_settings_dialog_settings(
                        geometry=self.saveGeometry()
                    )
                except Exception:
                    pass

            try:
                self.close()
            finally:
                try:
                    globals_mod = _sys.modules.get("472573498.ankimorphs_globals")
                    dialog_name = getattr(globals_mod, "SETTINGS_DIALOG_NAME", None)
                    if dialog_name:
                        _aqt.dialogs.markClosed(dialog_name)
                except Exception:
                    pass

                try:
                    callback()
                except Exception:
                    pass

        _safe_close_with_callback._epub_reader_safe_patched = True  # type: ignore[attr-defined]
        settings_dialog_cls.closeWithCallback = _safe_close_with_callback
    except Exception:
        # Never block Anki startup/shutdown because of compatibility code.
        return

# 设置Qt高DPI缩放
if hasattr(Qt, 'AA_EnableHighDpiScaling'):  # 对于Qt5
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
elif hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):  # 对于Qt6
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

try:
    # 导入事件循环处理模块
    with vendored_sys_path():
        from .event_loop_handler import (
            cleanup_proactor_event_loop,
            setup_event_loop_policy,
            handle_event_loop_exception,
        )
        import asyncio
    
    # 设置事件循环策略
    setup_event_loop_policy()
    
    # 注册退出时的清理函数
    atexit.register(cleanup_proactor_event_loop)
    
    # 设置事件循环异常处理器
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_event_loop_exception)
    
    # 导入其他模块（这些模块可能依赖 vendor/ 内的第三方包）
    with vendored_sys_path():
        from .gui.reader_window import ReaderWindow
        from aqt import gui_hooks

    # Ensure Anki can close even if AnkiMorphs settings dialog is mid-initialization.
    gui_hooks.profile_will_close.append(_patch_ankimorphs_settings_dialog_close)

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
