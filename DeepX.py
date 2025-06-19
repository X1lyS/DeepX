#!/usr/bin/env python3
"""
DeepX - 多接口集成的子域名收集工具

用法:
    python DeepX.py example.com
    python DeepX.py collect example.com [--no-cache] [--no-brute]
    python DeepX.py fofa example.com
    python DeepX.py brute example.com
    python DeepX.py all example.com
"""

import os
import sys

# 确保当前目录在Python的导入路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.cli import main

if __name__ == "__main__":
    main() 