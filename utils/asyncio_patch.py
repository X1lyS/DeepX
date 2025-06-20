"""
asyncio补丁模块，用于解决Windows平台上的asyncio问题
"""

import sys
import asyncio
import warnings


def apply_asyncio_patches():
    """
    应用asyncio补丁，解决Windows平台上的事件循环问题
    """
    if sys.platform.startswith('win'):
        # 在Windows上，使用SelectorEventLoopPolicy而不是ProactorEventLoopPolicy
        # 这可以避免某些与标准输入/输出相关的问题以及事件循环关闭时的异常
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except (ImportError, AttributeError):
            warnings.warn("无法设置WindowsSelectorEventLoopPolicy，某些asyncio功能可能不稳定")
            
        # 禁用特定的asyncio警告，这些警告通常是误报
        warnings.filterwarnings(
            "ignore", 
            message="There is no current event loop", 
            category=RuntimeWarning
        )
        
        # 忽略"Event loop is closed"警告
        warnings.filterwarnings(
            "ignore",
            message="Event loop is closed",
            category=RuntimeWarning
        )
        
    # 设置更大的默认线程栈大小，以避免某些深度递归操作引起的栈溢出
    try:
        import threading
        threading.stack_size(1024 * 1024)  # 1MB栈大小
    except (ImportError, RuntimeError):
        pass 