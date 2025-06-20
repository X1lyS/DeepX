#!/usr/bin/env python3
"""
DeepX - 多接口集成的子域名收集工具
支持多个接口的集成，专注于发现隐藏子域名资产

用法:
    python DeepX.py example.com
    python DeepX.py collect example.com [--no-cache] [--no-brute]
    python DeepX.py fofa example.com
    python DeepX.py brute example.com
    python DeepX.py all example.com
"""

import os
import sys
import asyncio
import platform

# 在Windows平台上配置事件循环策略
if platform.system() == "Windows":
    # 为避免 "Event loop is closed" 错误，使用 WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 导入CLI模块
from core.cli import main

# 主程序入口
if __name__ == "__main__":
    try:
        # 执行命令行接口
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc() 