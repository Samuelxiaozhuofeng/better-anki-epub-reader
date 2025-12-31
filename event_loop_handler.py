import asyncio
import sys
import warnings
from contextlib import suppress
from typing import Optional, Set

def cleanup_proactor_event_loop() -> None:
    """清理 Windows ProactorEventLoop 的资源，避免关闭时的警告信息"""
    loop: Optional[asyncio.AbstractEventLoop] = None
    try:
        # 获取当前事件循环
        loop = asyncio.get_event_loop()
    except Exception:
        return

    if loop is None or not isinstance(loop, asyncio.ProactorEventLoop):
        return

    # 关闭事件循环前的清理工作
    with suppress(Exception):
        # 取消所有待处理的任务
        pending = asyncio.all_tasks(loop)
        if pending:
            for task in pending:
                task.cancel()
            with suppress(asyncio.CancelledError):
                loop.run_until_complete(asyncio.gather(*pending))

        # 停止事件循环
        if not loop.is_closed():
            loop.call_soon(loop.stop)
            loop.run_forever()
            loop.close()

def setup_event_loop_policy() -> None:
    """设置合适的事件循环策略"""
    if sys.platform == 'win32':
        # Windows 平台使用 WindowsSelectorEventLoopPolicy 来避免 ProactorEventLoop 的问题
        with suppress(Exception):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def handle_event_loop_exception(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    """处理事件循环中的异常"""
    message = context.get('message')
    exception = context.get('exception')
    
    if isinstance(exception, asyncio.CancelledError):
        return  # 忽略取消操作导致的异常
        
    if "Event loop is closed" in str(exception):
        return  # 忽略事件循环关闭的警告
        
    # 其他异常则记录警告信息
    warning_message = f"Event loop exception: {message}\n{exception}"
    warnings.warn(warning_message, RuntimeWarning) 