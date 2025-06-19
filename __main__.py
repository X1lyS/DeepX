#!/usr/bin/env python3
"""
DeepX主模块入口
"""

import asyncio
import warnings
import sys
from deepx.cli import main

# 忽略asyncio的RuntimeError警告
if sys.platform.startswith('win'):
    # Windows上的asyncio事件循环关闭警告处理
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 定义自定义异常处理器，忽略事件循环已关闭的错误
    def custom_exception_handler(loop, context):
        exception = context.get('exception')
        if isinstance(exception, RuntimeError) and "Event loop is closed" in str(exception):
            # 忽略事件循环关闭的错误
            return
        loop.default_exception_handler(context)

    # 设置自定义异常处理器
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(custom_exception_handler)

    # 抑制特定的警告消息
    warnings.filterwarnings("ignore", 
                          message="There is no current event loop", 
                          category=RuntimeWarning)

if __name__ == "__main__":
    main() 