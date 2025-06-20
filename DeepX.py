#!/usr/bin/env python3
"""
DeepX - 多接口集成的子域名收集工具
专注发现隐藏子域名资产

用法:
    python DeepX.py example.com
    python DeepX.py collect example.com [--no-cache] [--no-brute]
    python DeepX.py fofa example.com
    python DeepX.py brute example.com
    python DeepX.py all example.com
"""

import sys
import asyncio

from core.cli import main
from utils.asyncio_patch import apply_asyncio_patches

if __name__ == "__main__":
    # 应用asyncio补丁，确保在Windows上正常工作
    apply_asyncio_patches()
    
    # 运行主函数
    main() 